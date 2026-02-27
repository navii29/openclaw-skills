"""
Shopware 6 Admin API Client
Deutsche eCommerce-Plattform Integration für NAVII Automation

Features:
- OAuth2 Client Credentials Authentication
- Core CRUD Operations (Products, Customers, Orders, Categories)
- Automatic Token Refresh
- Rate Limiting with exponential backoff
- Comprehensive Error Handling
- Type hints throughout

API Documentation: https://developer.shopware.com/docs/guides/integrations-api/admin-api
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union, Generator
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShopwareError(Exception):
    """Base exception for Shopware API errors"""
    pass


class AuthenticationError(ShopwareError):
    """Raised when authentication fails"""
    pass


class RateLimitError(ShopwareError):
    """Raised when rate limit is exceeded"""
    pass


class NotFoundError(ShopwareError):
    """Raised when resource is not found"""
    pass


class ValidationError(ShopwareError):
    """Raised when request validation fails"""
    pass


@dataclass
class RateLimitInfo:
    """Rate limit information from API response"""
    limit: int
    remaining: int
    reset_time: Optional[datetime] = None


class Shopware6Client:
    """
    Shopware 6 Admin API Client
    
    German eCommerce platform integration with full CRUD support
    for Products, Customers, Orders, and Categories.
    
    Example:
        client = Shopware6Client(
            base_url="https://shop.example.com",
            client_id="your-client-id",
            client_secret="your-client-secret"
        )
        
        # Get all products
        products = client.get_products(limit=50)
        
        # Create a new product
        new_product = client.create_product({
            "name": "Premium Produkt",
            "productNumber": "PROD-001",
            "stock": 100,
            "price": [{"currencyId": "b7d2554b0ce847cd82f3ac9bd1c0dfca", "gross": 99.99, "net": 84.03}]
        })
    """
    
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 2
    
    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize Shopware 6 client
        
        Args:
            base_url: Shopware instance URL (e.g., https://shop.example.com)
            client_id: OAuth2 Client ID from Shopware Admin
            client_secret: OAuth2 Client Secret from Shopware Admin
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts for rate-limited requests
        """
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout
        self.max_retries = max_retries
        
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._session = requests.Session()
        self._rate_limit_info: Optional[RateLimitInfo] = None
        
        logger.info(f"Shopware6Client initialized for {self.base_url}")
    
    # ==================== AUTHENTICATION ====================
    
    def _authenticate(self) -> str:
        """
        Obtain OAuth2 access token using Client Credentials flow
        
        Returns:
            Access token string
            
        Raises:
            AuthenticationError: If authentication fails
        """
        auth_url = f"{self.base_url}/api/oauth/token"
        
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = self._session.post(
                auth_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            self._access_token = data["access_token"]
            expires_in = data.get("expires_in", 600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info("Successfully authenticated with Shopware 6 API")
            return self._access_token
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"Authentication failed: {e.response.text if e.response else str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during authentication: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg)
    
    def _get_valid_token(self) -> str:
        """Get valid access token, refreshing if necessary"""
        if not self._access_token or datetime.now() >= self._token_expires_at:
            return self._authenticate()
        return self._access_token
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authorization"""
        token = self._get_valid_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    # ==================== RATE LIMITING ====================
    
    def _update_rate_limit_info(self, response: requests.Response):
        """Extract rate limit information from response headers"""
        self._rate_limit_info = RateLimitInfo(
            limit=int(response.headers.get('X-RateLimit-Limit', 0)),
            remaining=int(response.headers.get('X-RateLimit-Remaining', 0)),
            reset_time=None  # Shopware doesn't provide reset time in standard header
        )
    
    def _wait_for_rate_limit_reset(self):
        """Wait for rate limit to reset with exponential backoff"""
        if self._rate_limit_info and self._rate_limit_info.remaining == 0:
            wait_time = 60  # Default wait time
            logger.warning(f"Rate limit reached. Waiting {wait_time} seconds...")
            time.sleep(wait_time)
    
    def _handle_rate_limit(self, attempt: int) -> float:
        """Calculate backoff time for retry"""
        return min(self.BACKOFF_FACTOR ** attempt, 60)  # Cap at 60 seconds
    
    # ==================== CORE HTTP METHODS ====================
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Execute HTTP request with error handling and retry logic
        
        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            json_data: JSON request body
            retry_count: Current retry attempt
            
        Returns:
            JSON response as dictionary
            
        Raises:
            ShopwareError: Various exceptions based on response status
        """
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        
        # Check rate limit before request
        if self._rate_limit_info and self._rate_limit_info.remaining < 5:
            logger.warning("Approaching rate limit, waiting...")
            time.sleep(5)
        
        try:
            response = self._session.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=json_data,
                timeout=self.timeout
            )
            
            # Update rate limit info
            self._update_rate_limit_info(response)
            
            # Handle specific status codes
            if response.status_code == 429:
                if retry_count < self.max_retries:
                    wait_time = self._handle_rate_limit(retry_count)
                    logger.warning(f"Rate limited. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    return self._request(method, endpoint, params, json_data, retry_count + 1)
                raise RateLimitError("Rate limit exceeded. Maximum retries reached.")
            
            if response.status_code == 401:
                # Token expired, re-authenticate and retry
                logger.info("Token expired, re-authenticating...")
                self._access_token = None
                return self._request(method, endpoint, params, json_data, retry_count)
            
            if response.status_code == 404:
                raise NotFoundError(f"Resource not found: {endpoint}")
            
            if response.status_code == 400:
                error_data = response.json() if response.text else {}
                errors = error_data.get('errors', [])
                raise ValidationError(f"Validation error: {errors}")
            
            response.raise_for_status()
            
            if response.status_code == 204:
                return {"success": True}
            
            return response.json() if response.text else {"success": True}
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text if e.response else str(e)}"
            logger.error(error_msg)
            raise ShopwareError(error_msg)
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout for {url}"
            logger.error(error_msg)
            raise ShopwareError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            raise ShopwareError(error_msg)
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute GET request"""
        return self._request("GET", endpoint, params=params)
    
    def _post(self, endpoint: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute POST request"""
        return self._request("POST", endpoint, json_data=json_data)
    
    def _patch(self, endpoint: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute PATCH request"""
        return self._request("PATCH", endpoint, json_data=json_data)
    
    def _delete(self, endpoint: str) -> Dict[str, Any]:
        """Execute DELETE request"""
        return self._request("DELETE", endpoint)
    
    # ==================== PRODUCT OPERATIONS ====================
    
    def get_products(
        self,
        limit: int = 25,
        page: int = 1,
        search: Optional[str] = None,
        filters: Optional[Dict] = None,
        sort: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get products with pagination and filtering
        
        Args:
            limit: Number of items per page (max 100)
            page: Page number
            search: Search term for product name/number
            filters: Additional filters (e.g., {"active": "true"})
            sort: Sort field (e.g., "-createdAt" for descending)
            
        Returns:
            Dictionary with 'data' (list) and 'meta' (pagination info)
        """
        params = {"limit": min(limit, 100), "page": page}
        
        if search:
            params["search"] = search
        if sort:
            params["sort"] = sort
        if filters:
            params.update(filters)
        
        return self._get("product", params)
    
    def get_product(self, product_id: str) -> Dict[str, Any]:
        """
        Get single product by ID
        
        Args:
            product_id: Shopware product UUID
            
        Returns:
            Product data dictionary
        """
        return self._get(f"product/{product_id}")
    
    def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new product
        
        Required fields:
            - name: Product name
            - productNumber: Unique product number/SKU
            - stock: Initial stock quantity
            - price: List of price objects with currencyId, gross, net
            - taxId: Tax rate UUID
            
        Args:
            product_data: Product data dictionary
            
        Returns:
            Created product data
        """
        return self._post("product", product_data)
    
    def update_product(self, product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update existing product
        
        Args:
            product_id: Product UUID
            product_data: Fields to update
            
        Returns:
            Updated product data
        """
        return self._patch(f"product/{product_id}", product_data)
    
    def delete_product(self, product_id: str) -> bool:
        """
        Delete product by ID
        
        Args:
            product_id: Product UUID
            
        Returns:
            True if deleted successfully
        """
        result = self._delete(f"product/{product_id}")
        return result.get("success", False)
    
    def sync_products(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk sync multiple products (upsert operation)
        
        Args:
            products: List of product dictionaries
            
        Returns:
            Sync result with success/error counts
        """
        payload = {
            "entity": "product",
            "action": "upsert",
            "payload": products
        }
        return self._post("_action/sync", payload)
    
    # ==================== CUSTOMER OPERATIONS ====================
    
    def get_customers(
        self,
        limit: int = 25,
        page: int = 1,
        search: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Get customers with pagination
        
        Args:
            limit: Items per page
            page: Page number
            search: Search term (email, name, company)
            filters: Additional filters
            
        Returns:
            Paginated customer list
        """
        params = {"limit": min(limit, 100), "page": page}
        if search:
            params["search"] = search
        if filters:
            params.update(filters)
        
        return self._get("customer", params)
    
    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get single customer by ID"""
        return self._get(f"customer/{customer_id}")
    
    def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Find customer by email address
        
        Args:
            email: Customer email
            
        Returns:
            Customer data or None if not found
        """
        result = self.get_customers(filters={"email": email}, limit=1)
        data = result.get("data", [])
        return data[0] if data else None
    
    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new customer
        
        Required fields:
            - email: Unique email address
            - firstName: First name
            - lastName: Last name
            - password: Customer password
            - groupId: Customer group UUID
            - defaultBillingAddress: Address object
            - defaultShippingAddress: Address object
        """
        return self._post("customer", customer_data)
    
    def update_customer(self, customer_id: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing customer"""
        return self._patch(f"customer/{customer_id}", customer_data)
    
    def delete_customer(self, customer_id: str) -> bool:
        """Delete customer by ID"""
        result = self._delete(f"customer/{customer_id}")
        return result.get("success", False)
    
    # ==================== ORDER OPERATIONS ====================
    
    def get_orders(
        self,
        limit: int = 25,
        page: int = 1,
        filters: Optional[Dict] = None,
        sort: str = "-orderDate"
    ) -> Dict[str, Any]:
        """
        Get orders with pagination
        
        Args:
            limit: Items per page
            page: Page number
            filters: Filters like {"orderDate": "2024-01-01"}
            sort: Sort order (default: newest first)
            
        Returns:
            Paginated order list
        """
        params = {"limit": min(limit, 100), "page": page, "sort": sort}
        if filters:
            params.update(filters)
        
        return self._get("order", params)
    
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get single order by ID"""
        return self._get(f"order/{order_id}")
    
    def get_order_by_order_number(self, order_number: str) -> Optional[Dict[str, Any]]:
        """Find order by order number (e.g., '10001')"""
        result = self.get_orders(filters={"orderNumber": order_number}, limit=1)
        data = result.get("data", [])
        return data[0] if data else None
    
    def update_order_status(self, order_id: str, state_id: str) -> Dict[str, Any]:
        """
        Update order state/status
        
        Args:
            order_id: Order UUID
            state_id: New state UUID
            
        Returns:
            Updated order data
        """
        return self._post(f"_action/order/{order_id}/state", {
            "stateId": state_id
        })
    
    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new order (typically via Store API, but available here)"""
        return self._post("order", order_data)
    
    # ==================== CATEGORY OPERATIONS ====================
    
    def get_categories(
        self,
        limit: int = 100,
        page: int = 1
    ) -> Dict[str, Any]:
        """Get all categories"""
        params = {"limit": limit, "page": page}
        return self._get("category", params)
    
    def get_category(self, category_id: str) -> Dict[str, Any]:
        """Get single category by ID"""
        return self._get(f"category/{category_id}")
    
    def create_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new category
        
        Required fields:
            - name: Category name
            - parentId: Parent category UUID (or null for root)
        """
        return self._post("category", category_data)
    
    def update_category(self, category_id: str, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update category"""
        return self._patch(f"category/{category_id}", category_data)
    
    def delete_category(self, category_id: str) -> bool:
        """Delete category"""
        result = self._delete(f"category/{category_id}")
        return result.get("success", False)
    
    # ==================== UTILITY METHODS ====================
    
    def get_entity_list(self, entity: str, limit: int = 100) -> Generator[Dict, None, None]:
        """
        Paginate through all entities of a type
        
        Args:
            entity: Entity type (product, customer, order, etc.)
            limit: Items per page
            
        Yields:
            Individual entity dictionaries
        """
        page = 1
        while True:
            result = self._get(entity, {"limit": limit, "page": page})
            data = result.get("data", [])
            
            if not data:
                break
            
            for item in data:
                yield item
            
            # Check if we've reached the end
            meta = result.get("meta", {})
            total = meta.get("total", 0)
            if page * limit >= total:
                break
            
            page += 1
    
    def search(
        self,
        entity: str,
        criteria: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Advanced search with Shopware Criteria API
        
        Args:
            entity: Entity type to search
            criteria: Shopware criteria object with filters, sorting, etc.
            
        Returns:
            Search results
        """
        payload = criteria or {}
        return self._post(f"search/{entity}", payload)
    
    def get_health(self) -> Dict[str, Any]:
        """Check API health/status"""
        try:
            # Try to get a simple entity to verify connection
            result = self._get("currency", {"limit": 1})
            return {
                "status": "healthy",
                "connected": True,
                "rate_limit": self._rate_limit_info.remaining if self._rate_limit_info else None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    def close(self):
        """Close HTTP session"""
        self._session.close()
        logger.info("Shopware6Client session closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False


# ==================== HELPER FUNCTIONS ====================

def create_product_payload(
    name: str,
    product_number: str,
    price_gross: float,
    tax_rate: int = 19,
    stock: int = 0,
    description: Optional[str] = None,
    active: bool = True
) -> Dict[str, Any]:
    """
    Helper to create a standard product payload
    
    Args:
        name: Product name
        product_number: SKU/product number
        price_gross: Gross price (including VAT)
        tax_rate: VAT percentage (default 19% Germany)
        stock: Initial stock
        description: Product description
        active: Whether product is active
        
    Returns:
        Product payload dictionary
    """
    # Calculate net price
    price_net = round(price_gross / (1 + tax_rate / 100), 2)
    
    payload = {
        "name": name,
        "productNumber": product_number,
        "stock": stock,
        "active": active,
        "price": [{
            "currencyId": "b7d2554b0ce847cd82f3ac9bd1c0dfca",  # EUR
            "gross": price_gross,
            "net": price_net,
            "linked": True
        }],
        "tax": {"taxRate": tax_rate}
    }
    
    if description:
        payload["description"] = description
    
    return payload


def create_customer_payload(
    email: str,
    first_name: str,
    last_name: str,
    password: str,
    company: Optional[str] = None,
    street: str = "",
    zipcode: str = "",
    city: str = "",
    country_id: str = "5cfa9f194cbb4fa68a4dfd4c99746eb8"  # Germany
) -> Dict[str, Any]:
    """
    Helper to create a standard customer payload
    
    Args:
        email: Customer email
        first_name: First name
        last_name: Last name
        password: Password (will be hashed by Shopware)
        company: Company name (optional)
        street: Street address
        zipcode: Postal code
        city: City
        country_id: Country UUID (default: Germany)
        
    Returns:
        Customer payload dictionary
    """
    address = {
        "firstName": first_name,
        "lastName": last_name,
        "street": street,
        "zipcode": zipcode,
        "city": city,
        "countryId": country_id
    }
    
    if company:
        address["company"] = company
    
    return {
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "password": password,
        "guest": False,
        "defaultBillingAddress": address,
        "defaultShippingAddress": address
    }


# ==================== TESTING / EXAMPLE ====================

if __name__ == "__main__":
    # Example usage
    import os
    
    # Load from environment variables
    client = Shopware6Client(
        base_url=os.getenv("SHOPWARE_URL", "https://shop.example.com"),
        client_id=os.getenv("SHOPWARE_CLIENT_ID"),
        client_secret=os.getenv("SHOPWARE_CLIENT_SECRET")
    )
    
    # Check health
    health = client.get_health()
    print(f"API Health: {health}")
    
    # Get products
    products = client.get_products(limit=5)
    print(f"Found {len(products.get('data', []))} products")
    
    # Create a product example (uncomment to test)
    # new_product = client.create_product(create_product_payload(
    #     name="Test Produkt",
    #     product_number="TEST-001",
    #     price_gross=29.99,
    #     stock=50
    # ))
    # print(f"Created product: {new_product}")
    
    client.close()
