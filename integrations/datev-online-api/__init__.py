"""
DATEV Online API Integration
============================

Vollständige Python-Integration für die DATEV accounting:documents API.

Example:
    >>> from datev_client import DATEVClient, DATEVDocument
    >>> client = DATEVClient(client_id="...", client_secret="...")
    >>> auth_url = client.get_authorization_url("http://localhost:8080/callback")
"""

from .datev_client import (
    DATEVClient,
    DATEVDocument,
    DATEVToken,
    Client,
    DocumentType,
    UploadResult,
    DATEVError,
    DATEVAuthError,
    DATEVRateLimitError,
    DATEVValidationError,
    create_datev_client_from_env,
)

__version__ = "1.0.0"
__author__ = "Navii Automation"
__all__ = [
    "DATEVClient",
    "DATEVDocument",
    "DATEVToken",
    "Client",
    "DocumentType",
    "UploadResult",
    "DATEVError",
    "DATEVAuthError",
    "DATEVRateLimitError",
    "DATEVValidationError",
    "create_datev_client_from_env",
]
