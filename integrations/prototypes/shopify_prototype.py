#!/usr/bin/env python3
"""
Shopify Integration Prototype for Navii Automation
Handles orders, products, customers, and inventory

Usage:
    python shopify_prototype.py --shop navii-demo --action list_orders
    python shopify_prototype.py --shop navii-demo --action get_order --order-id 12345
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import requests
from dataclasses import dataclass


@dataclass
class ShopifyConfig:
    """Configuration for Shopify API"""
    shop_domain: str  # e.g., "navii-demo.myshopify.com"
    access_token: str
    api_version: str = "2024-01"
    
    @property
    def base_url(self) -> str:
        return f"https://{self.shop_domain}/admin/api/{self.api_version}"


class ShopifyClient:
    """Shopify API Client with rate limiting and error handling"""
    
    def __init__(self, config: ShopifyConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "X-Shopify-Access-Token": config.access_token,
            "Content-Type": "application/json"
        })
        self.last_call_time = 0
        self.min_delay = 0.5  # 2 calls/second = 0.5s delay
    
    def _rate_limit(self):
        """Simple rate limiting - ensure we don't exceed 2 calls/second"""
        elapsed = time.time() - self.last_call_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_call_time = time.time()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make a rate-limited request to Shopify API"""
        self._rate_limit()
        
        url = f"{self.config.base_url}/{endpoint}"
        response = self.session.request(method, url, **kwargs)
        
        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 2))
            print(f"⚠️ Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            return self._request(method, endpoint, **kwargs)
        
        response.raise_for_status()
        return response.json() if response.content else {}
    
    # ===== ORDERS =====
    
    def list_orders(self, status: str = "any", limit: int = 50, 
                    created_at_min: Optional[str] = None) -> List[Dict]:
        """List orders with optional filtering"""
        params = {"status": status, "limit": min(limit, 250)}
        if created_at_min:
            params["created_at_min"] = created_at_min
        
        result = self._request("GET", "orders.json", params=params)
        return result.get("orders", [])
    
    def get_order(self, order_id: int) -> Dict:
        """Get a single order by ID"""
        result = self._request("GET", f"orders/{order_id}.json")
        return result.get("order", {})
    
    def update_order(self, order_id: int, data: Dict) -> Dict:
        """Update an order"""
        result = self._request("PUT", f"orders/{order_id}.json", json={"order": data})
        return result.get("order", {})
    
    def cancel_order(self, order_id: int, reason: Optional[str] = None,
                     email: bool = False, restock: bool = True) -> Dict:
        """Cancel an order"""
        payload = {
            "reason": reason or "customer",
            "email": email,
            "restock": restock
        }
        result = self._request("POST", f"orders/{order_id}/cancel.json", json=payload)
        return result.get("order", {})
    
    # ===== PRODUCTS =====
    
    def list_products(self, limit: int = 50, ids: Optional[List[int]] = None) -> List[Dict]:
        """List products"""
        params = {"limit": min(limit, 250)}
        if ids:
            params["ids"] = ",".join(map(str, ids))
        
        result = self._request("GET", "products.json", params=params)
        return result.get("products", [])
    
    def update_product(self, product_id: int, data: Dict) -> Dict:
        """Update a product"""
        result = self._request("PUT", f"products/{product_id}.json", json={"product": data})
        return result.get("product", {})
    
    # ===== CUSTOMERS =====
    
    def list_customers(self, limit: int = 50, query: Optional[str] = None) -> List[Dict]:
        """List customers with optional search"""
        params = {"limit": min(limit, 250)}
        if query:
            params["query"] = query
        
        result = self._request("GET", "customers.json", params=params)
        return result.get("customers", [])
    
    def get_customer(self, customer_id: int) -> Dict:
        """Get a single customer"""
        result = self._request("GET", f"customers/{customer_id}.json")
        return result.get("customer", {})
    
    def create_customer(self, email: str, first_name: str = "", 
                        last_name: str = "", **kwargs) -> Dict:
        """Create a new customer"""
        payload = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            **kwargs
        }
        result = self._request("POST", "customers.json", json={"customer": payload})
        return result.get("customer", {})
    
    # ===== INVENTORY =====
    
    def get_inventory_levels(self, location_id: Optional[int] = None,
                            inventory_item_ids: Optional[List[int]] = None) -> List[Dict]:
        """Get inventory levels"""
        params = {}
        if location_id:
            params["location_ids"] = location_id
        if inventory_item_ids:
            params["inventory_item_ids"] = ",".join(map(str, inventory_item_ids))
        
        result = self._request("GET", "inventory_levels.json", params=params)
        return result.get("inventory_levels", [])
    
    def adjust_inventory(self, inventory_item_id: int, location_id: int,
                         adjustment: int) -> Dict:
        """Adjust inventory quantity"""
        payload = {
            "inventory_item_id": inventory_item_id,
            "location_id": location_id,
            "available_adjustment": adjustment
        }
        result = self._request("POST", "inventory_levels/adjust.json", json=payload)
        return result.get("inventory_level", {})
    
    # ===== WEBHOOKS =====
    
    def list_webhooks(self) -> List[Dict]:
        """List registered webhooks"""
        result = self._request("GET", "webhooks.json")
        return result.get("webhooks", [])
    
    def create_webhook(self, topic: str, address: str, 
                       format: str = "json") -> Dict:
        """Create a webhook subscription"""
        payload = {
            "topic": topic,
            "address": address,
            "format": format
        }
        result = self._request("POST", "webhooks.json", json={"webhook": payload})
        return result.get("webhook", {})


class OrderProcessor:
    """Process orders for German accounting integration"""
    
    def __init__(self, client: ShopifyClient):
        self.client = client
    
    def get_orders_for_invoicing(self, days: int = 1) -> List[Dict]:
        """Get paid orders ready for invoicing"""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        orders = self.client.list_orders(
            status="any",
            created_at_min=since,
            limit=250
        )
        
        # Filter to paid orders only
        paid_orders = [
            o for o in orders 
            if o.get("financial_status") == "paid" and 
            not o.get("tags", "").contains("invoiced")
        ]
        
        return paid_orders
    
    def format_for_sevdesk(self, order: Dict) -> Dict:
        """Format a Shopify order for sevDesk invoice import"""
        customer = order.get("customer", {})
        billing = order.get("billing_address", {})
        
        return {
            "external_id": str(order["id"]),
            "order_number": order.get("name", ""),
            "customer": {
                "email": customer.get("email", ""),
                "first_name": customer.get("first_name", ""),
                "last_name": customer.get("last_name", ""),
                "company": billing.get("company", ""),
            },
            "billing_address": {
                "address1": billing.get("address1", ""),
                "address2": billing.get("address2", ""),
                "city": billing.get("city", ""),
                "zip": billing.get("zip", ""),
                "country": billing.get("country_code", "DE"),
            },
            "line_items": [
                {
                    "name": item.get("name", ""),
                    "sku": item.get("sku", ""),
                    "quantity": item.get("quantity", 1),
                    "price": float(item.get("price", 0)),
                    "tax_rate": 19.0 if item.get("tax_lines") else 0.0,
                }
                for item in order.get("line_items", [])
            ],
            "total_price": float(order.get("total_price", 0)),
            "tax_amount": sum(
                float(t.get("price", 0)) 
                for t in order.get("tax_lines", [])
            ),
            "currency": order.get("currency", "EUR"),
            "created_at": order.get("created_at"),
        }
    
    def mark_as_invoiced(self, order_id: int) -> Dict:
        """Mark an order as invoiced in Shopify"""
        return self.client.update_order(order_id, {"tags": "invoiced"})


def main():
    parser = argparse.ArgumentParser(description="Shopify Integration Prototype")
    parser.add_argument("--shop", required=True, help="Shop domain (e.g., navii-demo)")
    parser.add_argument("--token", help="Access token (or set SHOPIFY_TOKEN env)")
    parser.add_argument("--action", required=True, 
                       choices=["list_orders", "get_order", "list_products",
                               "list_customers", "get_inventory", "invoice_ready"])
    parser.add_argument("--order-id", type=int, help="Order ID for get_order")
    parser.add_argument("--days", type=int, default=1, help="Days back for orders")
    
    args = parser.parse_args()
    
    # Get credentials
    token = args.token or os.getenv("SHOPIFY_TOKEN")
    if not token:
        print("❌ Error: Provide --token or set SHOPIFY_TOKEN environment variable")
        sys.exit(1)
    
    shop_domain = args.shop if ".myshopify.com" in args.shop else f"{args.shop}.myshopify.com"
    config = ShopifyConfig(shop_domain=shop_domain, access_token=token)
    client = ShopifyClient(config)
    
    # Execute action
    if args.action == "list_orders":
        orders = client.list_orders(limit=10)
        print(f"\n📦 Last {len(orders)} Orders:")
        for order in orders:
            print(f"  #{order['name']} - {order['customer'].get('email', 'Guest')} - €{order['total_price']}")
    
    elif args.action == "get_order":
        if not args.order_id:
            print("❌ Error: --order-id required")
            sys.exit(1)
        order = client.get_order(args.order_id)
        print(json.dumps(order, indent=2, default=str))
    
    elif args.action == "list_products":
        products = client.list_products(limit=10)
        print(f"\n📋 Products:")
        for p in products:
            print(f"  {p['title']} - €{p['variants'][0]['price'] if p['variants'] else 'N/A'}")
    
    elif args.action == "list_customers":
        customers = client.list_customers(limit=10)
        print(f"\n👥 Customers:")
        for c in customers:
            print(f"  {c.get('first_name', '')} {c.get('last_name', '')} - {c['email']}")
    
    elif args.action == "get_inventory":
        inventory = client.get_inventory_levels()
        print(f"\n📊 Inventory Levels:")
        for inv in inventory[:10]:
            print(f"  Item {inv['inventory_item_id']}: {inv['available']} available")
    
    elif args.action == "invoice_ready":
        processor = OrderProcessor(client)
        orders = processor.get_orders_for_invoicing(days=args.days)
        print(f"\n📄 Orders ready for invoicing ({len(orders)}):")
        for order in orders:
            formatted = processor.format_for_sevdesk(order)
            print(f"\n  #{order['name']} - {formatted['customer']['email']}")
            print(f"    Total: €{formatted['total_price']}")
            print(f"    Items: {len(formatted['line_items'])}")


if __name__ == "__main__":
    main()
