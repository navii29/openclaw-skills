"""
Shopware 6 Integration Package
Deutsche eCommerce-Plattform für NAVII Automation
"""

from .shopware6_client import (
    Shopware6Client,
    ShopwareError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    RateLimitInfo,
    create_product_payload,
    create_customer_payload
)

__version__ = "1.0.0"
__author__ = "NAVII Automation"
__all__ = [
    "Shopware6Client",
    "ShopwareError",
    "AuthenticationError", 
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "RateLimitInfo",
    "create_product_payload",
    "create_customer_payload"
]
