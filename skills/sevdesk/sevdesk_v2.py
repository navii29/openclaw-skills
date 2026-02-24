#!/usr/bin/env python3
"""
SevDesk Skill - German Accounting Automation
Handles invoices, contacts, vouchers, and banking via SevDesk API

Improvements in v2.2:
- **NEW: Batch operations** - Bulk create/update contacts and invoices
- **NEW: Health check** - API connectivity monitoring
- **NEW: Webhook support** - Register and verify webhooks
- **NEW: CSV/Excel export/import** - Data portability
- **NEW: Async batch processing** - Parallel API calls with concurrency control
- **NEW: Operation queue** - Offline operation buffering

Improvements in v2.1:
- Structured logging
- Retry logic with exponential backoff
- Pagination support
- Input validation
- Circuit breaker pattern
- Proper CLI with argparse
- TTL-based caching
- Enums for status codes
- Response metadata tracking
- Config file support
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import csv
import io
import hashlib
import hmac
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Callable, TypeVar, Generic, Tuple, Union
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from pathlib import Path
from collections import deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sevdesk')

T = TypeVar('T')

# ==================== VERSION & CONSTANTS ====================

VERSION = "2.3.0"

class InvoiceStatus(IntEnum):
    """Invoice status codes"""
    DRAFT = 100
    OPEN = 200
    PARTIAL = 750
    PAID = 1000

class ContactCategory(IntEnum):
    """Contact category codes"""
    CUSTOMER = 3
    SUPPLIER = 4
    PARTNER = 5

class InvoiceType(str, Enum):
    """Invoice type codes"""
    INVOICE = "RE"          # Rechnung
    ADVANCE = "AR"          # Anzahlungsrechnung
    PARTIAL = "TR"          # Teilrechnung
    FINAL = "ER"            # Endrechnung
    CREDIT = "GS"           # Gutschrift

class VoucherStatus(IntEnum):
    """Voucher status codes"""
    DRAFT = 100
    OPEN = 200
    PARTIAL = 750
    PAID = 1000


class DunningLevel(IntEnum):
    """Dunning/reminder levels (Mahnstufen)"""
    REMINDER = 1          # Erste Mahnung (friendly reminder)
    FIRST = 2             # Zweite Mahnung (first formal dunning)
    SECOND = 3            # Dritte Mahnung (second formal dunning)
    FINAL = 4             # Letzte Mahnung (final notice before legal action)


class WebhookEvent(str, Enum):
    """SevDesk webhook event types"""
    CONTACT_CREATED = "ContactCreate"
    CONTACT_UPDATED = "ContactUpdate"
    CONTACT_DELETED = "ContactDelete"
    INVOICE_CREATED = "InvoiceCreate"
    INVOICE_UPDATED = "InvoiceUpdate"
    INVOICE_DELETED = "InvoiceDelete"
    VOUCHER_CREATED = "VoucherCreate"
    VOUCHER_UPDATED = "VoucherUpdate"
    TRANSACTION_CREATED = "CheckAccountTransactionCreate"

# API Configuration
BASE_URL = "https://my.sevdesk.de/api/v1"
API_TOKEN = os.environ.get("SEVDESK_API_TOKEN", "")
DEFAULT_TIMEOUT = 30
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_MAX_RETRIES = 3
RATE_LIMIT_REQUESTS_PER_SECOND = 10
DEFAULT_BATCH_CONCURRENCY = 5  # Max parallel batch operations

# Connection Pool Settings
CONNECTION_POOL_SIZE = 10
CONNECTION_MAX_RETRIES = 3
CONNECTION_POOL_ENABLED = True


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreaker:
    """Circuit breaker for API resilience"""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    
    def __post_init__(self):
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time: Optional[float] = None
    
    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - (self.last_failure_time or 0) > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN
    
    def record_success(self) -> None:
        self.failures = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self) -> None:
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN


@dataclass
class BatchResult:
    """Result of a batch operation"""
    successful: List[Dict] = field(default_factory=list)
    failed: List[Dict] = field(default_factory=list)
    total: int = 0
    duration_ms: float = 0.0
    
    @property
    def success_count(self) -> int:
        return len(self.successful)
    
    @property
    def failure_count(self) -> int:
        return len(self.failed)
    
    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.success_count / self.total) * 100


@dataclass
class HealthStatus:
    """API health check status"""
    healthy: bool
    response_time_ms: float
    api_version: Optional[str] = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "healthy": self.healthy,
            "response_time_ms": round(self.response_time_ms, 2),
            "api_version": self.api_version,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class DunningResult:
    """Result of a dunning/reminder operation"""
    invoice_id: str
    invoice_number: str
    contact_name: str
    amount_due: float
    days_overdue: int
    dunning_level: DunningLevel
    success: bool
    message: str = ""
    reminder_date: Optional[str] = None
    reminder_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "contact_name": self.contact_name,
            "amount_due": self.amount_due,
            "days_overdue": self.days_overdue,
            "dunning_level": self.dunning_level.name,
            "success": self.success,
            "message": self.message,
            "reminder_date": self.reminder_date,
            "reminder_id": self.reminder_id
        }


class WebhookHandler:
    """Handle SevDesk webhook verification and processing"""
    
    def __init__(self, secret: Optional[str] = None):
        self.secret = secret
        self._handlers: Dict[str, List[Callable]] = {}
    
    def register_handler(self, event: WebhookEvent, handler: Callable) -> None:
        """Register a handler for a specific webhook event"""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature if secret is configured"""
        if not self.secret:
            return True  # No secret configured, accept all
        
        expected = hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    def process_webhook(self, event: str, data: Dict) -> bool:
        """Process incoming webhook and call registered handlers"""
        handlers = self._handlers.get(event, [])
        success = True
        
        for handler in handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Webhook handler failed for {event}: {e}")
                success = False
        
        return success


class OperationQueue:
    """Queue operations for offline/buffered execution"""
    
    def __init__(self, max_size: int = 1000):
        self._queue: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._persist_path: Optional[Path] = None
    
    def set_persistence(self, path: str) -> None:
        """Enable disk persistence for queue"""
        self._persist_path = Path(path)
        self._load_from_disk()
    
    def enqueue(self, operation: str, data: Dict) -> bool:
        """Add operation to queue"""
        with self._lock:
            item = {
                "operation": operation,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            try:
                self._queue.append(item)
                if self._persist_path:
                    self._save_to_disk()
                return True
            except Exception as e:
                logger.error(f"Failed to enqueue operation: {e}")
                return False
    
    def dequeue(self) -> Optional[Dict]:
        """Get next operation from queue"""
        with self._lock:
            if self._queue:
                item = self._queue.popleft()
                if self._persist_path:
                    self._save_to_disk()
                return item
            return None
    
    def peek_all(self) -> List[Dict]:
        """View all queued operations without removing"""
        with self._lock:
            return list(self._queue)
    
    def clear(self) -> None:
        """Clear all queued operations"""
        with self._lock:
            self._queue.clear()
            if self._persist_path:
                self._save_to_disk()
    
    def __len__(self) -> int:
        return len(self._queue)
    
    def _save_to_disk(self) -> None:
        """Persist queue to disk"""
        if self._persist_path:
            try:
                with open(self._persist_path, 'w') as f:
                    json.dump(list(self._queue), f)
            except Exception as e:
                logger.error(f"Failed to save queue: {e}")
    
    def _load_from_disk(self) -> None:
        """Load queue from disk"""
        if self._persist_path and self._persist_path.exists():
            try:
                with open(self._persist_path) as f:
                    data = json.load(f)
                    self._queue.extend(data)
            except Exception as e:
                logger.error(f"Failed to load queue: {e}")


@dataclass
class CacheEntry:
    """Cache entry with expiration time"""
    data: Any
    expires_at: float


class SimpleCache:
    """Simple TTL-based cache for API responses"""

    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None
        
        if time.time() > entry.expires_at:
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        return entry.data
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value in cache with TTL"""
        ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(
            data=value,
            expires_at=time.time() + ttl
        )
    
    def clear(self) -> None:
        """Clear all cached entries"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2)
        }


def retry_on_error(max_retries: int = DEFAULT_MAX_RETRIES, delay: float = DEFAULT_RETRY_DELAY, 
                   exceptions: tuple = (requests.RequestException,),
                   backoff_factor: float = 2.0) -> Callable:
    """Decorator for retry logic with exponential backoff"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff_factor ** attempt)
                        logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception
        return wrapper
    return decorator


def validate_contact_data(func: Callable) -> Callable:
    """Decorator to validate contact data"""
    @wraps(func)
    def wrapper(self, name: str, email: Optional[str] = None, **kwargs) -> Any:
        if not name or len(name.strip()) < 2:
            raise ValueError("Contact name must be at least 2 characters")
        if email and '@' not in email:
            raise ValueError(f"Invalid email format: {email}")
        return func(self, name, email, **kwargs)
    return wrapper


def validate_invoice_items(func: Callable) -> Callable:
    """Decorator to validate invoice items"""
    @wraps(func)
    def wrapper(self, contact_id: str, items: List[Dict], **kwargs) -> Any:
        if not contact_id:
            raise ValueError("contact_id is required")
        if not items or not isinstance(items, list):
            raise ValueError("items must be a non-empty list")
        
        for i, item in enumerate(items):
            if not item.get('name'):
                raise ValueError(f"Item {i}: name is required")
            price = item.get('price')
            if not isinstance(price, (int, float)):
                raise ValueError(f"Item {i}: price must be a number, got {type(price).__name__}")
            if price < 0:
                raise ValueError(f"Item {i}: price cannot be negative ({price})")
        
        return func(self, contact_id, items, **kwargs)
    return wrapper


@dataclass
class ResponseMetadata:
    """Metadata about API response"""
    request_count: int
    cached: bool
    duration_ms: float
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[int] = None


class SevDeskClient:
    """
    Enhanced client for SevDesk API interactions
    
    Features:
    - Circuit breaker for resilience
    - Retry logic with exponential backoff
    - Input validation via decorators
    - TTL-based caching
    - Rate limiting
    - Pagination support
    - **NEW: Batch operations** - Bulk create/update with concurrency control
    - **NEW: Health monitoring** - API health checks
    - **NEW: Webhook management** - Register and verify webhooks
    - **NEW: Export/Import** - CSV/Excel data portability
    - **NEW: Operation queue** - Offline operation buffering
    """
    
    def __init__(self, token: Optional[str] = None, enable_cache: bool = True, 
                 cache_ttl: int = 300, config_path: Optional[str] = None,
                 batch_concurrency: int = DEFAULT_BATCH_CONCURRENCY,
                 webhook_secret: Optional[str] = None,
                 queue_persist_path: Optional[str] = None):
        """
        Initialize SevDesk client
        
        Args:
            token: API token (or set SEVDESK_API_TOKEN env var)
            enable_cache: Enable response caching
            cache_ttl: Default cache TTL in seconds
            config_path: Path to config file (JSON)
            batch_concurrency: Max parallel batch operations (default: 5)
            webhook_secret: Secret for webhook signature verification
            queue_persist_path: Path for operation queue persistence
        """
        self.token = token or API_TOKEN or self._load_token_from_config(config_path)
        if not self.token:
            raise ValueError(
                "SevDesk API token required. "
                "Set SEVDESK_API_TOKEN environment variable or provide config file."
            )
        
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.circuit_breaker = CircuitBreaker()
        self.cache = SimpleCache(default_ttl=cache_ttl) if enable_cache else None
        self._request_count = 0
        self._cached_request_count = 0
        self._last_request_time = 0.0
        self._min_request_interval = 1.0 / RATE_LIMIT_REQUESTS_PER_SECOND
        self._last_response_metadata: Optional[ResponseMetadata] = None
        
        # v2.2.0: New components
        self._batch_concurrency = batch_concurrency
        self.webhook_handler = WebhookHandler(secret=webhook_secret)
        self.operation_queue = OperationQueue()
        if queue_persist_path:
            self.operation_queue.set_persistence(queue_persist_path)
        
        # v2.3.0: Connection Pooling for performance
        self._session: Optional[requests.Session] = None
        if CONNECTION_POOL_ENABLED:
            self._init_session()
    
    def _load_token_from_config(self, config_path: Optional[str]) -> Optional[str]:
        """Load API token from config file"""
        if not config_path:
            # Try default locations
            for path in ["sevdesk.json", "~/.sevdesk/config.json"]:
                expanded = Path(path).expanduser()
                if expanded.exists():
                    config_path = str(expanded)
                    break
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                    return config.get('api_token')
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return None
    
    def _init_session(self) -> None:
        """Initialize connection pool session for performance"""
        self._session = requests.Session()
        self._session.headers.update(self.headers)
        
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=CONNECTION_POOL_SIZE,
            pool_maxsize=CONNECTION_POOL_SIZE,
            max_retries=CONNECTION_MAX_RETRIES
        )
        self._session.mount('https://', adapter)
        self._session.mount('http://', adapter)
        logger.debug(f"Connection pool initialized with {CONNECTION_POOL_SIZE} connections")
    
    def close(self) -> None:
        """Close session and release connections"""
        if self._session:
            self._session.close()
            self._session = None
            logger.debug("Connection pool closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures session is closed"""
        self.close()
        return False
    
    def _rate_limit(self) -> None:
        """Apply rate limiting between requests"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def _get_cache_key(self, method: str, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from request parameters"""
        key_parts = [method, endpoint]
        if params:
            # Sort params for consistent keys
            sorted_params = json.dumps(params, sort_keys=True)
            key_parts.append(sorted_params)
        return "|".join(key_parts)
    
    def _extract_rate_limits(self, response: requests.Response) -> Tuple[Optional[int], Optional[int]]:
        """Extract rate limit info from response headers"""
        remaining = response.headers.get('X-RateLimit-Remaining')
        reset = response.headers.get('X-RateLimit-Reset')
        return (
            int(remaining) if remaining else None,
            int(reset) if reset else None
        )
    
    @retry_on_error(max_retries=DEFAULT_MAX_RETRIES, delay=DEFAULT_RETRY_DELAY, 
                    exceptions=(requests.RequestException,))
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                 params: Optional[Dict] = None, use_cache: bool = True) -> Dict:
        """
        Make API request to SevDesk with circuit breaker, retry logic, and caching
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body
            params: Query parameters
            use_cache: Whether to use cache for GET requests
        
        Returns:
            API response as dict
        """
        if not self.circuit_breaker.can_execute():
            raise Exception("Circuit breaker is OPEN - API temporarily unavailable. Try again later.")
        
        # Check cache for GET requests
        cache_key = None
        if method.upper() == "GET" and use_cache and self.cache:
            cache_key = self._get_cache_key(method, endpoint, params)
            cached = self.cache.get(cache_key)
            if cached is not None:
                self._cached_request_count += 1
                self._last_response_metadata = ResponseMetadata(
                    request_count=self._request_count,
                    cached=True,
                    duration_ms=0.0
                )
                logger.debug(f"Cache hit for {endpoint}")
                return cached
        
        self._rate_limit()
        url = f"{BASE_URL}{endpoint}"
        start_time = time.time()
        
        try:
            # Use session for connection pooling (v2.3.0 performance improvement)
            if self._session:
                response = self._session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=DEFAULT_TIMEOUT
                )
            else:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=DEFAULT_TIMEOUT
                )
            response.raise_for_status()
            self.circuit_breaker.record_success()
            self._request_count += 1
            
            result = response.json()
            
            # Store in cache
            if cache_key and self.cache:
                self.cache.set(cache_key, result)
            
            duration_ms = (time.time() - start_time) * 1000
            rate_remaining, rate_reset = self._extract_rate_limits(response)
            
            self._last_response_metadata = ResponseMetadata(
                request_count=self._request_count,
                cached=False,
                duration_ms=duration_ms,
                rate_limit_remaining=rate_remaining,
                rate_limit_reset=rate_reset
            )
            
            logger.debug(f"Request to {endpoint} completed in {duration_ms:.2f}ms")
            return result
            
        except requests.exceptions.HTTPError as e:
            self.circuit_breaker.record_failure()
            error_msg = self._parse_http_error(response, e)
            logger.error(f"HTTP Error: {error_msg}")
            return {"error": error_msg, "status_code": response.status_code}
            
        except requests.exceptions.RequestException as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Request failed: {e}")
            raise
    
    def _parse_http_error(self, response: requests.Response, error: Exception) -> str:
        """Parse HTTP error into user-friendly message with suggestions"""
        status_map = {
            400: ("Bad Request", "Check your request parameters."),
            401: ("Invalid API token", "Check your SEVDESK_API_TOKEN environment variable."),
            403: ("Access forbidden", "Check your API token permissions."),
            404: ("Resource not found", f"The requested resource does not exist: {response.url}"),
            422: ("Validation error", f"Invalid data provided: {response.text}"),
            429: ("Rate limit exceeded", "Too many requests. Please wait before retrying."),
            500: ("SevDesk server error", "Please try again later."),
            502: ("Bad Gateway", "SevDesk is temporarily unavailable."),
            503: ("Service unavailable", "SevDesk is under maintenance."),
        }
        
        status_info = status_map.get(response.status_code)
        if status_info:
            error_type, suggestion = status_info
            return f"{error_type} ({response.status_code}): {suggestion}"
        
        return f"API Error {response.status_code}: {str(error)}"
    
    def _get_all_pages(self, endpoint: str, params: Optional[Dict] = None, 
                       limit: int = 1000) -> List[Dict]:
        """
        Fetch all paginated results
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            limit: Maximum number of results to fetch
        
        Returns:
            List of all objects
        """
        all_objects: List[Dict] = []
        params = params or {}
        params['limit'] = min(limit, 100)  # API max is 100
        offset = 0
        
        while len(all_objects) < limit:
            params['offset'] = offset
            result = self._request("GET", endpoint, params=params, use_cache=False)
            
            if 'error' in result:
                logger.error(f"Error fetching page: {result['error']}")
                break
            
            objects = result.get("objects", [])
            if not objects:
                break
            
            all_objects.extend(objects)
            
            if len(objects) < params['limit']:
                break
            
            offset += params['limit']
            
            # Be nice to the API
            if len(all_objects) < limit:
                time.sleep(0.1)
        
        return all_objects[:limit]
    
    # ==================== CONTACTS ====================
    
    def list_contacts(self, search: Optional[str] = None, limit: int = 100) -> Dict:
        """List all contacts (customers/suppliers) with pagination"""
        params: Dict[str, Any] = {}
        if search:
            params["name"] = search
        
        objects = self._get_all_pages("/Contact", params, limit)
        return {"objects": objects, "total": len(objects)}
    
    def get_contact(self, contact_id: str) -> Dict:
        """Get specific contact details"""
        if not contact_id:
            raise ValueError("contact_id is required")
        return self._request("GET", f"/Contact/{contact_id}")
    
    @validate_contact_data
    def create_contact(self, name: str, email: Optional[str] = None, 
                       phone: Optional[str] = None, address: Optional[Dict] = None,
                       customer_number: Optional[str] = None) -> Dict:
        """Create a new contact with validation"""
        data: Dict[str, Any] = {
            "name": name.strip(),
            "category": {"id": ContactCategory.CUSTOMER, "objectName": "Category"}
        }
        if email:
            data["email"] = email.strip()
        if phone:
            data["phone"] = phone.strip()
        if address:
            data["addresses"] = [address]
        if customer_number:
            data["customerNumber"] = customer_number
        
        return self._request("POST", "/Contact", data=data)
    
    def update_contact(self, contact_id: str, **kwargs) -> Dict:
        """Update an existing contact"""
        if not contact_id:
            raise ValueError("contact_id is required")
        return self._request("PUT", f"/Contact/{contact_id}", data=kwargs)
    
    # ==================== INVOICES ====================
    
    def list_invoices(self, status: Optional[str] = None, limit: int = 100,
                      start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """List invoices with optional filters and pagination"""
        params: Dict[str, Any] = {}
        if status:
            status_map = {
                "draft": str(InvoiceStatus.DRAFT),
                "open": str(InvoiceStatus.OPEN),
                "paid": str(InvoiceStatus.PAID),
                "overdue": str(InvoiceStatus.OPEN)
            }
            params["status"] = status_map.get(status, status)
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        
        objects = self._get_all_pages("/Invoice", params, limit)
        return {"objects": objects, "total": len(objects)}
    
    def get_invoice(self, invoice_id: str) -> Dict:
        """Get specific invoice details with embedded contact and positions"""
        if not invoice_id:
            raise ValueError("invoice_id is required")
        return self._request("GET", f"/Invoice/{invoice_id}", params={"embed": "contact,invoicePos"})
    
    @validate_invoice_items
    def create_invoice(self, contact_id: str, items: List[Dict], 
                       invoice_type: str = InvoiceType.INVOICE, due_date_days: int = 14,
                       header: Optional[str] = None, footer: Optional[str] = None) -> Dict:
        """
        Create a new invoice with validation
        
        Args:
            contact_id: SevDesk contact ID
            items: List of {"name": str, "quantity": int, "price": float, "tax_rate": float}
            invoice_type: RE=Invoice, AR=Advance, TR=Partial, ER=Final
            due_date_days: Days until invoice is due
            header: Optional header text
            footer: Optional footer text
        
        Returns:
            API response dict
        """
        due_date = (datetime.now() + timedelta(days=due_date_days)).strftime("%Y-%m-%d")
        
        invoice_pos = []
        for i, item in enumerate(items):
            invoice_pos.append({
                "positionNumber": i + 1,
                "name": item["name"],
                "quantity": item.get("quantity", 1),
                "price": item["price"],
                "taxRate": item.get("tax_rate", 19.0),
                "mapAll": True
            })
        
        data = {
            "invoice": {
                "contact": {"id": contact_id, "objectName": "Contact"},
                "invoiceDate": datetime.now().strftime("%Y-%m-%d"),
                "deliveryDate": datetime.now().strftime("%Y-%m-%d"),
                "status": InvoiceStatus.DRAFT,
                "invoiceType": invoice_type,
                "currency": "EUR",
                "mapAll": True
            },
            "invoicePosSave": invoice_pos,
            "invoicePosDelete": []
        }
        
        if header:
            data["invoice"]["header"] = header
        if footer:
            data["invoice"]["footer"] = footer
        
        return self._request("POST", "/Invoice/Factory/saveInvoice", data=data)
    
    def send_invoice_email(self, invoice_id: str, email: Optional[str] = None,
                          subject: Optional[str] = None, body: Optional[str] = None) -> Dict:
        """Send invoice via email with optional custom message"""
        if not invoice_id:
            raise ValueError("invoice_id is required")
        
        data: Dict[str, Any] = {"invoiceId": invoice_id}
        if email:
            data["email"] = email
        if subject:
            data["subject"] = subject
        if body:
            data["text"] = body
        
        return self._request("POST", f"/Invoice/{invoice_id}/sendViaEmail", data=data)
    
    def get_unpaid_invoices(self, days_overdue: Optional[int] = None) -> List[Dict]:
        """Get all unpaid (open) invoices with optional overdue filter"""
        result = self.list_invoices(status="open")
        invoices = result.get("objects", [])
        
        if days_overdue:
            cutoff = datetime.now() - timedelta(days=days_overdue)
            invoices = [
                inv for inv in invoices 
                if datetime.strptime(inv.get("deliveryDate", "2025-01-01"), "%Y-%m-%d") < cutoff
            ]
        
        return invoices
    
    def get_invoice_pdf(self, invoice_id: str) -> bytes:
        """Download invoice as PDF"""
        if not invoice_id:
            raise ValueError("invoice_id is required")
        
        url = f"{BASE_URL}/Invoice/{invoice_id}/getPdf"
        response = requests.get(url, headers={"Authorization": self.token}, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return response.content
    
    # ==================== VOUCHERS ====================
    
    def list_vouchers(self, limit: int = 100, start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> Dict:
        """List expense vouchers with optional date range"""
        params: Dict[str, Any] = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        
        objects = self._get_all_pages("/Voucher", params, limit)
        return {"objects": objects, "total": len(objects)}
    
    def create_voucher(self, supplier_id: str, amount: float, description: str,
                       tax_rate: float = 19.0, voucher_date: Optional[str] = None,
                       category_id: Optional[str] = None) -> Dict:
        """Create a new expense voucher with validation"""
        if not supplier_id:
            raise ValueError("supplier_id is required")
        if amount <= 0:
            raise ValueError(f"amount must be positive, got {amount}")
        if not description or len(description.strip()) < 3:
            raise ValueError("description must be at least 3 characters")
        
        if not voucher_date:
            voucher_date = datetime.now().strftime("%Y-%m-%d")
        
        data = {
            "voucher": {
                "supplier": {"id": supplier_id, "objectName": "Contact"},
                "voucherDate": voucher_date,
                "description": description,
                "status": VoucherStatus.DRAFT,
                "taxType": "default",
                "mapAll": True
            },
            "voucherPos": [{
                "amount": amount,
                "taxRate": tax_rate,
                "name": description,
                "mapAll": True
            }]
        }
        
        return self._request("POST", "/Voucher/Factory/saveVoucher", data=data)
    
    # ==================== BANKING ====================
    
    def list_bank_accounts(self) -> Dict:
        """List all bank/check accounts"""
        return self._request("GET", "/CheckAccount")
    
    def get_bank_balance(self, account_id: Optional[str] = None) -> Dict:
        """Get bank account balance"""
        if account_id:
            return self._request("GET", f"/CheckAccount/{account_id}")
        
        accounts = self.list_bank_accounts()
        if accounts.get("objects"):
            return accounts["objects"][0]
        return {"error": "No bank accounts found"}
    
    def list_transactions(self, account_id: Optional[str] = None, limit: int = 100,
                         start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """List bank transactions with optional filters"""
        params: Dict[str, Any] = {}
        if account_id:
            params["checkAccount"] = account_id
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        
        objects = self._get_all_pages("/CheckAccountTransaction", params, limit)
        return {"objects": objects, "total": len(objects)}
    
    def match_transaction_to_invoice(self, transaction_id: str, invoice_id: str) -> Dict:
        """Match a bank transaction to an invoice for reconciliation"""
        if not transaction_id or not invoice_id:
            raise ValueError("Both transaction_id and invoice_id are required")
        
        data = {
            "invoiceId": invoice_id,
            "checkAccountTransactionId": transaction_id
        }
        return self._request("POST", "/CheckAccountTransaction/Factory/matchInvoice", data=data)
    
    # ==================== REPORTS ====================
    
    def get_revenue_report(self, start_date: str, end_date: str) -> Dict:
        """Get revenue report for date range"""
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "reportType": "revenue"
        }
        return self._request("GET", "/Report", params=params)
    
    def get_outstanding_invoices_report(self) -> Dict:
        """Get summary of outstanding invoices"""
        unpaid = self.get_unpaid_invoices()
        total_net = sum(inv.get("sumNet", 0) for inv in unpaid)
        total_gross = sum(inv.get("sumGross", 0) for inv in unpaid)
        
        return {
            "count": len(unpaid),
            "total_net": total_net,
            "total_gross": total_gross,
            "currency": "EUR",
            "invoices": unpaid[:20]  # Limit details
        }
    
    # ==================== FORMATTING ====================
    
    def format_invoice(self, invoice: Dict) -> str:
        """Format invoice for display"""
        contact = invoice.get("contact", {})
        status_map = {
            InvoiceStatus.DRAFT: "📝 Entwurf",
            InvoiceStatus.OPEN: "📤 Offen",
            InvoiceStatus.PARTIAL: "💶 Teilweise bezahlt",
            InvoiceStatus.PAID: "✅ Bezahlt"
        }
        status = status_map.get(invoice.get("status"), f"Status {invoice.get('status')}")
        
        return f"""
📄 Rechnung {invoice.get('invoiceNumber', '---')}
   Kunde: {contact.get('name', '---')}
   Betrag: {invoice.get('sumNet', 0):.2f} € (Netto)
   Status: {status}
   Datum: {invoice.get('invoiceDate', '---')}
"""
    
    def format_contact(self, contact: Dict) -> str:
        """Format contact for display"""
        category_map = {
            ContactCategory.CUSTOMER: "Kunde",
            ContactCategory.SUPPLIER: "Lieferant",
            ContactCategory.PARTNER: "Partner"
        }
        category = category_map.get(
            contact.get("category", {}).get("id"), 
            "Kontakt"
        )
        return f"👤 {contact.get('name')} ({category}) - ID: {contact.get('id')}"
    
    # ==================== v2.2.0: BATCH OPERATIONS ====================
    
    def batch_create_contacts(self, contacts: List[Dict], 
                              continue_on_error: bool = True) -> BatchResult:
        """
        Batch create multiple contacts with concurrency control
        
        Args:
            contacts: List of contact data dicts with 'name', 'email', etc.
            continue_on_error: Continue processing if individual items fail
        
        Returns:
            BatchResult with successful and failed operations
        """
        start_time = time.time()
        result = BatchResult(total=len(contacts))
        
        def create_single(contact_data: Dict) -> Tuple[Optional[Dict], Optional[Dict]]:
            try:
                created = self.create_contact(**contact_data)
                if 'error' in created:
                    return None, {"data": contact_data, "error": created['error']}
                return created, None
            except Exception as e:
                return None, {"data": contact_data, "error": str(e)}
        
        with ThreadPoolExecutor(max_workers=self._batch_concurrency) as executor:
            futures = {executor.submit(create_single, c): c for c in contacts}
            
            for future in as_completed(futures):
                success, error = future.result()
                if success:
                    result.successful.append(success)
                else:
                    result.failed.append(error)
                    if not continue_on_error:
                        executor.shutdown(wait=False)
                        break
        
        result.duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Batch create contacts: {result.success_count}/{result.total} successful "
                   f"({result.success_rate:.1f}%) in {result.duration_ms:.0f}ms")
        return result
    
    def batch_create_invoices(self, invoices: List[Dict],
                              continue_on_error: bool = True) -> BatchResult:
        """
        Batch create multiple invoices with concurrency control
        
        Args:
            invoices: List of invoice data dicts with 'contact_id', 'items', etc.
            continue_on_error: Continue processing if individual items fail
        
        Returns:
            BatchResult with successful and failed operations
        """
        start_time = time.time()
        result = BatchResult(total=len(invoices))
        
        def create_single(invoice_data: Dict) -> Tuple[Optional[Dict], Optional[Dict]]:
            try:
                created = self.create_invoice(**invoice_data)
                if 'error' in created:
                    return None, {"data": invoice_data, "error": created['error']}
                return created, None
            except Exception as e:
                return None, {"data": invoice_data, "error": str(e)}
        
        with ThreadPoolExecutor(max_workers=self._batch_concurrency) as executor:
            futures = {executor.submit(create_single, inv): inv for inv in invoices}
            
            for future in as_completed(futures):
                success, error = future.result()
                if success:
                    result.successful.append(success)
                else:
                    result.failed.append(error)
                    if not continue_on_error:
                        executor.shutdown(wait=False)
                        break
        
        result.duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Batch create invoices: {result.success_count}/{result.total} successful "
                   f"({result.success_rate:.1f}%) in {result.duration_ms:.0f}ms")
        return result
    
    def batch_update_invoice_status(self, invoice_ids: List[str], 
                                    status: InvoiceStatus) -> BatchResult:
        """
        Batch update status of multiple invoices
        
        Args:
            invoice_ids: List of invoice IDs to update
            status: New status to set
        
        Returns:
            BatchResult with successful and failed operations
        """
        start_time = time.time()
        result = BatchResult(total=len(invoice_ids))
        
        def update_single(invoice_id: str) -> Tuple[Optional[str], Optional[Dict]]:
            try:
                # SevDesk API for status update
                response = self._request(
                    "PUT", 
                    f"/Invoice/{invoice_id}", 
                    data={"status": int(status)}
                )
                if 'error' in response:
                    return None, {"invoice_id": invoice_id, "error": response['error']}
                return invoice_id, None
            except Exception as e:
                return None, {"invoice_id": invoice_id, "error": str(e)}
        
        with ThreadPoolExecutor(max_workers=self._batch_concurrency) as executor:
            futures = {executor.submit(update_single, inv_id): inv_id for inv_id in invoice_ids}
            
            for future in as_completed(futures):
                success, error = future.result()
                if success:
                    result.successful.append({"invoice_id": success})
                else:
                    result.failed.append(error)
        
        result.duration_ms = (time.time() - start_time) * 1000
        logger.info(f"Batch update invoices: {result.success_count}/{result.total} successful")
        return result
    
    # ==================== v2.2.0: HEALTH CHECK ====================
    
    def health_check(self, timeout: float = 5.0) -> HealthStatus:
        """
        Check API health and connectivity
        
        Args:
            timeout: Request timeout in seconds
        
        Returns:
            HealthStatus with health information
        """
        start_time = time.time()
        
        try:
            # Try a lightweight API call
            response = requests.get(
                f"{BASE_URL}/Contact",
                headers=self.headers,
                params={"limit": 1},
                timeout=timeout
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Try to get API version from headers if available
                api_version = response.headers.get('X-API-Version', 'unknown')
                return HealthStatus(
                    healthy=True,
                    response_time_ms=response_time,
                    api_version=api_version,
                    message="API is responsive"
                )
            elif response.status_code == 401:
                return HealthStatus(
                    healthy=False,
                    response_time_ms=response_time,
                    message="Authentication failed - check API token"
                )
            else:
                return HealthStatus(
                    healthy=False,
                    response_time_ms=response_time,
                    message=f"API returned status {response.status_code}"
                )
                
        except requests.exceptions.Timeout:
            return HealthStatus(
                healthy=False,
                response_time_ms=(time.time() - start_time) * 1000,
                message=f"Request timed out after {timeout}s"
            )
        except requests.exceptions.ConnectionError:
            return HealthStatus(
                healthy=False,
                response_time_ms=(time.time() - start_time) * 1000,
                message="Connection error - check network"
            )
        except Exception as e:
            return HealthStatus(
                healthy=False,
                response_time_ms=(time.time() - start_time) * 1000,
                message=f"Health check failed: {str(e)}"
            )
    
    # ==================== v2.2.0: WEBHOOKS ====================
    
    def list_webhooks(self) -> Dict:
        """List all registered webhooks"""
        return self._request("GET", "/Webhook")
    
    def create_webhook(self, url: str, events: List[WebhookEvent],
                       name: Optional[str] = None, active: bool = True) -> Dict:
        """
        Register a new webhook
        
        Args:
            url: Endpoint URL to receive webhook events
            events: List of events to subscribe to
            name: Optional webhook name
            active: Whether webhook is active
        
        Returns:
            API response with created webhook
        """
        data = {
            "url": url,
            "event": [e.value for e in events],
            "active": active
        }
        if name:
            data["name"] = name
        
        return self._request("POST", "/Webhook", data=data)
    
    def delete_webhook(self, webhook_id: str) -> Dict:
        """Delete a webhook by ID"""
        if not webhook_id:
            raise ValueError("webhook_id is required")
        return self._request("DELETE", f"/Webhook/{webhook_id}")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook payload signature"""
        return self.webhook_handler.verify_signature(payload, signature)
    
    def register_webhook_handler(self, event: WebhookEvent, handler: Callable) -> None:
        """Register a handler for a webhook event"""
        self.webhook_handler.register_handler(event, handler)
    
    # ==================== v2.2.0: EXPORT/IMPORT ====================
    
    def export_contacts_csv(self, filename: Optional[str] = None,
                            search: Optional[str] = None) -> str:
        """
        Export contacts to CSV format
        
        Args:
            filename: Output filename (optional, returns CSV string if None)
            search: Optional search filter
        
        Returns:
            CSV content as string or path to saved file
        """
        result = self.list_contacts(search=search, limit=10000)
        contacts = result.get("objects", [])
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["ID", "Name", "Email", "Phone", "Customer Number", 
                        "Category", "Created"])
        
        # Data
        for contact in contacts:
            writer.writerow([
                contact.get("id", ""),
                contact.get("name", ""),
                contact.get("email", ""),
                contact.get("phone", ""),
                contact.get("customerNumber", ""),
                contact.get("category", {}).get("name", ""),
                contact.get("create", "")
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        # v2.3.0: Add UTF-8 BOM for Excel compatibility with German umlauts
        csv_content = '\ufeff' + csv_content
        
        if filename:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                f.write(csv_content)
            return filename
        
        return csv_content
    
    def export_invoices_csv(self, filename: Optional[str] = None,
                            status: Optional[str] = None,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> str:
        """
        Export invoices to CSV format
        
        Args:
            filename: Output filename (optional, returns CSV string if None)
            status: Filter by status
            start_date: Start date filter
            end_date: End date filter
        
        Returns:
            CSV content as string or path to saved file
        """
        result = self.list_invoices(status=status, start_date=start_date, 
                                    end_date=end_date, limit=10000)
        invoices = result.get("objects", [])
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["ID", "Invoice Number", "Contact", "Contact ID",
                        "Net Amount", "Gross Amount", "Status", "Date", "Due Date"])
        
        # Data
        for inv in invoices:
            contact = inv.get("contact", {})
            writer.writerow([
                inv.get("id", ""),
                inv.get("invoiceNumber", ""),
                contact.get("name", ""),
                contact.get("id", ""),
                inv.get("sumNet", 0),
                inv.get("sumGross", 0),
                inv.get("status", ""),
                inv.get("invoiceDate", ""),
                inv.get("deliveryDate", "")
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        # v2.3.0: Add UTF-8 BOM for Excel compatibility with German umlauts
        csv_content = '\ufeff' + csv_content
        
        if filename:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                f.write(csv_content)
            return filename
        
        return csv_content
    
    def import_contacts_csv(self, csv_data: str, skip_header: bool = True,
                            dry_run: bool = False,
                            encoding: str = 'utf-8-sig') -> BatchResult:
        """
        Import contacts from CSV data
        
        Args:
            csv_data: CSV content as string
            skip_header: Whether first row is header
            dry_run: Validate without creating
        
        Returns:
            BatchResult with import results
        """
        reader = csv.reader(io.StringIO(csv_data))
        rows = list(reader)
        
        if skip_header and rows:
            rows = rows[1:]
        
        contacts_to_create = []
        for row in rows:
            if len(row) >= 2 and row[1]:  # At least name required
                contact = {"name": row[1]}
                if len(row) > 2 and row[2]:
                    contact["email"] = row[2]
                if len(row) > 3 and row[3]:
                    contact["phone"] = row[3]
                contacts_to_create.append(contact)
        
        if dry_run:
            result = BatchResult(total=len(contacts_to_create))
            result.successful = [{"dry_run": True, "data": c} for c in contacts_to_create]
            return result
        
        return self.batch_create_contacts(contacts_to_create)
    
    # ==================== v2.2.0: QUEUE MANAGEMENT ====================
    
    def queue_operation(self, operation: str, data: Dict) -> bool:
        """Queue an operation for later execution"""
        return self.operation_queue.enqueue(operation, data)
    
    def process_queue(self) -> BatchResult:
        """Process all queued operations"""
        operations = self.operation_queue.peek_all()
        result = BatchResult(total=len(operations))
        
        while True:
            item = self.operation_queue.dequeue()
            if not item:
                break
            
            try:
                op = item["operation"]
                data = item["data"]
                
                if op == "create_contact":
                    self.create_contact(**data)
                elif op == "create_invoice":
                    self.create_invoice(**data)
                elif op == "create_voucher":
                    self.create_voucher(**data)
                else:
                    logger.warning(f"Unknown operation: {op}")
                    result.failed.append({"operation": op, "error": "Unknown operation"})
                    continue
                
                result.successful.append({"operation": op, "data": data})
                
            except Exception as e:
                result.failed.append({"operation": item.get("operation"), 
                                      "error": str(e)})
        
        return result
    
    def get_queue_status(self) -> Dict:
        """Get current queue status"""
        return {
            "queued_operations": len(self.operation_queue),
            "operations": self.operation_queue.peek_all()
        }
    
    def clear_queue(self) -> None:
        """Clear all queued operations"""
        self.operation_queue.clear()
    
    # ==================== STATS ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get API usage statistics"""
        stats: Dict[str, Any] = {
            "request_count": self._request_count,
            "cached_request_count": self._cached_request_count,
            "circuit_state": self.circuit_breaker.state.value,
            "circuit_failures": self.circuit_breaker.failures
        }
        
        if self.cache:
            stats["cache"] = self.cache.get_stats()
        
        if self._last_response_metadata:
            stats["last_response"] = {
                "cached": self._last_response_metadata.cached,
                "duration_ms": round(self._last_response_metadata.duration_ms, 2),
                "rate_limit_remaining": self._last_response_metadata.rate_limit_remaining
            }
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear the response cache"""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")
    
    # ==================== v2.3.0: DUNNING / MAHNUNGEN ====================
    
    def get_overdue_invoices(self, days_overdue: int = 1, 
                             max_dunning_level: Optional[DunningLevel] = None) -> List[Dict]:
        """
        Get all overdue invoices with their dunning status
        
        Args:
            days_overdue: Minimum days overdue (default: 1)
            max_dunning_level: Only return invoices up to this dunning level
        
        Returns:
            List of overdue invoice dicts with 'days_overdue' and 'current_dunning_level'
        """
        invoices = self.get_unpaid_invoices(days_overdue=days_overdue)
        overdue = []
        
        for inv in invoices:
            # Calculate days overdue from delivery/due date
            due_date_str = inv.get('deliveryDate') or inv.get('invoiceDate')
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                    days = (datetime.now() - due_date).days
                except ValueError:
                    days = 0
            else:
                days = 0
            
            # Determine current dunning level from invoice
            current_level = DunningLevel.REMINDER
            reminder_sent = inv.get('reminderSent', False)
            reminder_count = inv.get('reminderCount', 0)
            
            if reminder_count >= 3:
                current_level = DunningLevel.FINAL
            elif reminder_count >= 2:
                current_level = DunningLevel.SECOND
            elif reminder_count >= 1:
                current_level = DunningLevel.FIRST
            elif reminder_sent:
                current_level = DunningLevel.REMINDER
            
            if max_dunning_level and current_level.value > max_dunning_level.value:
                continue
            
            inv['days_overdue'] = days
            inv['current_dunning_level'] = current_level
            overdue.append(inv)
        
        # Sort by days overdue (most overdue first)
        overdue.sort(key=lambda x: x['days_overdue'], reverse=True)
        return overdue
    
    def create_dunning(self, invoice_id: str, 
                       level: DunningLevel = DunningLevel.REMINDER,
                       fee: Optional[float] = None,
                       note: Optional[str] = None,
                       due_date_days: int = 7) -> DunningResult:
        """
        Create a dunning/reminder for an overdue invoice
        
        Args:
            invoice_id: The invoice to create dunning for
            level: Dunning level (REMINDER, FIRST, SECOND, FINAL)
            fee: Optional dunning fee to add
            note: Optional note/message for the dunning
            due_date_days: Days until payment is due (default: 7)
        
        Returns:
            DunningResult with success status and details
        """
        # Get invoice details
        invoice = self.get_invoice(invoice_id)
        if 'error' in invoice:
            return DunningResult(
                invoice_id=invoice_id,
                invoice_number="",
                contact_name="",
                amount_due=0,
                days_overdue=0,
                dunning_level=level,
                success=False,
                message=f"Invoice not found: {invoice['error']}"
            )
        
        # Calculate due date
        due_date = (datetime.now() + timedelta(days=due_date_days)).strftime('%Y-%m-%d')
        
        # Prepare reminder data for SevDesk API
        reminder_data = {
            "invoice": {"id": invoice_id, "objectName": "Invoice"},
            "reminderLevel": level.value,
            "reminderDate": datetime.now().strftime('%Y-%m-%d'),
            "dueDate": due_date,
        }
        
        if fee:
            reminder_data["reminderCharge"] = fee
        if note:
            reminder_data["text"] = note
        
        # Send to API
        response = self._request("POST", "/InvoiceReminder", data=reminder_data)
        
        contact = invoice.get('contact', {})
        amount = float(invoice.get('sumGross', 0)) - float(invoice.get('paidAmount', 0))
        
        if 'error' in response:
            return DunningResult(
                invoice_id=invoice_id,
                invoice_number=invoice.get('invoiceNumber', ''),
                contact_name=contact.get('name', ''),
                amount_due=amount,
                days_overdue=0,
                dunning_level=level,
                success=False,
                message=response['error']
            )
        
        # Success
        return DunningResult(
            invoice_id=invoice_id,
            invoice_number=invoice.get('invoiceNumber', ''),
            contact_name=contact.get('name', ''),
            amount_due=amount,
            days_overdue=0,
            dunning_level=level,
            success=True,
            message=f"Dunning created successfully (Level {level.name})",
            reminder_date=reminder_data['reminderDate'],
            reminder_id=response.get('id')
        )
    
    def batch_create_dunnings(self, invoice_ids: List[str],
                              level: DunningLevel = DunningLevel.REMINDER,
                              fee: Optional[float] = None,
                              note: Optional[str] = None) -> List[DunningResult]:
        """
        Batch create dunnings for multiple invoices
        
        Args:
            invoice_ids: List of invoice IDs to create dunnings for
            level: Dunning level for all invoices
            fee: Optional dunning fee
            note: Optional note/message
        
        Returns:
            List of DunningResult for each invoice
        """
        results = []
        
        for invoice_id in invoice_ids:
            result = self.create_dunning(invoice_id, level, fee, note)
            results.append(result)
            
            # Rate limit between dunnings
            time.sleep(0.2)
        
        return results
    
    def get_dunning_summary(self, days_overdue: int = 1) -> Dict:
        """
        Get summary of dunning status across all overdue invoices
        
        Args:
            days_overdue: Minimum days overdue to include
        
        Returns:
            Summary dict with counts, amounts, and recommendations
        """
        overdue = self.get_overdue_invoices(days_overdue=days_overdue)
        
        total_amount = sum(inv.get('sumGross', 0) for inv in overdue)
        total_count = len(overdue)
        
        by_level = {level: [] for level in DunningLevel}
        for inv in overdue:
            level = inv.get('current_dunning_level', DunningLevel.REMINDER)
            by_level[level].append(inv)
        
        summary = {
            "total_overdue": total_count,
            "total_amount": round(total_amount, 2),
            "by_level": {
                level.name: {
                    "count": len(invoices),
                    "amount": round(sum(i.get('sumGross', 0) for i in invoices), 2)
                }
                for level, invoices in by_level.items()
            },
            "recommendations": []
        }
        
        # Generate recommendations
        for level in [DunningLevel.REMINDER, DunningLevel.FIRST, DunningLevel.SECOND]:
            invoices = by_level[level]
            if invoices:
                next_level = DunningLevel(level.value + 1)
                summary["recommendations"].append({
                    "action": f"Create {next_level.name} dunnings",
                    "count": len(invoices),
                    "invoices": [i.get('invoiceNumber') for i in invoices[:5]]
                })
        
        return summary


# ==================== CLI INTERFACE ====================

def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser"""
    parser = argparse.ArgumentParser(
        prog='sevdesk',
        description='SevDesk Accounting Automation CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  SEVDESK_API_TOKEN    Your SevDesk API token (required)

Examples:
  %(prog)s contacts                          # List all contacts
  %(prog)s contacts --search "Müller"        # Search contacts
  %(prog)s invoices --status open            # List open invoices
  %(prog)s unpaid --days 30                  # Show invoices overdue by 30 days
  %(prog)s create-invoice CONTACT_ID         # Interactive invoice creation
  %(prog)s stats                             # Show API statistics
        """
    )
    
    parser.add_argument(
        '--token', '-t',
        help='API token (or set SEVDESK_API_TOKEN env var)'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable response caching'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {VERSION}'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # contacts command
    contacts_parser = subparsers.add_parser('contacts', help='List contacts')
    contacts_parser.add_argument('--search', '-s', help='Search by name')
    contacts_parser.add_argument('--limit', '-l', type=int, default=100, help='Maximum results')
    
    # contact command
    contact_parser = subparsers.add_parser('contact', help='Get contact details')
    contact_parser.add_argument('contact_id', help='Contact ID')
    
    # create-contact command
    create_contact_parser = subparsers.add_parser('create-contact', help='Create new contact')
    create_contact_parser.add_argument('name', help='Contact name')
    create_contact_parser.add_argument('--email', '-e', help='Email address')
    create_contact_parser.add_argument('--phone', '-p', help='Phone number')
    
    # batch-create-contacts command (v2.2.0)
    batch_contacts_parser = subparsers.add_parser('batch-create-contacts', 
                                                   help='Batch create contacts from CSV')
    batch_contacts_parser.add_argument('csv_file', help='CSV file with contact data')
    batch_contacts_parser.add_argument('--dry-run', action='store_true', 
                                       help='Validate without creating')
    
    # invoices command
    invoices_parser = subparsers.add_parser('invoices', help='List invoices')
    invoices_parser.add_argument('--status', '-s', choices=['draft', 'open', 'paid'], 
                                  help='Filter by status')
    invoices_parser.add_argument('--limit', '-l', type=int, default=100, help='Maximum results')
    invoices_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    invoices_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    
    # invoice command
    invoice_parser = subparsers.add_parser('invoice', help='Get invoice details')
    invoice_parser.add_argument('invoice_id', help='Invoice ID')
    
    # create-invoice command
    create_invoice_parser = subparsers.add_parser('create-invoice', help='Create invoice (interactive)')
    create_invoice_parser.add_argument('contact_id', help='Contact ID')
    
    # unpaid command
    unpaid_parser = subparsers.add_parser('unpaid', help='Show unpaid invoices')
    unpaid_parser.add_argument('--days', '-d', type=int, help='Only show overdue by N days')
    
    # send-invoice command
    send_parser = subparsers.add_parser('send-invoice', help='Send invoice via email')
    send_parser.add_argument('invoice_id', help='Invoice ID')
    send_parser.add_argument('--email', '-e', help='Override recipient email')
    send_parser.add_argument('--subject', '-s', help='Email subject')
    
    # export commands (v2.2.0)
    export_contacts_parser = subparsers.add_parser('export-contacts', help='Export contacts to CSV')
    export_contacts_parser.add_argument('--output', '-o', help='Output filename')
    export_contacts_parser.add_argument('--search', '-s', help='Search filter')
    
    export_invoices_parser = subparsers.add_parser('export-invoices', help='Export invoices to CSV')
    export_invoices_parser.add_argument('--output', '-o', help='Output filename')
    export_invoices_parser.add_argument('--status', choices=['draft', 'open', 'paid'])
    export_invoices_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    export_invoices_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    
    # webhooks command (v2.2.0)
    webhooks_parser = subparsers.add_parser('webhooks', help='List webhooks')
    
    create_webhook_parser = subparsers.add_parser('create-webhook', help='Create webhook')
    create_webhook_parser.add_argument('url', help='Webhook URL')
    create_webhook_parser.add_argument('--events', '-e', required=True,
                                       help='Comma-separated events (e.g., ContactCreate,InvoiceCreate)')
    create_webhook_parser.add_argument('--name', '-n', help='Webhook name')
    
    delete_webhook_parser = subparsers.add_parser('delete-webhook', help='Delete webhook')
    delete_webhook_parser.add_argument('webhook_id', help='Webhook ID')
    
    # health command (v2.2.0)
    health_parser = subparsers.add_parser('health', help='Check API health')
    health_parser.add_argument('--timeout', '-t', type=float, default=5.0, 
                               help='Timeout in seconds')
    
    # queue commands (v2.2.0)
    queue_parser = subparsers.add_parser('queue', help='Show queue status')
    queue_process_parser = subparsers.add_parser('queue-process', help='Process queued operations')
    queue_clear_parser = subparsers.add_parser('queue-clear', help='Clear operation queue')
    
    # batch-update command (v2.2.0)
    batch_update_parser = subparsers.add_parser('batch-update-invoices', 
                                                 help='Batch update invoice status')
    batch_update_parser.add_argument('invoice_ids', help='Comma-separated invoice IDs')
    batch_update_parser.add_argument('--status', required=True, 
                                     choices=['draft', 'open', 'paid'],
                                     help='New status to set')
    
    # bank-accounts command
    subparsers.add_parser('bank-accounts', help='List bank accounts')
    
    # transactions command
    transactions_parser = subparsers.add_parser('transactions', help='List transactions')
    transactions_parser.add_argument('--account', '-a', help='Account ID')
    transactions_parser.add_argument('--limit', '-l', type=int, default=100, help='Maximum results')
    
    # vouchers command
    vouchers_parser = subparsers.add_parser('vouchers', help='List vouchers')
    vouchers_parser.add_argument('--limit', '-l', type=int, default=100, help='Maximum results')
    
    # stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument('--clear-cache', action='store_true', help='Clear cache and show stats')
    
    # dunning commands (v2.3.0)
    dunning_parser = subparsers.add_parser('dunning', help='List overdue invoices with dunning status')
    dunning_parser.add_argument('--days', '-d', type=int, default=1, help='Minimum days overdue')
    dunning_parser.add_argument('--level', '-l', type=int, choices=[1, 2, 3, 4], 
                                help='Max dunning level to include')
    
    dunning_summary_parser = subparsers.add_parser('dunning-summary', 
                                                   help='Show dunning summary and recommendations')
    dunning_summary_parser.add_argument('--days', '-d', type=int, default=1, help='Minimum days overdue')
    
    create_dunning_parser = subparsers.add_parser('create-dunning', 
                                                  help='Create dunning/reminder for invoice')
    create_dunning_parser.add_argument('invoice_id', help='Invoice ID')
    create_dunning_parser.add_argument('--level', '-l', type=int, default=1, 
                                       choices=[1, 2, 3, 4],
                                       help='Dunning level (1=Reminder, 2=First, 3=Second, 4=Final)')
    create_dunning_parser.add_argument('--fee', '-f', type=float, help='Dunning fee amount')
    create_dunning_parser.add_argument('--note', '-n', help='Note/message for dunning')
    create_dunning_parser.add_argument('--due-days', type=int, default=7, 
                                       help='Days until payment due')
    
    batch_dunning_parser = subparsers.add_parser('batch-dunning', 
                                                 help='Create dunnings for multiple invoices')
    batch_dunning_parser.add_argument('invoice_ids', help='Comma-separated invoice IDs')
    batch_dunning_parser.add_argument('--level', '-l', type=int, default=1, 
                                      choices=[1, 2, 3, 4],
                                      help='Dunning level')
    batch_dunning_parser.add_argument('--fee', '-f', type=float, help='Dunning fee amount')
    
    return parser


def handle_contacts_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle contacts command"""
    result = client.list_contacts(search=args.search, limit=args.limit)
    contacts = result.get("objects", [])
    print(f"\n📇 {len(contacts)} Kontakte gefunden:\n")
    for c in contacts[:20]:
        print(client.format_contact(c))


def handle_contact_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle contact command"""
    result = client.get_contact(args.contact_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def handle_create_contact_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle create-contact command"""
    result = client.create_contact(args.name, args.email, args.phone)
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Contact created: {result.get('objects', [{}])[0].get('id')}")


def handle_invoices_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle invoices command"""
    result = client.list_invoices(
        status=args.status,
        limit=args.limit,
        start_date=args.start_date,
        end_date=args.end_date
    )
    invoices = result.get("objects", [])
    print(f"\n📄 {len(invoices)} Rechnungen:\n")
    for inv in invoices[:20]:
        print(client.format_invoice(inv))


def handle_invoice_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle invoice command"""
    result = client.get_invoice(args.invoice_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def handle_create_invoice_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle create-invoice command (interactive)"""
    print("📝 Neue Rechnung erstellen")
    items: List[Dict] = []
    while True:
        name = input("  Position (oder 'fertig'): ")
        if name.lower() in ["fertig", "done", ""]:
            break
        try:
            price = float(input("  Preis (€): "))
            qty = int(input("  Menge [1]: ") or 1)
            tax = float(input("  Steuersatz [19]: ") or 19)
            items.append({"name": name, "price": price, "quantity": qty, "tax_rate": tax})
        except ValueError:
            print("  ⚠️ Ungültige Eingabe")
            continue
    
    if items:
        result = client.create_invoice(args.contact_id, items)
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"\n✅ Rechnung erstellt:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("❌ Keine Positionen eingegeben")


def handle_unpaid_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle unpaid command"""
    invoices = client.get_unpaid_invoices(days_overdue=args.days)
    total_net = sum(inv.get("sumNet", 0) for inv in invoices)
    total_gross = sum(inv.get("sumGross", 0) for inv in invoices)
    print(f"\n💰 {len(invoices)} unbezahlte Rechnungen")
    print(f"   Gesamt Netto: {total_net:.2f} €")
    print(f"   Gesamt Brutto: {total_gross:.2f} €\n")
    for inv in invoices[:20]:
        print(client.format_invoice(inv))


def handle_send_invoice_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle send-invoice command"""
    result = client.send_invoice_email(args.invoice_id, args.email, args.subject)
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Invoice sent successfully")


def handle_bank_accounts_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle bank-accounts command"""
    result = client.list_bank_accounts()
    accounts = result.get("objects", [])
    print(f"\n🏦 {len(accounts)} Bankkonten:\n")
    for acc in accounts:
        print(f"  {acc.get('name')}: {acc.get('balance', 0):.2f} €")


def handle_transactions_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle transactions command"""
    result = client.list_transactions(account_id=args.account, limit=args.limit)
    transactions = result.get("objects", [])
    print(f"\n💳 {len(transactions)} Transaktionen:\n")
    for t in transactions[:20]:
        amount = t.get("amount", 0)
        print(f"  {t.get('date')}: {amount:>10.2f} € - {t.get('payeePayerName', '---')[:30]}")


def handle_vouchers_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle vouchers command"""
    result = client.list_vouchers(limit=args.limit)
    vouchers = result.get("objects", [])
    print(f"\n🧾 {len(vouchers)} Belege:\n")
    for v in vouchers[:20]:
        print(f"  {v.get('voucherDate')}: {v.get('sumNet', 0):.2f} € - {v.get('description', '---')[:40]}")


def handle_stats_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle stats command"""
    if args.clear_cache:
        client.clear_cache()
    
    stats = client.get_stats()
    print(f"\n📊 API Statistics:\n")
    print(f"  Total Requests: {stats['request_count']}")
    print(f"  Cached Requests: {stats['cached_request_count']}")
    print(f"  Circuit State: {stats['circuit_state']}")
    print(f"  Circuit Failures: {stats['circuit_failures']}")
    
    if 'cache' in stats:
        cache = stats['cache']
        print(f"\n  Cache Statistics:")
        print(f"    Entries: {cache['size']}")
        print(f"    Hits: {cache['hits']}")
        print(f"    Misses: {cache['misses']}")
        print(f"    Hit Rate: {cache['hit_rate_percent']}%")
    
    if 'last_response' in stats:
        last = stats['last_response']
        print(f"\n  Last Response:")
        print(f"    Cached: {last['cached']}")
        print(f"    Duration: {last['duration_ms']}ms")
        if last['rate_limit_remaining']:
            print(f"    Rate Limit Remaining: {last['rate_limit_remaining']}")


# ==================== v2.2.0: NEW COMMAND HANDLERS ====================

def handle_health_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle health check command"""
    health = client.health_check(timeout=args.timeout)
    status = "✅ Healthy" if health.healthy else "❌ Unhealthy"
    print(f"\n{status}")
    print(f"  Response Time: {health.response_time_ms:.1f}ms")
    print(f"  API Version: {health.api_version or 'unknown'}")
    print(f"  Message: {health.message}")
    print(f"  Timestamp: {health.timestamp.isoformat()}")
    
    if not health.healthy:
        sys.exit(1)


def handle_export_contacts_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle export-contacts command"""
    result = client.export_contacts_csv(filename=args.output, search=args.search)
    if args.output:
        print(f"✅ Contacts exported to: {result}")
    else:
        print(result)


def handle_export_invoices_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle export-invoices command"""
    result = client.export_invoices_csv(
        filename=args.output,
        status=args.status,
        start_date=args.start_date,
        end_date=args.end_date
    )
    if args.output:
        print(f"✅ Invoices exported to: {result}")
    else:
        print(result)


def handle_batch_create_contacts_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle batch-create-contacts command"""
    try:
        with open(args.csv_file, 'r', encoding='utf-8') as f:
            csv_data = f.read()
        
        result = client.import_contacts_csv(csv_data, dry_run=args.dry_run)
        
        if args.dry_run:
            print(f"\n🔍 Dry Run: Would create {result.success_count} contacts")
            for item in result.successful[:5]:
                print(f"  - {item['data'].get('name', 'N/A')}")
            if len(result.successful) > 5:
                print(f"  ... and {len(result.successful) - 5} more")
        else:
            print(f"\n✅ Batch Result:")
            print(f"  Successful: {result.success_count}/{result.total}")
            print(f"  Failed: {result.failure_count}")
            print(f"  Success Rate: {result.success_rate:.1f}%")
            print(f"  Duration: {result.duration_ms:.0f}ms")
            
            if result.failed:
                print(f"\n❌ Failures:")
                for fail in result.failed[:5]:
                    print(f"  - {fail.get('data', {}).get('name', 'N/A')}: {fail.get('error')}")
    
    except FileNotFoundError:
        print(f"❌ File not found: {args.csv_file}")
        sys.exit(1)


def handle_webhooks_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle webhooks list command"""
    result = client.list_webhooks()
    webhooks = result.get("objects", [])
    print(f"\n🔗 {len(webhooks)} Webhooks:\n")
    for wh in webhooks:
        status = "✅" if wh.get("active") else "❌"
        print(f"  {status} {wh.get('name', 'Unnamed')} ({wh.get('id')})")
        print(f"     URL: {wh.get('url')}")
        print(f"     Events: {', '.join(wh.get('event', []))}")


def handle_create_webhook_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle create-webhook command"""
    try:
        events = [WebhookEvent(e.strip()) for e in args.events.split(',')]
    except ValueError as e:
        print(f"❌ Invalid event type: {e}")
        print(f"Valid events: {[e.value for e in WebhookEvent]}")
        sys.exit(1)
    
    result = client.create_webhook(args.url, events, name=args.name)
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Webhook created: {result.get('objects', [{}])[0].get('id')}")


def handle_delete_webhook_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle delete-webhook command"""
    result = client.delete_webhook(args.webhook_id)
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Webhook deleted: {args.webhook_id}")


def handle_queue_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle queue status command"""
    status = client.get_queue_status()
    print(f"\n📋 Operation Queue:")
    print(f"  Queued: {status['queued_operations']}")
    if status['queued_operations'] > 0:
        print(f"\n  Pending operations:")
        for op in status['operations'][:10]:
            print(f"    - {op['operation']} ({op['timestamp']})")


def handle_queue_process_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle queue-process command"""
    result = client.process_queue()
    print(f"\n✅ Queue Processing Complete:")
    print(f"  Successful: {result.success_count}/{result.total}")
    print(f"  Failed: {result.failure_count}")
    print(f"  Duration: {result.duration_ms:.0f}ms")


def handle_queue_clear_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle queue-clear command"""
    client.clear_queue()
    print("✅ Operation queue cleared")


def handle_batch_update_invoices_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle batch-update-invoices command"""
    invoice_ids = [id.strip() for id in args.invoice_ids.split(',')]
    
    status_map = {
        'draft': InvoiceStatus.DRAFT,
        'open': InvoiceStatus.OPEN,
        'paid': InvoiceStatus.PAID
    }
    new_status = status_map[args.status]
    
    print(f"\n🔄 Updating {len(invoice_ids)} invoices to status '{args.status}'...")
    result = client.batch_update_invoice_status(invoice_ids, new_status)
    
    print(f"✅ Batch Update Complete:")
    print(f"  Successful: {result.success_count}/{result.total}")
    print(f"  Failed: {result.failure_count}")
    print(f"  Duration: {result.duration_ms:.0f}ms")


# ==================== v2.3.0: DUNNING COMMAND HANDLERS ====================

def handle_dunning_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle dunning command - list overdue invoices"""
    max_level = DunningLevel(args.level) if args.level else None
    overdue = client.get_overdue_invoices(days_overdue=args.days, max_dunning_level=max_level)
    
    total_amount = sum(inv.get('sumGross', 0) for inv in overdue)
    
    print(f"\n📋 {len(overdue)} überfällige Rechnungen ({args.days}+ Tage):")
    print(f"   Gesamtbetrag: {total_amount:.2f} €\n")
    
    for inv in overdue[:20]:
        level = inv.get('current_dunning_level', DunningLevel.REMINDER)
        days = inv.get('days_overdue', 0)
        contact = inv.get('contact', {})
        amount = inv.get('sumGross', 0)
        inv_num = inv.get('invoiceNumber', '---')
        
        level_emoji = {1: "📝", 2: "⚠️", 3: "🔔", 4: "🚨"}.get(level.value, "📝")
        
        print(f"  {level_emoji} {inv_num}")
        print(f"     Kontakt: {contact.get('name', '---')}")
        print(f"     Betrag: {amount:.2f} € | Überfällig: {days} Tage")
        print(f"     Mahnstufe: {level.name}")
        print()


def handle_dunning_summary_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle dunning-summary command"""
    summary = client.get_dunning_summary(days_overdue=args.days)
    
    print(f"\n📊 Mahnungs-Übersicht:\n")
    print(f"  Überfällige Rechnungen: {summary['total_overdue']}")
    print(f"  Gesamtbetrag: {summary['total_amount']:.2f} €\n")
    
    print("  Nach Mahnstufe:")
    for level_name, data in summary['by_level'].items():
        if data['count'] > 0:
            print(f"    {level_name}: {data['count']} Rechnungen ({data['amount']:.2f} €)")
    
    if summary['recommendations']:
        print(f"\n  Empfohlene Aktionen:")
        for rec in summary['recommendations']:
            print(f"    → {rec['action']}: {rec['count']} Rechnungen")
            for inv_num in rec['invoices'][:3]:
                print(f"       - {inv_num}")


def handle_create_dunning_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle create-dunning command"""
    level = DunningLevel(args.level)
    
    print(f"\n📝 Erstelle Mahnung (Stufe {level.name})...")
    
    result = client.create_dunning(
        invoice_id=args.invoice_id,
        level=level,
        fee=args.fee,
        note=args.note,
        due_date_days=args.due_days
    )
    
    if result.success:
        print(f"✅ Mahnung erstellt:")
        print(f"   Rechnung: {result.invoice_number}")
        print(f"   Kontakt: {result.contact_name}")
        print(f"   Betrag: {result.amount_due:.2f} €")
        print(f"   Mahnstufe: {result.dunning_level.name}")
    else:
        print(f"❌ Fehler: {result.message}")
        sys.exit(1)


def handle_batch_dunning_command(client: SevDeskClient, args: argparse.Namespace) -> None:
    """Handle batch-dunning command"""
    invoice_ids = [id.strip() for id in args.invoice_ids.split(',')]
    level = DunningLevel(args.level)
    
    print(f"\n🔄 Erstelle {len(invoice_ids)} Mahnungen (Stufe {level.name})...")
    
    results = client.batch_create_dunnings(
        invoice_ids=invoice_ids,
        level=level,
        fee=args.fee
    )
    
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    
    print(f"✅ Batch-Mahnung abgeschlossen:")
    print(f"   Erfolgreich: {len(successful)}/{len(results)}")
    print(f"   Fehlgeschlagen: {len(failed)}")
    
    if failed:
        print(f"\n   Fehler:")
        for r in failed[:5]:
            print(f"     - {r.invoice_number}: {r.message}")


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger('sevdesk').setLevel(logging.DEBUG)
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    try:
        client = SevDeskClient(
            token=args.token,
            enable_cache=not args.no_cache
        )
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    # Command dispatch
    command_handlers = {
        'contacts': handle_contacts_command,
        'contact': handle_contact_command,
        'create-contact': handle_create_contact_command,
        'batch-create-contacts': handle_batch_create_contacts_command,
        'invoices': handle_invoices_command,
        'invoice': handle_invoice_command,
        'create-invoice': handle_create_invoice_command,
        'batch-update-invoices': handle_batch_update_invoices_command,
        'unpaid': handle_unpaid_command,
        'send-invoice': handle_send_invoice_command,
        'bank-accounts': handle_bank_accounts_command,
        'transactions': handle_transactions_command,
        'vouchers': handle_vouchers_command,
        'stats': handle_stats_command,
        'health': handle_health_command,
        'export-contacts': handle_export_contacts_command,
        'export-invoices': handle_export_invoices_command,
        'webhooks': handle_webhooks_command,
        'create-webhook': handle_create_webhook_command,
        'delete-webhook': handle_delete_webhook_command,
        'queue': handle_queue_command,
        'queue-process': handle_queue_process_command,
        'queue-clear': handle_queue_clear_command,
        # v2.3.0: Dunning commands
        'dunning': handle_dunning_command,
        'dunning-summary': handle_dunning_summary_command,
        'create-dunning': handle_create_dunning_command,
        'batch-dunning': handle_batch_dunning_command,
    }
    
    handler = command_handlers.get(args.command)
    if handler:
        try:
            handler(client, args)
        except ValueError as e:
            print(f"❌ Validation Error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"❌ Error: {e}")
            sys.exit(1)
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
