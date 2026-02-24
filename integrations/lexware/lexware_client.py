"""
Lexware API Python Integration
==============================

Eine vollständige Python-Integration für die Lexware (ehemals lexoffice) REST API.

Deutsche Buchhaltungssoftware für:
- Rechnungsstellung
- Kontaktverwaltung
- Artikelverwaltung
- Belegbuchhaltung
- XRechnung (E-Rechnung für Behörden)

API-Dokumentation: https://developers.lexware.io
"""

import time
import json
import logging
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('lexware')


class LexwareError(Exception):
    """Base exception for Lexware API errors."""
    pass


class LexwareAuthError(LexwareError):
    """Authentication error (401)."""
    pass


class LexwareRateLimitError(LexwareError):
    """Rate limit exceeded (429)."""
    pass


class LexwareNotFoundError(LexwareError):
    """Resource not found (404)."""
    pass


class LexwareValidationError(LexwareError):
    """Validation error (400, 422)."""
    pass


class ContactType(Enum):
    """Contact types."""
    CUSTOMER = "customer"
    VENDOR = "vendor"


class ArticleType(Enum):
    """Article types."""
    PRODUCT = "PRODUCT"
    SERVICE = "SERVICE"


class VoucherStatus(Enum):
    """Voucher statuses."""
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOIDED = "voided"


@dataclass
class Price:
    """Price object for articles."""
    netPrice: Optional[float] = None
    grossPrice: Optional[float] = None
    leadingPrice: str = "NET"  # "NET" or "GROSS"
    taxRate: float = 19  # German VAT: 0, 7, or 19


@dataclass
class Article:
    """Article data class."""
    title: str
    type: str  # "PRODUCT" or "SERVICE"
    unitName: str
    articleNumber: Optional[str] = None
    description: Optional[str] = None
    gtin: Optional[str] = None
    note: Optional[str] = None
    price: Optional[Price] = None
    id: Optional[str] = None
    version: Optional[int] = None


@dataclass
class Address:
    """Address data class."""
    street: str
    zip: str
    city: str
    countryCode: str = "DE"
    supplement: Optional[str] = None


@dataclass
class Person:
    """Person data class."""
    lastName: str
    firstName: Optional[str] = None
    salutation: Optional[str] = None


@dataclass
class Company:
    """Company data class."""
    name: str
    taxNumber: Optional[str] = None
    vatRegistrationId: Optional[str] = None
    allowTaxFreeInvoices: bool = False


@dataclass
class Contact:
    """Contact data class."""
    roles: Dict[str, Any]  # {"customer": {}, "vendor": {}}
    company: Optional[Company] = None
    person: Optional[Person] = None
    addresses: Optional[Dict[str, List[Address]]] = None
    emailAddresses: Optional[Dict[str, List[str]]] = None
    phoneNumbers: Optional[Dict[str, List[str]]] = None
    note: Optional[str] = None
    id: Optional[str] = None
    version: Optional[int] = None


@dataclass
class LineItem:
    """Line item for invoices."""
    name: str
    quantity: float
    unitName: str
    unitPrice: Dict[str, Any]  # {"netAmount": 100, "grossAmount": 119, "taxRate": 19}
    description: Optional[str] = None


class TokenBucketRateLimiter:
    """
    Token Bucket Algorithm for Rate Limiting.
    
    Lexware API allows 2 requests per second.
    Implements the token bucket algorithm to stay within limits.
    """
    
    def __init__(self, rate: float = 2.0, capacity: int = 2):
        """
        Initialize rate limiter.
        
        Args:
            rate: Tokens added per second (default: 2.0)
            capacity: Maximum bucket capacity (default: 2)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = False
    
    def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            Wait time in seconds (0 if no wait needed)
        """
        now = time.time()
        elapsed = now - self.last_update
        
        # Add new tokens based on elapsed time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return 0.0
        
        # Calculate wait time
        wait_time = (tokens - self.tokens) / self.rate
        self.tokens = 0
        return wait_time
    
    def wait_if_needed(self, tokens: int = 1):
        """Wait if rate limit would be exceeded."""
        wait_time = self.acquire(tokens)
        if wait_time > 0:
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            time.sleep(wait_time)


class LexwareClient:
    """
    Lexware API Client
    
    Full-featured client for the Lexware (lexoffice) REST API.
    
    Features:
    - Bearer Token Authentication
    - Automatic Rate Limiting (2 req/s)
    - Full CRUD operations
    - Comprehensive error handling
    - Retry logic with exponential backoff
    - Type hints and data classes
    
    Usage:
        client = LexwareClient(api_key="your-api-key")
        
        # Create contact
        contact = Contact(
            roles={"customer": {}},
            person=Person(firstName="Max", lastName="Mustermann"),
            addresses={"billing": [Address(street="Hauptstr. 1", zip="12345", city="Berlin")]}
        )
        result = client.create_contact(contact)
        
        # Create invoice
        invoice = client.create_invoice(
            contact_id=result.id,
            line_items=[LineItem(...)],
            headline="Rechnung"
        )
    """
    
    BASE_URL = "https://api.lexware.io"
    API_VERSION = "v1"
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        respect_rate_limit: bool = True
    ):
        """
        Initialize Lexware client.
        
        Args:
            api_key: Your Lexware API key (from https://app.lexware.de/addons/public-api)
            base_url: Optional custom base URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for failed requests
            respect_rate_limit: Whether to enforce rate limiting
        """
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.respect_rate_limit = respect_rate_limit
        
        # Initialize rate limiter (2 requests per second)
        self.rate_limiter = TokenBucketRateLimiter(rate=2.0, capacity=2)
        
        # Setup session with connection pooling
        self.session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=0  # We handle retries manually
        )
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        
        # Default headers
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Lexware-Python-Client/1.0'
        })
        
        logger.info("Lexware client initialized")
    
    def _apply_rate_limit(self):
        """Apply rate limiting before request."""
        if self.respect_rate_limit:
            self.rate_limiter.wait_if_needed()
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions.
        
        Args:
            response: HTTP response object
            
        Returns:
            Parsed JSON response
            
        Raises:
            LexwareAuthError: On 401
            LexwareNotFoundError: On 404
            LexwareRateLimitError: On 429
            LexwareValidationError: On 400, 422
            LexwareError: On other errors
        """
        status_code = response.status_code
        
        if status_code == 200 or status_code == 201:
            return response.json() if response.content else {}
        
        if status_code == 204:
            return {}
        
        error_data = {}
        try:
            error_data = response.json()
        except:
            error_data = {"message": response.text}
        
        error_msg = error_data.get('message', error_data.get('error', 'Unknown error'))
        
        if status_code == 401:
            raise LexwareAuthError(f"Authentication failed: {error_msg}")
        elif status_code == 404:
            raise LexwareNotFoundError(f"Resource not found: {error_msg}")
        elif status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            raise LexwareRateLimitError(
                f"Rate limit exceeded. Retry after {retry_after}s: {error_msg}",
                retry_after=retry_after
            )
        elif status_code in (400, 422):
            raise LexwareValidationError(f"Validation error: {error_msg}")
        elif status_code >= 500:
            raise LexwareError(f"Server error ({status_code}): {error_msg}")
        else:
            raise LexwareError(f"HTTP {status_code}: {error_msg}")
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            retry_count: Current retry attempt
            
        Returns:
            Parsed JSON response
        """
        url = urljoin(f"{self.base_url}/", f"{self.API_VERSION}/{endpoint}")
        
        # Apply rate limiting
        self._apply_rate_limit()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.warning(f"Request timeout, retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self._request(method, endpoint, data, params, retry_count + 1)
            raise LexwareError("Request timeout after max retries")
            
        except requests.exceptions.ConnectionError:
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count
                logger.warning(f"Connection error, retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self._request(method, endpoint, data, params, retry_count + 1)
            raise LexwareError("Connection error after max retries")
            
        except LexwareRateLimitError as e:
            if retry_count < self.max_retries:
                wait_time = getattr(e, 'retry_after', 60)
                logger.warning(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                return self._request(method, endpoint, data, params, retry_count + 1)
            raise
            
        except (LexwareAuthError, LexwareValidationError):
            # Don't retry auth or validation errors
            raise
    
    # ==================== CONTACTS ====================
    
    def create_contact(self, contact: Contact) -> Dict[str, Any]:
        """
        Create a new contact (customer or vendor).
        
        Args:
            contact: Contact object
            
        Returns:
            Created contact with id and resourceUri
        """
        data = self._contact_to_dict(contact)
        result = self._request("POST", "contacts", data=data)
        logger.info(f"Created contact: {result.get('id')}")
        return result
    
    def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """
        Get a contact by ID.
        
        Args:
            contact_id: Contact UUID
            
        Returns:
            Contact data
        """
        return self._request("GET", f"contacts/{contact_id}")
    
    def update_contact(self, contact_id: str, contact: Contact) -> Dict[str, Any]:
        """
        Update an existing contact.
        
        Args:
            contact_id: Contact UUID
            contact: Updated contact data
            
        Returns:
            Updated contact
        """
        data = self._contact_to_dict(contact)
        result = self._request("PUT", f"contacts/{contact_id}", data=data)
        logger.info(f"Updated contact: {contact_id}")
        return result
    
    def list_contacts(
        self,
        page: int = 0,
        size: int = 25,
        email: Optional[str] = None,
        name: Optional[str] = None,
        number: Optional[int] = None,
        customer: Optional[bool] = None,
        vendor: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        List contacts with optional filters.
        
        Args:
            page: Page number (0-indexed)
            size: Page size (max 100)
            email: Filter by email address
            name: Filter by name (min 3 chars)
            number: Filter by customer/vendor number
            customer: Filter by customer role
            vendor: Filter by vendor role
            
        Returns:
            Paginated list of contacts
        """
        params = {'page': page, 'size': min(size, 100)}
        
        if email:
            params['email'] = email
        if name and len(name) >= 3:
            params['name'] = name
        if number:
            params['number'] = number
        if customer is not None:
            params['customer'] = str(customer).lower()
        if vendor is not None:
            params['vendor'] = str(vendor).lower()
        
        return self._request("GET", "contacts", params=params)
    
    def _contact_to_dict(self, contact: Contact) -> Dict[str, Any]:
        """Convert Contact dataclass to API-compatible dict."""
        data = {
            'roles': contact.roles,
            'version': contact.version or 0
        }
        
        if contact.company:
            data['company'] = {
                'name': contact.company.name,
                'taxNumber': contact.company.taxNumber,
                'vatRegistrationId': contact.company.vatRegistrationId,
                'allowTaxFreeInvoices': contact.company.allowTaxFreeInvoices
            }
            # Handle contact persons if present
            if hasattr(contact.company, 'contactPersons') and contact.company.contactPersons:
                data['company']['contactPersons'] = contact.company.contactPersons
        
        if contact.person:
            data['person'] = {
                'salutation': contact.person.salutation,
                'firstName': contact.person.firstName,
                'lastName': contact.person.lastName
            }
        
        if contact.addresses:
            data['addresses'] = {}
            for addr_type, addresses in contact.addresses.items():
                data['addresses'][addr_type] = [
                    {
                        'supplement': a.supplement,
                        'street': a.street,
                        'zip': a.zip,
                        'city': a.city,
                        'countryCode': a.countryCode
                    }
                    for a in addresses
                ]
        
        if contact.emailAddresses:
            data['emailAddresses'] = contact.emailAddresses
        
        if contact.phoneNumbers:
            data['phoneNumbers'] = contact.phoneNumbers
        
        if contact.note:
            data['note'] = contact.note
        
        # Remove None values
        return self._clean_dict(data)
    
    # ==================== ARTICLES ====================
    
    def create_article(self, article: Article) -> Dict[str, Any]:
        """
        Create a new article (product or service).
        
        Args:
            article: Article object
            
        Returns:
            Created article with id
        """
        data = self._article_to_dict(article)
        result = self._request("POST", "articles", data=data)
        logger.info(f"Created article: {result.get('id')}")
        return result
    
    def get_article(self, article_id: str) -> Dict[str, Any]:
        """Get article by ID."""
        return self._request("GET", f"articles/{article_id}")
    
    def update_article(self, article_id: str, article: Article) -> Dict[str, Any]:
        """
        Update an existing article.
        
        Note: Must include current version for optimistic locking.
        """
        data = self._article_to_dict(article)
        result = self._request("PUT", f"articles/{article_id}", data=data)
        logger.info(f"Updated article: {article_id}")
        return result
    
    def delete_article(self, article_id: str) -> bool:
        """
        Delete an article.
        
        Returns:
            True if deleted successfully
        """
        self._request("DELETE", f"articles/{article_id}")
        logger.info(f"Deleted article: {article_id}")
        return True
    
    def list_articles(
        self,
        page: int = 0,
        size: int = 25,
        article_number: Optional[str] = None,
        gtin: Optional[str] = None,
        type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List articles with optional filters.
        
        Args:
            page: Page number
            size: Page size
            article_number: Filter by article number
            gtin: Filter by GTIN/EAN
            type: Filter by type (PRODUCT or SERVICE)
        """
        params = {'page': page, 'size': min(size, 100)}
        
        if article_number:
            params['articleNumber'] = article_number
        if gtin:
            params['gtin'] = gtin
        if type:
            params['type'] = type
        
        return self._request("GET", "articles", params=params)
    
    def _article_to_dict(self, article: Article) -> Dict[str, Any]:
        """Convert Article dataclass to API-compatible dict."""
        data = {
            'title': article.title,
            'type': article.type,
            'unitName': article.unitName,
        }
        
        if article.articleNumber:
            data['articleNumber'] = article.articleNumber
        if article.description:
            data['description'] = article.description
        if article.gtin:
            data['gtin'] = article.gtin
        if article.note:
            data['note'] = article.note
        if article.price:
            data['price'] = {
                'leadingPrice': article.price.leadingPrice,
                'taxRate': article.price.taxRate
            }
            if article.price.leadingPrice == "NET" and article.price.netPrice:
                data['price']['netPrice'] = article.price.netPrice
            elif article.price.leadingPrice == "GROSS" and article.price.grossPrice:
                data['price']['grossPrice'] = article.price.grossPrice
        if article.version is not None:
            data['version'] = article.version
        
        return data
    
    # ==================== INVOICES ====================
    
    def create_invoice(
        self,
        contact_id: str,
        line_items: List[LineItem],
        headline: str = "Rechnung",
        voucher_date: Optional[str] = None,
        due_date: Optional[str] = None,
        address: Optional[Dict] = None,
        note: Optional[str] = None,
        payment_conditions: Optional[Dict] = None,
        shipping_conditions: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Create a new invoice.
        
        Args:
            contact_id: Contact UUID
            line_items: List of line items
            headline: Invoice headline
            voucher_date: Invoice date (ISO 8601 format)
            due_date: Due date (ISO 8601 format)
            address: Billing address (if different from contact)
            note: Invoice note
            payment_conditions: Payment terms
            shipping_conditions: Shipping terms
            
        Returns:
            Created invoice with id
        """
        data = {
            'voucherDate': voucher_date or self._today(),
            'address': address or {},
            'lineItems': [self._line_item_to_dict(item) for item in line_items],
            'headline': headline
        }
        
        if due_date:
            data['dueDate'] = due_date
        if note:
            data['note'] = note
        if payment_conditions:
            data['paymentConditions'] = payment_conditions
        if shipping_conditions:
            data['shippingConditions'] = shipping_conditions
        
        # Add contact reference
        data['address']['contactId'] = contact_id
        
        result = self._request("POST", "invoices", data=self._clean_dict(data))
        logger.info(f"Created invoice: {result.get('id')}")
        return result
    
    def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Get invoice by ID."""
        return self._request("GET", f"invoices/{invoice_id}")
    
    def render_invoice_pdf(self, invoice_id: str) -> bytes:
        """
        Render invoice as PDF.
        
        Returns:
            PDF content as bytes
        """
        url = f"{self.base_url}/{self.API_VERSION}/invoices/{invoice_id}/document"
        self._apply_rate_limit()
        
        response = self.session.get(url, timeout=self.timeout)
        
        if response.status_code == 200:
            return response.content
        
        self._handle_response(response)  # Will raise appropriate error
        return b""
    
    def list_invoices(
        self,
        page: int = 0,
        size: int = 25,
        status: Optional[str] = None,
        contact_id: Optional[str] = None,
        voucher_number: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List invoices with filters.
        
        Args:
            status: Filter by status (draft, open, paid, voided)
            contact_id: Filter by contact
            voucher_number: Filter by invoice number
            from_date: Start date (ISO 8601)
            to_date: End date (ISO 8601)
        """
        params = {'page': page, 'size': min(size, 100)}
        
        if status:
            params['status'] = status
        if contact_id:
            params['contactId'] = contact_id
        if voucher_number:
            params['voucherNumber'] = voucher_number
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
        
        return self._request("GET", "invoices", params=params)
    
    def _line_item_to_dict(self, item: LineItem) -> Dict[str, Any]:
        """Convert LineItem to dict."""
        data = {
            'name': item.name,
            'quantity': item.quantity,
            'unitName': item.unitName,
            'unitPrice': item.unitPrice
        }
        if item.description:
            data['description'] = item.description
        return data
    
    # ==================== VOUCHERS ====================
    
    def create_voucher(
        self,
        voucher_date: str,
        total_amount: float,
        voucher_type: str = "expense",
        note: Optional[str] = None,
        contact_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a bookkeeping voucher (Beleg).
        
        Used for expenses, receipts, etc.
        
        Args:
            voucher_date: Date (ISO 8601)
            total_amount: Total amount
            voucher_type: Type (expense, income)
            note: Description
            contact_id: Optional contact reference
        """
        data = {
            'voucherDate': voucher_date,
            'totalAmount': total_amount,
            'type': voucher_type
        }
        
        if note:
            data['note'] = note
        if contact_id:
            data['contactId'] = contact_id
        
        result = self._request("POST", "vouchers", data=data)
        logger.info(f"Created voucher: {result.get('id')}")
        return result
    
    def upload_voucher_file(
        self,
        voucher_id: str,
        file_path: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to a voucher (e.g., receipt scan).
        
        Args:
            voucher_id: Voucher UUID
            file_path: Path to file
            filename: Optional custom filename
            
        Returns:
            File upload result
        """
        url = f"{self.base_url}/{self.API_VERSION}/vouchers/{voucher_id}/files"
        self._apply_rate_limit()
        
        filename = filename or file_path.split('/')[-1]
        
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f)}
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            response = requests.post(
                url,
                files=files,
                headers=headers,
                timeout=self.timeout
            )
        
        return self._handle_response(response)
    
    # ==================== PROFILE ====================
    
    def get_profile(self) -> Dict[str, Any]:
        """
        Get organization profile information.
        
        Returns:
            Organization details including company name, tax info, etc.
        """
        return self._request("GET", "profile")
    
    # ==================== EVENT SUBSCRIPTIONS ====================
    
    def create_webhook(
        self,
        event_type: str,
        callback_url: str
    ) -> Dict[str, Any]:
        """
        Create a webhook subscription for real-time events.
        
        Supported events:
        - contact.created, contact.changed, contact.deleted
        - invoice.created, invoice.changed, invoice.deleted
        - voucher.created, voucher.changed, voucher.booked
        
        Args:
            event_type: Event type to subscribe to
            callback_url: Your webhook endpoint URL
        """
        data = {
            'eventType': event_type,
            'callbackUrl': callback_url
        }
        
        result = self._request("POST", "event-subscriptions", data=data)
        logger.info(f"Created webhook for {event_type}")
        return result
    
    def list_webhooks(self) -> Dict[str, Any]:
        """List all webhook subscriptions."""
        return self._request("GET", "event-subscriptions")
    
    def delete_webhook(self, subscription_id: str) -> bool:
        """Delete a webhook subscription."""
        self._request("DELETE", f"event-subscriptions/{subscription_id}")
        logger.info(f"Deleted webhook: {subscription_id}")
        return True
    
    # ==================== HELPERS ====================
    
    def _today(self) -> str:
        """Get today's date in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _clean_dict(self, data: Dict) -> Dict:
        """Remove None values from dict recursively."""
        if isinstance(data, dict):
            return {
                k: self._clean_dict(v)
                for k, v in data.items()
                if v is not None and v != {}
            }
        elif isinstance(data, list):
            return [self._clean_dict(item) for item in data]
        return data
    
    def health_check(self) -> bool:
        """
        Check API connectivity.
        
        Returns:
            True if API is accessible
        """
        try:
            self.get_profile()
            return True
        except LexwareError:
            return False


# Convenience factory function
def create_lexware_client(api_key: Optional[str] = None) -> LexwareClient:
    """
    Factory function to create a Lexware client.
    
    Args:
        api_key: API key (or from LEXWARE_API_KEY env var)
        
    Returns:
        Configured LexwareClient instance
    """
    import os
    
    api_key = api_key or os.environ.get('LEXWARE_API_KEY')
    
    if not api_key:
        raise LexwareError(
            "API key required. Provide as argument or set LEXWARE_API_KEY environment variable.\n"
            "Get your API key at: https://app.lexware.de/addons/public-api"
        )
    
    return LexwareClient(api_key=api_key)
