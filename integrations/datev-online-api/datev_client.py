"""
DATEV Online API Integration
==============================

Vollständige Python-Integration für die DATEV Online API (accounting:documents).
Unterstützt OAuth2 mit PKCE, Dokumenten-Upload, Fehlerbehandlung und Rate-Limiting.

Author: Navii Automation
Version: 1.0.0
"""

import os
import json
import time
import base64
import hashlib
import secrets
import logging
from typing import Optional, Dict, List, Union, BinaryIO
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import mimetypes

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# DATEV API Endpoints
DATEV_SANDBOX_BASE_URL = "https://accounting-documents.api.datev.de/platform-sandbox/v2"
DATEV_PRODUCTION_BASE_URL = "https://accounting-documents.api.datev.de/platform/v2"
DATEV_SANDBOX_AUTH_URL = "https://login.datev.de/openidsandbox"
DATEV_PRODUCTION_AUTH_URL = "https://login.datev.de/openid"
DATEV_TOKEN_URL = "https://api.datev.de/token"


class DATEVError(Exception):
    """Base exception for DATEV API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 error_code: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class DATEVAuthError(DATEVError):
    """Authentication/Authorization error."""
    pass


class DATEVRateLimitError(DATEVError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class DATEVValidationError(DATEVError):
    """Validation error (400 Bad Request)."""
    pass


@dataclass
class DATEVToken:
    """OAuth2 Token representation."""
    access_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "Bearer"
    scope: str = ""
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 60s buffer)."""
        return datetime.now() >= (self.expires_at - timedelta(seconds=60))


@dataclass
class DATEVDocument:
    """Represents a document to upload."""
    file_path: Optional[str] = None
    file_content: Optional[bytes] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None
    document_type: Optional[str] = None  # e.g., "Rechnungseingang", "Rechnungsausgang"
    note: Optional[str] = None
    
    def __post_init__(self):
        if self.file_path and not self.file_content:
            path = Path(self.file_path)
            self.filename = self.filename or path.name
            if not self.content_type:
                self.content_type, _ = mimetypes.guess_type(str(path))
                self.content_type = self.content_type or "application/octet-stream"
        
        if not self.filename:
            raise ValueError("Either file_path with valid filename or filename must be provided")
    
    def get_content(self) -> bytes:
        """Get file content as bytes."""
        if self.file_content:
            return self.file_content
        if self.file_path:
            with open(self.file_path, 'rb') as f:
                return f.read()
        raise ValueError("No file content available")


@dataclass
class DocumentType:
    """Represents a DATEV document type."""
    id: str
    name: str
    description: Optional[str] = None


@dataclass
class Client:
    """Represents a DATEV client (Mandant)."""
    client_id: str
    name: str
    consultant_number: Optional[str] = None
    client_number: Optional[str] = None
    
    @property
    def full_client_id(self) -> str:
        """Returns the full client ID in format {consultant_number}-{client_number}."""
        if self.consultant_number and self.client_number:
            return f"{self.consultant_number}-{self.client_number}"
        return self.client_id


@dataclass
class UploadResult:
    """Result of a document upload."""
    success: bool
    document_id: Optional[str] = None
    files: List[Dict] = field(default_factory=list)
    document_type: Optional[str] = None
    note: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None


class RateLimiter:
    """Simple rate limiter for API requests."""
    
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[float] = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove old requests outside the time window
        self.requests = [t for t in self.requests if now - t < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            # Calculate wait time
            oldest_request = min(self.requests)
            wait_time = self.time_window - (now - oldest_request) + 1
            if wait_time > 0:
                logger.warning(f"Rate limit approaching. Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
        
        self.requests.append(now)


class DATEVClient:
    """
    DATEV Online API Client
    =======================
    
    Vollständiger Client für die DATEV accounting:documents API.
    
    Features:
    - OAuth2 mit PKCE Authentifizierung
    - Automatische Token-Refresh (single-use refresh tokens)
    - Dokumenten-Upload mit Metadaten
    - Mandanten (Clients) Verwaltung
    - Belegtypen (Document Types) Verwaltung
    - Umfassende Fehlerbehandlung
    - Rate-Limiting
    
    Usage:
        client = DATEVClient(
            client_id="your-client-id",
            client_secret="your-client-secret",
            sandbox=True
        )
        
        # OAuth2 Flow starten
        auth_url = client.get_authorization_url(redirect_uri="http://localhost:8080/callback")
        # ... User authentifizieren und code erhalten ...
        
        token = client.exchange_code(code, redirect_uri="http://localhost:8080/callback")
        
        # Dokument hochladen
        result = client.upload_document(
            client_id="12345-1",
            document=DATEVDocument(
                file_path="/path/to/invoice.pdf",
                document_type="Rechnungseingang",
                note="Rechnung von Muster GmbH"
            )
        )
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        sandbox: bool = True,
        token: Optional[DATEVToken] = None,
        rate_limit_max: int = 60,
        rate_limit_window: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize DATEV API Client.
        
        Args:
            client_id: OAuth2 Client ID from DATEV Developer Portal
            client_secret: OAuth2 Client Secret
            sandbox: Use sandbox environment (default: True)
            token: Existing token (optional)
            rate_limit_max: Max requests per time window
            rate_limit_window: Time window in seconds
            max_retries: Max retries for failed requests
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.sandbox = sandbox
        self.token = token
        self.rate_limiter = RateLimiter(rate_limit_max, rate_limit_window)
        
        # Setup base URLs
        self.base_url = DATEV_SANDBOX_BASE_URL if sandbox else DATEV_PRODUCTION_BASE_URL
        self.auth_url = DATEV_SANDBOX_AUTH_URL if sandbox else DATEV_PRODUCTION_AUTH_URL
        
        # Setup session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # PKCE state
        self._code_verifier: Optional[str] = None
        self._state: Optional[str] = None
        self._nonce: Optional[str] = None
    
    def _generate_pkce(self) -> tuple:
        """Generate PKCE code_verifier and code_challenge."""
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def _generate_state(self, min_length: int = 20) -> str:
        """Generate state parameter (min 20 chars per DATEV spec)."""
        return secrets.token_urlsafe(max(32, min_length))
    
    def get_authorization_url(
        self,
        redirect_uri: str,
        scope: str = "openid accounting:documents",
        enable_windows_sso: bool = True
    ) -> str:
        """
        Generate OAuth2 authorization URL with PKCE.
        
        Args:
            redirect_uri: Redirect URI registered in DATEV Developer Portal
            scope: OAuth scopes (default: "openid accounting:documents")
            enable_windows_sso: Enable Windows SSO (DATEV-Benutzer)
        
        Returns:
            Full authorization URL to redirect user to
        """
        self._code_verifier, code_challenge = self._generate_pkce()
        self._state = self._generate_state()
        self._nonce = self._generate_state()
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": scope,
            "redirect_uri": redirect_uri,
            "state": self._state,
            "nonce": self._nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        if enable_windows_sso:
            params["enableWindowsSso"] = "true"
        
        auth_endpoint = f"{self.auth_url}/authorize"
        
        from urllib.parse import urlencode, urljoin
        return f"{auth_endpoint}?{urlencode(params)}"
    
    def exchange_code(
        self,
        code: str,
        redirect_uri: str,
        state: Optional[str] = None
    ) -> DATEVToken:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from callback
            redirect_uri: Same redirect URI used in authorization request
            state: State parameter for verification (optional)
        
        Returns:
            DATEVToken with access and refresh tokens
        
        Raises:
            DATEVAuthError: If code exchange fails
        """
        if state and self._state and state != self._state:
            raise DATEVAuthError("State mismatch - possible CSRF attack")
        
        if not self._code_verifier:
            raise DATEVAuthError("No code_verifier available. Call get_authorization_url first.")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()}"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": self._code_verifier
        }
        
        try:
            response = self.session.post(
                DATEV_TOKEN_URL,
                headers=headers,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            
            expires_in = token_data.get("expires_in", 900)
            self.token = DATEVToken(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token", ""),
                expires_at=datetime.now() + timedelta(seconds=expires_in),
                token_type=token_data.get("token_type", "Bearer"),
                scope=token_data.get("scope", "")
            )
            
            logger.info("Successfully obtained access token")
            return self.token
            
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = response.json()
            except:
                error_detail = response.text
            
            raise DATEVAuthError(
                f"Token exchange failed: {e}",
                status_code=response.status_code,
                details=error_detail
            )
    
    def refresh_token(self) -> DATEVToken:
        """
        Refresh access token using refresh token.
        
        IMPORTANT: DATEV uses single-use refresh tokens. Each refresh
        invalidates the old refresh token and returns a new one.
        
        Returns:
            New DATEVToken
        
        Raises:
            DATEVAuthError: If refresh fails
        """
        if not self.token or not self.token.refresh_token:
            raise DATEVAuthError("No refresh token available")
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()}"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.token.refresh_token
        }
        
        try:
            response = self.session.post(
                DATEV_TOKEN_URL,
                headers=headers,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            
            expires_in = token_data.get("expires_in", 900)
            self.token = DATEVToken(
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token", self.token.refresh_token),
                expires_at=datetime.now() + timedelta(seconds=expires_in),
                token_type=token_data.get("token_type", "Bearer"),
                scope=token_data.get("scope", "")
            )
            
            logger.info("Successfully refreshed access token")
            return self.token
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 400:
                # Refresh token expired or invalid
                raise DATEVAuthError(
                    "Refresh token expired or invalid. User must re-authenticate.",
                    status_code=400,
                    error_code="invalid_grant"
                )
            raise DATEVAuthError(
                f"Token refresh failed: {e}",
                status_code=response.status_code
            )
    
    def _ensure_valid_token(self):
        """Ensure token is valid, refresh if needed."""
        if not self.token:
            raise DATEVAuthError("No token available. Authenticate first.")
        
        if self.token.is_expired:
            logger.info("Access token expired, refreshing...")
            self.refresh_token()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get headers with authorization."""
        self._ensure_valid_token()
        return {
            "Authorization": f"Bearer {self.token.access_token}",
            "X-DATEV-Client-Id": self.client_id,
            "Accept": "application/json"
        }
    
    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle API response and errors."""
        # Check for rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise DATEVRateLimitError(
                f"Rate limit exceeded. Retry after {retry_after}s",
                retry_after=retry_after
            )
        
        # Handle auth errors
        if response.status_code in (401, 403):
            try:
                error_data = response.json()
                error_desc = error_data.get("error_description", "Unknown auth error")
            except:
                error_desc = response.text
            
            raise DATEVAuthError(
                f"Authentication failed: {error_desc}",
                status_code=response.status_code
            )
        
        # Handle validation errors
        if response.status_code == 400:
            try:
                error_data = response.json()
            except:
                error_data = {"message": response.text}
            
            raise DATEVValidationError(
                f"Validation error: {error_data}",
                status_code=400,
                details=error_data
            )
        
        # Handle other errors
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise DATEVError(
                f"API request failed: {e}",
                status_code=response.status_code
            )
        
        # Return JSON response or empty dict
        try:
            return response.json()
        except:
            return {}
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict:
        """Make authenticated API request with rate limiting."""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_auth_headers()
        
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        
        response = self.session.request(
            method=method,
            url=url,
            headers=headers,
            timeout=30,
            **kwargs
        )
        
        return self._handle_response(response)
    
    # =====================================================================
    # CLIENT (MANDANT) OPERATIONS
    # =====================================================================
    
    def list_clients(self) -> List[Client]:
        """
        List all accessible clients (Mandanten).
        
        Returns:
            List of Client objects
        """
        data = self._make_request("GET", "/clients")
        
        clients = []
        for item in data.get("clients", []):
            clients.append(Client(
                client_id=item.get("id", ""),
                name=item.get("name", ""),
                consultant_number=item.get("consultant_number"),
                client_number=item.get("client_number")
            ))
        
        return clients
    
    def get_client(self, client_id: str) -> Client:
        """
        Get details for a specific client.
        
        Args:
            client_id: Client ID (format: consultant_number-client_number)
        
        Returns:
            Client object
        """
        data = self._make_request("GET", f"/clients/{client_id}")
        
        return Client(
            client_id=data.get("id", ""),
            name=data.get("name", ""),
            consultant_number=data.get("consultant_number"),
            client_number=data.get("client_number")
        )
    
    # =====================================================================
    # DOCUMENT TYPE (BELEGTYP) OPERATIONS
    # =====================================================================
    
    def list_document_types(self, client_id: str) -> List[DocumentType]:
        """
        List available document types for a client.
        
        Args:
            client_id: Client ID
        
        Returns:
            List of DocumentType objects
        """
        data = self._make_request("GET", f"/clients/{client_id}/document-types")
        
        types = []
        for item in data.get("document_types", []):
            types.append(DocumentType(
                id=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description")
            ))
        
        return types
    
    def get_document_type(self, client_id: str, type_id: str) -> DocumentType:
        """
        Get details for a specific document type.
        
        Args:
            client_id: Client ID
            type_id: Document type ID
        
        Returns:
            DocumentType object
        """
        data = self._make_request(
            "GET",
            f"/clients/{client_id}/document-types/{type_id}"
        )
        
        return DocumentType(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description")
        )
    
    # =====================================================================
    # DOCUMENT (BELEG) OPERATIONS
    # =====================================================================
    
    def upload_document(
        self,
        client_id: str,
        document: DATEVDocument,
        idempotent_key: Optional[str] = None
    ) -> UploadResult:
        """
        Upload a document to DATEV Unternehmen online.
        
        Args:
            client_id: Client ID (format: consultant_number-client_number)
            document: DATEVDocument to upload
            idempotent_key: Optional idempotency key for retry safety
        
        Returns:
            UploadResult with status and document details
        
        Raises:
            DATEVError: If upload fails
        """
        # Prepare multipart form data
        files = {
            "file": (
                document.filename,
                document.get_content(),
                document.content_type or "application/octet-stream"
            )
        }
        
        data = {}
        if document.document_type:
            data["document_type"] = document.document_type
        if document.note:
            data["note"] = document.note
        
        headers = {}
        if idempotent_key:
            headers["Idempotency-Key"] = idempotent_key
        
        try:
            result = self._make_request(
                "POST",
                f"/clients/{client_id}/documents",
                files=files,
                data=data,
                headers=headers
            )
            
            return UploadResult(
                success=True,
                document_id=result.get("id"),
                files=result.get("files", []),
                document_type=result.get("document_type"),
                note=result.get("note"),
                status_code=201
            )
            
        except DATEVError as e:
            return UploadResult(
                success=False,
                error=str(e),
                status_code=e.status_code
            )
    
    def upload_document_with_id(
        self,
        client_id: str,
        document_id: str,
        document: DATEVDocument
    ) -> UploadResult:
        """
        Upload a document with a specific ID (PUT request).
        
        Args:
            client_id: Client ID
            document_id: Specific document ID to use
            document: DATEVDocument to upload
        
        Returns:
            UploadResult
        """
        files = {
            "file": (
                document.filename,
                document.get_content(),
                document.content_type or "application/octet-stream"
            )
        }
        
        data = {}
        if document.document_type:
            data["document_type"] = document.document_type
        if document.note:
            data["note"] = document.note
        
        try:
            result = self._make_request(
                "PUT",
                f"/clients/{client_id}/documents/{document_id}",
                files=files,
                data=data
            )
            
            return UploadResult(
                success=True,
                document_id=result.get("id"),
                files=result.get("files", []),
                document_type=result.get("document_type"),
                note=result.get("note"),
                status_code=200
            )
            
        except DATEVError as e:
            return UploadResult(
                success=False,
                error=str(e),
                status_code=e.status_code
            )
    
    def validate_filename(self, filename: str) -> str:
        """
        Validate and sanitize filename according to DATEV specs.
        
        DATEV erlaubt: Space &()+-._ 0-9A-Za-zÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ
        
        Args:
            filename: Original filename
        
        Returns:
            Sanitized filename
        """
        allowed_chars = set(
            " &()+-._0123456789"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz"
            "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß"
            "àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ"
        )
        
        sanitized = []
        for char in filename:
            if char in allowed_chars:
                sanitized.append(char)
            else:
                sanitized.append("_")
        
        return "".join(sanitized)
    
    # =====================================================================
    # UTILITY METHODS
    # =====================================================================
    
    def revoke_token(self, token_type: str = "access_token") -> bool:
        """
        Revoke access or refresh token.
        
        Args:
            token_type: "access_token" or "refresh_token"
        
        Returns:
            True if successful
        """
        if not self.token:
            return False
        
        token = self.token.access_token if token_type == "access_token" else self.token.refresh_token
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()}"
        }
        
        data = {
            "token": token,
            "token_type_hint": token_type
        }
        
        try:
            response = self.session.post(
                f"{self.auth_url}/revoke",
                headers=headers,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Successfully revoked {token_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False
    
    def get_user_info(self) -> Dict:
        """
        Get information about the authenticated user.
        
        Returns:
            User info dictionary
        """
        self._ensure_valid_token()
        
        response = self.session.get(
            f"{self.auth_url}/userinfo",
            headers={"Authorization": f"Bearer {self.token.access_token}"},
            timeout=30
        )
        
        return self._handle_response(response)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_datev_client_from_env(sandbox: bool = True) -> DATEVClient:
    """
    Create DATEV client from environment variables.
    
    Required env vars:
    - DATEV_CLIENT_ID
    - DATEV_CLIENT_SECRET
    
    Optional:
    - DATEV_ACCESS_TOKEN
    - DATEV_REFRESH_TOKEN
    - DATEV_TOKEN_EXPIRES_AT
    """
    client_id = os.environ.get("DATEV_CLIENT_ID")
    client_secret = os.environ.get("DATEV_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("DATEV_CLIENT_ID and DATEV_CLIENT_SECRET must be set")
    
    token = None
    if os.environ.get("DATEV_ACCESS_TOKEN"):
        expires_at = datetime.now() + timedelta(hours=1)
        expires_str = os.environ.get("DATEV_TOKEN_EXPIRES_AT")
        if expires_str:
            try:
                expires_at = datetime.fromisoformat(expires_str)
            except:
                pass
        
        token = DATEVToken(
            access_token=os.environ["DATEV_ACCESS_TOKEN"],
            refresh_token=os.environ.get("DATEV_REFRESH_TOKEN", ""),
            expires_at=expires_at
        )
    
    return DATEVClient(
        client_id=client_id,
        client_secret=client_secret,
        sandbox=sandbox,
        token=token
    )


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DATEV Online API Client")
    parser.add_argument("--client-id", help="OAuth2 Client ID", default=os.environ.get("DATEV_CLIENT_ID"))
    parser.add_argument("--client-secret", help="OAuth2 Client Secret", default=os.environ.get("DATEV_CLIENT_SECRET"))
    parser.add_argument("--sandbox", action="store_true", help="Use sandbox environment")
    parser.add_argument("--production", action="store_true", help="Use production environment")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Auth command
    auth_parser = subparsers.add_parser("auth", help="Get authorization URL")
    auth_parser.add_argument("--redirect-uri", required=True, help="Redirect URI")
    
    # Token command
    token_parser = subparsers.add_parser("token", help="Exchange code for token")
    token_parser.add_argument("--code", required=True, help="Authorization code")
    token_parser.add_argument("--redirect-uri", required=True, help="Redirect URI")
    
    # List clients
    clients_parser = subparsers.add_parser("clients", help="List accessible clients")
    
    # List document types
    types_parser = subparsers.add_parser("types", help="List document types")
    types_parser.add_argument("--client-id", required=True, help="Client ID")
    
    # Upload document
    upload_parser = subparsers.add_parser("upload", help="Upload document")
    upload_parser.add_argument("--client-id", required=True, help="Client ID")
    upload_parser.add_argument("--file", required=True, help="File path")
    upload_parser.add_argument("--doc-type", help="Document type")
    upload_parser.add_argument("--note", help="Note for tax consultant")
    
    args = parser.parse_args()
    
    if not args.client_id or not args.client_secret:
        parser.error("--client-id and --client-secret are required (or set env vars)")
    
    sandbox = not args.production
    client = DATEVClient(
        client_id=args.client_id,
        client_secret=args.client_secret,
        sandbox=sandbox
    )
    
    if args.command == "auth":
        url = client.get_authorization_url(redirect_uri=args.redirect_uri)
        print(f"Authorization URL:\n{url}")
    
    elif args.command == "token":
        token = client.exchange_code(code=args.code, redirect_uri=args.redirect_uri)
        print(f"Access Token: {token.access_token}")
        print(f"Refresh Token: {token.refresh_token}")
        print(f"Expires At: {token.expires_at.isoformat()}")
    
    elif args.command == "clients":
        # Requires token - load from env
        client = create_datev_client_from_env(sandbox)
        clients = client.list_clients()
        for c in clients:
            print(f"{c.client_id}: {c.name}")
    
    elif args.command == "types":
        client = create_datev_client_from_env(sandbox)
        types = client.list_document_types(args.client_id)
        for t in types:
            print(f"{t.id}: {t.name}")
    
    elif args.command == "upload":
        client = create_datev_client_from_env(sandbox)
        doc = DATEVDocument(
            file_path=args.file,
            document_type=args.doc_type,
            note=args.note
        )
        result = client.upload_document(args.client_id, doc)
        if result.success:
            print(f"Upload successful! Document ID: {result.document_id}")
        else:
            print(f"Upload failed: {result.error}")
    
    else:
        parser.print_help()
