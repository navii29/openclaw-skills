#!/usr/bin/env python3
"""
WooCommerce Integration Prototype for Navii Automation
WordPress/WooCommerce ist extrem populär in Deutschland (30%+ Marktanteil)

Usage:
    python woocommerce_prototype.py --url https://shop.de --key ck_... --secret cs_... --action list_orders
"""

import os
import sys
import json
import base64
import argparse
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
import requests
from dataclasses import dataclass


@dataclass
class WooCommerceConfig:
    """Configuration for WooCommerce API"""
    store_url: str  # e.g., "https://mein-shop.de"
    consumer_key: str
    consumer_secret: str
    api_version: str = "wc/v3"
    use_query_auth: bool = False  # Use query params instead of basic auth (for HTTP sites)
    
    @property
    def base_url(self) -> str:
        return f"{self.store_url}/wp-json/{self.api_version}"


class WooCommerceClient:
    """WooCommerce API Client with OAuth1-like authentication"""
    
    def __init__(self, config: WooCommerceConfig):
        self.config = config
        self.session = requests.Session()
        
        if config.use_query_auth:
            # For HTTP sites, use query parameter authentication
            self.auth = None
        else:
            # For HTTPS sites, use basic auth
            self.auth = (config.consumer_key, config.consumer_secret)
    
    def _get_auth_params(self) -> Dict:
        """Get authentication parameters"""
        if self.config.use_query_auth:
            return {
                "consumer_key": self.config.consumer_key,
                "consumer_secret": self.config.consumer_secret
            }
        return {}
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make a request to WooCommerce API"""
        url = f"{self.config.base_url}/{endpoint}"
        
        # Add auth params for HTTP sites
        if self.config.use_query_auth:
            params = kwargs.get("params", {})
            params.update(self._get_auth_params())
            kwargs["params"] = params
        
        response = self.session.request(
            method, url, 
            auth=self.auth if not self.config.use_query_auth else None,
            **kwargs
        )
        
        # Handle WooCommerce specific errors
        if response.status_code == 401:
            error_data = response.json() if response.content else {}
            raise Exception(f"Authentication failed: {error_data.get('message', 'Invalid credentials')}")
        
        if response.status_code == 403:
            raise Exception("Permission denied. Check API key permissions in WooCommerce settings.")
        
        response.raise_for_status()
        return response.json() if response.content else {}
    
    # ===== ORDERS =====
    
    def list_orders(self, status: Optional[str] = None, 
                   after: Optional[str] = None,
                   before: Optional[str] = None,
                   per_page: int = 10) -> List[Dict]:
        """List orders with filtering
        
        Status options: pending, processing, on-hold, completed, cancelled, refunded, failed, trash
        """
        params = {"per_page": min(per_page, 100)}
        if status:
            params["status"] = status
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        
        return self._request("GET", "orders", params=params)
    
    def get_order(self, order_id: int) -> Dict:
        """Get a single order"""
        return self._request("GET", f"orders/{order_id}")
    
    def update_order(self, order_id: int, data: Dict) -> Dict:
        """Update an order"""
        return self._request("PUT", f"orders/{order_id}", json=data)
    
    def create_order(self, data: Dict) -> Dict:
        """Create a new order"""
        return self._request("POST", "orders", json=data)
    
    def delete_order(self, order_id: int, force: bool = False) -> Dict:
        """Delete an order"""
        params = {"force": "true" if force else "false"}
        return self._request("DELETE", f"orders/{order_id}", params=params)
    
    # ===== PRODUCTS =====
    
    def list_products(self, per_page: int = 10, 
                     category: Optional[str] = None,
                     search: Optional[str] = None) -> List[Dict]:
        """List products"""
        params = {"per_page": min(per_page, 100)}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        
        return self._request("GET", "products", params=params)
    
    def get_product(self, product_id: int) -> Dict:
        """Get a single product"""
        return self._request("GET", f"products/{product_id}")
    
    def update_product(self, product_id: int, data: Dict) -> Dict:
        """Update a product"""
        return self._request("PUT", f"products/{product_id}", json=data)
    
    def update_stock(self, product_id: int, stock_quantity: int) -> Dict:
        """Update product stock quantity"""
        return self.update_product(product_id, {"stock_quantity": stock_quantity})
    
    # ===== CUSTOMERS =====
    
    def list_customers(self, per_page: int = 10, 
                      email: Optional[str] = None,
                      search: Optional[str] = None) -> List[Dict]:
        """List customers"""
        params = {"per_page": min(per_page, 100)}
        if email:
            params["email"] = email
        if search:
            params["search"] = search
        
        return self._request("GET", "customers", params=params)
    
    def get_customer(self, customer_id: int) -> Dict:
        """Get a single customer"""
        return self._request("GET", f"customers/{customer_id}")
    
    def create_customer(self, email: str, first_name: str = "", 
                       last_name: str = "", **kwargs) -> Dict:
        """Create a new customer"""
        data = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            **kwargs
        }
        return self._request("POST", "customers", json=data)
    
    # ===== REPORTS =====
    
    def get_sales_report(self, period: str = "month",
                        date_min: Optional[str] = None,
                        date_max: Optional[str] = None) -> List[Dict]:
        """Get sales report"""
        params = {"period": period}
        if date_min:
            params["date_min"] = date_min
        if date_max:
            params["date_max"] = date_max
        
        return self._request("GET", "reports/sales", params=params)
    
    def get_products_report(self, per_page: int = 10) -> List[Dict]:
        """Get products report"""
        params = {"per_page": min(per_page, 100)}
        return self._request("GET", "reports/products", params=params)
    
    def get_stock_report(self, per_page: int = 100) -> List[Dict]:
        """Get low stock report"""
        params = {"per_page": min(per_page, 100), "low_in_stock": True}
        return self._request("GET", "reports/stock", params=params)


class GermanInvoiceFormatter:
    """Format WooCommerce orders for German accounting systems"""
    
    def format_for_sevdesk(self, order: Dict) -> Dict:
        """Format order for sevDesk invoice import"""
        billing = order.get("billing", {})
        
        # Calculate totals
        total = float(order.get("total", 0))
        total_tax = float(order.get("total_tax", 0))
        
        # Determine tax rate
        if total > 0:
            tax_rate = round((total_tax / (total - total_tax)) * 100, 1)
        else:
            tax_rate = 19.0
        
        return {
            "external_id": str(order["id"]),
            "order_number": order.get("number", ""),
            "order_date": order.get("date_created", ""),
            "status": order.get("status", ""),
            "customer": {
                "email": billing.get("email", ""),
                "first_name": billing.get("first_name", ""),
                "last_name": billing.get("last_name", ""),
                "company": billing.get("company", ""),
            },
            "billing_address": {
                "first_name": billing.get("first_name", ""),
                "last_name": billing.get("last_name", ""),
                "company": billing.get("company", ""),
                "address_1": billing.get("address_1", ""),
                "address_2": billing.get("address_2", ""),
                "city": billing.get("city", ""),
                "postcode": billing.get("postcode", ""),
                "country": billing.get("country", "DE"),
            },
            "line_items": [
                {
                    "name": item.get("name", ""),
                    "sku": item.get("sku", ""),
                    "quantity": item.get("quantity", 1),
                    "unit_price": float(item.get("price", 0)),
                    "total": float(item.get("total", 0)),
                    "tax_rate": tax_rate,
                }
                for item in order.get("line_items", [])
            ],
            "shipping_lines": [
                {
                    "method": line.get("method_title", ""),
                    "total": float(line.get("total", 0)),
                }
                for line in order.get("shipping_lines", [])
            ],
            "subtotal": float(order.get("subtotal", 0)),
            "shipping_total": float(order.get("shipping_total", 0)),
            "total_tax": total_tax,
            "total": total,
            "currency": order.get("currency", "EUR"),
            "payment_method": order.get("payment_method", ""),
            "payment_method_title": order.get("payment_method_title", ""),
        }
    
    def format_for_datev(self, order: Dict) -> Dict:
        """Format order for DATEV import (CSV format)"""
        formatted = self.format_for_sevdesk(order)
        
        # DATEV requires specific fields
        return {
            "belegnummer": formatted["order_number"],
            "belegdatum": formatted["order_date"][:10] if formatted["order_date"] else "",
            "konto": "8400",  # Erlöskonto für Deutschland
            "gkto": "1200",   # Forderungen
            "umsatz": formatted["total"],
            "steuersatz": 19 if formatted["total_tax"] > 0 else 0,
            "ust": formatted["total_tax"],
            "buchungstext": f"Online-Bestellung {formatted['order_number']}",
            "kundennummer": formatted["customer"]["email"],
        }


class OrderAutomation:
    """Automate common WooCommerce workflows"""
    
    def __init__(self, client: WooCommerceClient):
        self.client = client
        self.formatter = GermanInvoiceFormatter()
    
    def get_orders_for_invoicing(self, days: int = 1, 
                                 status: str = "completed") -> List[Dict]:
        """Get orders ready for invoicing"""
        after = (datetime.now() - timedelta(days=days)).isoformat()
        
        orders = self.client.list_orders(
            status=status,
            after=after,
            per_page=100
        )
        
        # Filter out already invoiced orders
        # Note: WooCommerce doesn't have a built-in "invoiced" flag
        # You might want to use custom order meta or a plugin like Germanized
        return orders
    
    def get_abandoned_carts(self, days: int = 7) -> List[Dict]:
        """Get pending orders that might be abandoned carts"""
        after = (datetime.now() - timedelta(days=days)).isoformat()
        before = (datetime.now() - timedelta(hours=1)).isoformat()
        
        return self.client.list_orders(
            status="pending",
            after=after,
            before=before,
            per_page=100
        )
    
    def check_low_stock(self, threshold: int = 5) -> List[Dict]:
        """Get products with low stock"""
        products = self.client.list_products(per_page=100)
        
        low_stock = []
        for product in products:
            stock = product.get("stock_quantity", 0)
            manage_stock = product.get("manage_stock", False)
            
            if manage_stock and stock <= threshold:
                low_stock.append({
                    "id": product["id"],
                    "name": product["name"],
                    "sku": product.get("sku", ""),
                    "stock_quantity": stock,
                    "threshold": threshold,
                })
        
        return low_stock
    
    def get_vat_report(self, year: int, month: int) -> Dict:
        """Generate VAT report for German tax filing"""
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        
        orders = self.client.list_orders(
            status="completed",
            after=start.isoformat(),
            before=end.isoformat(),
            per_page=100
        )
        
        # Calculate VAT by rate
        vat_by_rate = {}
        total_net = 0
        total_gross = 0
        
        for order in orders:
            formatted = self.formatter.format_for_sevdesk(order)
            
            for item in formatted["line_items"]:
                rate = item["tax_rate"]
                net = item["total"] / (1 + rate / 100) if rate > 0 else item["total"]
                vat = item["total"] - net
                
                if rate not in vat_by_rate:
                    vat_by_rate[rate] = {"net": 0, "vat": 0}
                
                vat_by_rate[rate]["net"] += net
                vat_by_rate[rate]["vat"] += vat
                total_net += net
                total_gross += item["total"]
        
        return {
            "period": f"{year}-{month:02d}",
            "order_count": len(orders),
            "vat_by_rate": vat_by_rate,
            "total_net": total_net,
            "total_vat": total_gross - total_net,
            "total_gross": total_gross,
        }


def main():
    parser = argparse.ArgumentParser(description="WooCommerce Integration Prototype")
    parser.add_argument("--url", required=True, help="Store URL (e.g., https://shop.de)")
    parser.add_argument("--key", help="Consumer Key (or set WC_CONSUMER_KEY env)")
    parser.add_argument("--secret", help="Consumer Secret (or set WC_CONSUMER_SECRET env)")
    parser.add_argument("--use-query-auth", action="store_true", 
                       help="Use query parameter auth (for HTTP sites)")
    parser.add_argument("--action", required=True,
                       choices=["list_orders", "get_order", "list_products",
                               "list_customers", "invoice_ready", "low_stock",
                               "vat_report", "abandoned_carts"])
    parser.add_argument("--order-id", type=int, help="Order ID")
    parser.add_argument("--days", type=int, default=7, help="Days back")
    parser.add_argument("--year", type=int, default=datetime.now().year)
    parser.add_argument("--month", type=int, default=datetime.now().month)
    
    args = parser.parse_args()
    
    # Get credentials
    key = args.key or os.getenv("WC_CONSUMER_KEY")
    secret = args.secret or os.getenv("WC_CONSUMER_SECRET")
    
    if not key or not secret:
        print("❌ Error: Provide --key/--secret or set WC_CONSUMER_KEY/WC_CONSUMER_SECRET")
        sys.exit(1)
    
    config = WooCommerceConfig(
        store_url=args.url.rstrip("/"),
        consumer_key=key,
        consumer_secret=secret,
        use_query_auth=args.use_query_auth
    )
    client = WooCommerceClient(config)
    automation = OrderAutomation(client)
    
    # Execute action
    if args.action == "list_orders":
        orders = client.list_orders(per_page=10)
        print(f"\n📦 Orders ({len(orders)}):")
        for order in orders:
            print(f"  #{order['number']} - {order['status']} - €{order['total']}")
    
    elif args.action == "get_order":
        if not args.order_id:
            print("❌ Error: --order-id required")
            sys.exit(1)
        order = client.get_order(args.order_id)
        formatted = automation.formatter.format_for_sevdesk(order)
        print(json.dumps(formatted, indent=2, ensure_ascii=False))
    
    elif args.action == "list_products":
        products = client.list_products(per_page=10)
        print(f"\n📋 Products ({len(products)}):")
        for p in products:
            stock = p.get("stock_quantity", "N/A")
            print(f"  {p['name']} - €{p['price']} - Stock: {stock}")
    
    elif args.action == "list_customers":
        customers = client.list_customers(per_page=10)
        print(f"\n👥 Customers ({len(customers)}):")
        for c in customers:
            print(f"  {c.get('first_name', '')} {c.get('last_name', '')} - {c['email']}")
    
    elif args.action == "invoice_ready":
        orders = automation.get_orders_for_invoicing(days=args.days)
        print(f"\n📄 Orders ready for invoicing ({len(orders)}):")
        for order in orders[:5]:
            formatted = automation.formatter.format_for_sevdesk(order)
            print(f"\n  #{formatted['order_number']} - {formatted['customer']['email']}")
            print(f"    Total: €{formatted['total']}")
    
    elif args.action == "low_stock":
        products = automation.check_low_stock(threshold=5)
        print(f"\n⚠️ Low Stock Products ({len(products)}):")
        for p in products[:10]:
            print(f"  {p['name']} (SKU: {p['sku']}) - Stock: {p['stock_quantity']}")
    
    elif args.action == "vat_report":
        report = automation.get_vat_report(args.year, args.month)
        print(f"\n📊 VAT Report: {report['period']}")
        print(f"  Orders: {report['order_count']}")
        for rate, values in report['vat_by_rate'].items():
            print(f"  {rate}% MwSt: Netto €{values['net']:.2f}, MwSt €{values['vat']:.2f}")
        print(f"  Total: €{report['total_gross']:.2f}")
    
    elif args.action == "abandoned_carts":
        orders = automation.get_abandoned_carts(days=args.days)
        print(f"\n🛒 Potential Abandoned Carts ({len(orders)}):")
        for order in orders[:10]:
            print(f"  #{order['number']} - €{order['total']} - {order['date_created']}")


if __name__ == "__main__":
    main()
