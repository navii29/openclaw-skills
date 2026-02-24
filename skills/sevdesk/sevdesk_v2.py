#!/usr/bin/env python3
"""
SevDesk Skill - German Accounting Automation
Handles invoices, contacts, vouchers, and banking via SevDesk API

Improvements in v2.1:
- Structured logging
- Retry logic with exponential backoff
- Pagination support
- Input validation
- Circuit breaker pattern
- **NEW: Proper CLI with argparse**
- **NEW: TTL-based caching**
- **NEW: Enums for status codes**
- **NEW: Response metadata tracking**
- **NEW: Config file support**
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Callable, TypeVar, Generic, Tuple
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sevdesk')

T = TypeVar('T')

# ==================== CONSTANTS & ENUMS ====================

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

# API Configuration
BASE_URL = "https://my.sevdesk.de/api/v1"
API_TOKEN = os.environ.get("SEVDESK_API_TOKEN", "")
DEFAULT_TIMEOUT = 30
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_MAX_RETRIES = 3
RATE_LIMIT_REQUESTS_PER_SECOND = 10


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
class CacheEntry:
    """Cache entry with TTL"""
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
    """
    
    def __init__(self, token: Optional[str] = None, enable_cache: bool = True, 
                 cache_ttl: int = 300, config_path: Optional[str] = None):
        """
        Initialize SevDesk client
        
        Args:
            token: API token (or set SEVDESK_API_TOKEN env var)
            enable_cache: Enable response caching
            cache_ttl: Default cache TTL in seconds
            config_path: Path to config file (JSON)
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
        version='%(prog)s 2.1.0'
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
        'invoices': handle_invoices_command,
        'invoice': handle_invoice_command,
        'create-invoice': handle_create_invoice_command,
        'unpaid': handle_unpaid_command,
        'send-invoice': handle_send_invoice_command,
        'bank-accounts': handle_bank_accounts_command,
        'transactions': handle_transactions_command,
        'vouchers': handle_vouchers_command,
        'stats': handle_stats_command,
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
