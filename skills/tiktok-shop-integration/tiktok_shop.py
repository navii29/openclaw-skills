#!/usr/bin/env python3
"""
TikTok Shop Integration
Sync products and manage orders via TikTok Shop API.
"""

import os
import sys
import json
import hmac
import hashlib
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class TikTokProduct:
    """Represents a TikTok Shop product."""
    sku: str
    name: str
    description: str
    price: float
    stock: int
    category_id: str
    images: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TikTokShopAPI:
    """TikTok Shop API client."""
    
    BASE_URL = "https://open-api.tiktokglobalshop.com"
    
    def __init__(self):
        self.app_key = os.getenv("TIKTOK_APP_KEY")
        self.app_secret = os.getenv("TIKTOK_APP_SECRET")
        self.shop_id = os.getenv("TIKTOK_SHOP_ID")
        self.access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
        
        if not all([self.app_key, self.app_secret, self.shop_id]):
            raise ValueError("TIKTOK_APP_KEY, TIKTOK_APP_SECRET, TIKTOK_SHOP_ID required")
    
    def _generate_signature(self, params: Dict[str, str]) -> str:
        """Generate request signature."""
        sorted_params = sorted(params.items())
        param_str = ''.join([f"{k}{v}" for k, v in sorted_params])
        sign_str = f"{self.app_secret}{param_str}{self.app_secret}"
        return hmac.new(
            self.app_secret.encode(),
            sign_str.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make authenticated API request."""
        url = f"{self.BASE_URL}{endpoint}"
        
        # Common params
        request_params = {
            'app_key': self.app_key,
            'timestamp': str(int(datetime.now().timestamp())),
            'shop_id': self.shop_id,
            'version': '202212',
        }
        
        if params:
            request_params.update(params)
        
        # Add signature
        request_params['sign'] = self._generate_signature(request_params)
        
        # Add access token if available
        if self.access_token:
            request_params['access_token'] = self.access_token
        
        try:
            if method == "GET":
                response = requests.get(url, params=request_params, timeout=30)
            elif method == "POST":
                response = requests.post(url, params=request_params, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') != 0:
                raise Exception(f"API Error: {result.get('message', 'Unknown')}")
            
            return result.get('data', {})
            
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get_products(self, page_size: int = 20) -> List[Dict]:
        """Get products from shop."""
        logger.info("📦 Fetching products...")
        
        result = self._make_request(
            "GET",
            "/api/products/search",
            params={'page_size': str(page_size)}
        )
        
        products = result.get('products', [])
        logger.info(f"✅ Found {len(products)} products")
        return products
    
    def create_product(self, product: TikTokProduct) -> str:
        """Create new product."""
        logger.info(f"➕ Creating product: {product.name}")
        
        payload = {
            'product_name': product.name,
            'description': product.description,
            'category_id': product.category_id,
            'skus': [{
                'seller_sku': product.sku,
                'price': str(product.price),
                'stock': product.stock
            }],
            'images': [{'url': url} for url in product.images]
        }
        
        result = self._make_request("POST", "/api/products", data=payload)
        product_id = result.get('product_id')
        
        logger.info(f"✅ Created product: {product_id}")
        return product_id
    
    def update_inventory(self, sku: str, quantity: int) -> bool:
        """Update product inventory."""
        logger.info(f"📊 Updating stock for {sku}: {quantity}")
        
        payload = {
            'skus': [{
                'seller_sku': sku,
                'stock': quantity
            }]
        }
        
        self._make_request("POST", "/api/inventory/update", data=payload)
        logger.info(f"✅ Inventory updated")
        return True
    
    def update_price(self, sku: str, price: float) -> bool:
        """Update product price."""
        logger.info(f"💰 Updating price for {sku}: {price}")
        
        payload = {
            'skus': [{
                'seller_sku': sku,
                'price': str(price)
            }]
        }
        
        self._make_request("POST", "/api/products/prices", data=payload)
        logger.info(f"✅ Price updated")
        return True
    
    def get_orders(self, status: str = "ALL", page_size: int = 20) -> List[Dict]:
        """Get orders."""
        logger.info(f"📋 Fetching orders (status: {status})...")
        
        params = {'page_size': str(page_size)}
        if status != "ALL":
            params['order_status'] = status
        
        result = self._make_request("GET", "/api/orders", params=params)
        orders = result.get('order_list', [])
        
        logger.info(f"✅ Found {len(orders)} orders")
        return orders
    
    def sync_products(self, products_file: str):
        """Sync products from JSON file."""
        with open(products_file, 'r') as f:
            data = json.load(f)
        
        products = data.get('products', [])
        logger.info(f"🔄 Syncing {len(products)} products...")
        
        for p in products:
            product = TikTokProduct(
                sku=p['sku'],
                name=p['name'],
                description=p.get('description', ''),
                price=p['price'],
                stock=p['stock'],
                category_id=p['category_id'],
                images=p.get('images', [])
            )
            
            try:
                self.create_product(product)
            except Exception as e:
                logger.error(f"Failed to create {product.sku}: {e}")


def main():
    parser = argparse.ArgumentParser(description="TikTok Shop Integration")
    parser.add_argument("--sync", help="Sync products from JSON file")
    parser.add_argument("--products", action="store_true", help="List products")
    parser.add_argument("--orders", action="store_true", help="List orders")
    parser.add_argument("--status", default="ALL", help="Order status filter")
    parser.add_argument("--update-stock", nargs=2, metavar=('SKU', 'QTY'), help="Update inventory")
    parser.add_argument("--update-price", nargs=2, metavar=('SKU', 'PRICE'), help="Update price")
    
    args = parser.parse_args()
    
    try:
        api = TikTokShopAPI()
        
        if args.sync:
            api.sync_products(args.sync)
        elif args.products:
            products = api.get_products()
            print(json.dumps(products, indent=2))
        elif args.orders:
            orders = api.get_orders(status=args.status)
            print(json.dumps(orders, indent=2))
        elif args.update_stock:
            api.update_inventory(args.update_stock[0], int(args.update_stock[1]))
        elif args.update_price:
            api.update_price(args.update_price[0], float(args.update_price[1]))
        else:
            parser.print_help()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
