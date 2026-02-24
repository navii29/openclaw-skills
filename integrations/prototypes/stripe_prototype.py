#!/usr/bin/env python3
"""
Stripe Integration Prototype for Navii Automation
Handles payments, subscriptions, invoices, and webhooks

Usage:
    python stripe_prototype.py --action list_customers
    python stripe_prototype.py --action get_customer --customer-id cus_...
    python stripe_prototype.py --action sync_invoices --days 30
"""

import os
import sys
import json
import hmac
import hashlib
import argparse
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import requests
from dataclasses import dataclass


@dataclass
class StripeConfig:
    """Configuration for Stripe API"""
    api_key: str  # sk_test_... or sk_live_...
    webhook_secret: Optional[str] = None
    
    @property
    def is_live(self) -> bool:
        return self.api_key.startswith("sk_live_")


class StripeClient:
    """Stripe API Client with rate limiting and webhook verification"""
    
    BASE_URL = "https://api.stripe.com/v1"
    
    def __init__(self, config: StripeConfig):
        self.config = config
        self.session = requests.Session()
        self.session.auth = (config.api_key, "")  # Stripe uses basic auth with API key
        self.session.headers.update({
            "Stripe-Version": "2024-06-20",
            "Content-Type": "application/x-www-form-urlencoded"
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make a request to Stripe API"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Convert JSON to form-encoded for POST/PUT
        if method in ("POST", "PUT") and "json" in kwargs:
            data = self._flatten_dict(kwargs.pop("json"))
            kwargs["data"] = data
        
        response = self.session.request(method, url, **kwargs)
        
        if response.status_code == 429:
            # Rate limited - wait and retry
            import time
            retry_after = int(response.headers.get('Retry-After', 1))
            print(f"⚠️ Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after)
            return self._request(method, endpoint, **kwargs)
        
        response.raise_for_status()
        return response.json() if response.content else {}
    
    def _flatten_dict(self, d: Dict, parent_key: str = "", sep: str = "[") -> Dict:
        """Flatten nested dict for form encoding"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}]" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep="[").items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]").items())
                    else:
                        items.append((f"{new_key}[]", item))
            else:
                items.append((new_key, v))
        return dict(items)
    
    # ===== CUSTOMERS =====
    
    def list_customers(self, limit: int = 10, email: Optional[str] = None) -> List[Dict]:
        """List customers with optional email filter"""
        params = {"limit": min(limit, 100)}
        if email:
            params["email"] = email
        
        result = self._request("GET", "customers", params=params)
        return result.get("data", [])
    
    def get_customer(self, customer_id: str) -> Dict:
        """Get a single customer"""
        return self._request("GET", f"customers/{customer_id}")
    
    def create_customer(self, email: str, name: Optional[str] = None,
                        description: Optional[str] = None, **metadata) -> Dict:
        """Create a new customer"""
        payload = {"email": email}
        if name:
            payload["name"] = name
        if description:
            payload["description"] = description
        if metadata:
            payload["metadata"] = metadata
        
        return self._request("POST", "customers", json=payload)
    
    # ===== PAYMENT INTENTS =====
    
    def create_payment_intent(self, amount: int, currency: str = "eur",
                              customer: Optional[str] = None,
                              automatic_payment_methods: bool = True) -> Dict:
        """Create a payment intent
        
        Args:
            amount: Amount in smallest currency unit (e.g., cents)
            currency: ISO currency code (default: eur)
        """
        payload = {
            "amount": amount,
            "currency": currency,
            "automatic_payment_methods[enabled]": automatic_payment_methods
        }
        if customer:
            payload["customer"] = customer
        
        return self._request("POST", "payment_intents", json=payload)
    
    def get_payment_intent(self, payment_intent_id: str) -> Dict:
        """Get a payment intent"""
        return self._request("GET", f"payment_intents/{payment_intent_id}")
    
    def list_payment_intents(self, limit: int = 10, customer: Optional[str] = None) -> List[Dict]:
        """List payment intents"""
        params = {"limit": min(limit, 100)}
        if customer:
            params["customer"] = customer
        
        result = self._request("GET", "payment_intents", params=params)
        return result.get("data", [])
    
    # ===== SUBSCRIPTIONS =====
    
    def create_subscription(self, customer_id: str, price_id: str,
                           payment_behavior: str = "default_incomplete") -> Dict:
        """Create a subscription"""
        payload = {
            "customer": customer_id,
            "items[0][price]": price_id,
            "payment_behavior": payment_behavior,
            "expand[]": "latest_invoice.payment_intent"
        }
        return self._request("POST", "subscriptions", json=payload)
    
    def get_subscription(self, subscription_id: str) -> Dict:
        """Get a subscription"""
        return self._request("GET", f"subscriptions/{subscription_id}")
    
    def list_subscriptions(self, customer: Optional[str] = None,
                          status: Optional[str] = None) -> List[Dict]:
        """List subscriptions"""
        params = {}
        if customer:
            params["customer"] = customer
        if status:
            params["status"] = status
        
        result = self._request("GET", "subscriptions", params=params)
        return result.get("data", [])
    
    def cancel_subscription(self, subscription_id: str, 
                           cancel_at_period_end: bool = True) -> Dict:
        """Cancel a subscription"""
        if cancel_at_period_end:
            return self._request("POST", f"subscriptions/{subscription_id}",
                               json={"cancel_at_period_end": True})
        else:
            return self._request("DELETE", f"subscriptions/{subscription_id}")
    
    # ===== INVOICES =====
    
    def list_invoices(self, limit: int = 10, customer: Optional[str] = None,
                     status: Optional[str] = None) -> List[Dict]:
        """List invoices"""
        params = {"limit": min(limit, 100)}
        if customer:
            params["customer"] = customer
        if status:
            params["status"] = status
        
        result = self._request("GET", "invoices", params=params)
        return result.get("data", [])
    
    def get_invoice(self, invoice_id: str) -> Dict:
        """Get an invoice"""
        return self._request("GET", f"invoices/{invoice_id}")
    
    def create_invoice(self, customer_id: str, auto_advance: bool = True) -> Dict:
        """Create a draft invoice"""
        payload = {
            "customer": customer_id,
            "auto_advance": auto_advance
        }
        return self._request("POST", "invoices", json=payload)
    
    def finalize_invoice(self, invoice_id: str) -> Dict:
        """Finalize a draft invoice"""
        return self._request("POST", f"invoices/{invoice_id}/finalize")
    
    def pay_invoice(self, invoice_id: str) -> Dict:
        """Pay an invoice"""
        return self._request("POST", f"invoices/{invoice_id}/pay")
    
    # ===== WEBHOOKS =====
    
    def verify_webhook(self, payload: bytes, sig_header: str) -> Dict:
        """Verify webhook signature"""
        if not self.config.webhook_secret:
            raise ValueError("Webhook secret not configured")
        
        try:
            # Extract timestamp and signature
            elements = sig_header.split(",")
            sig_dict = {}
            for elem in elements:
                k, v = elem.split("=")
                sig_dict[k.strip()] = v.strip()
            
            timestamp = sig_dict.get("t")
            signature = sig_dict.get("v1")
            
            # Create signed payload
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_sig = hmac.new(
                self.config.webhook_secret.encode(),
                signed_payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(expected_sig, signature):
                raise ValueError("Invalid signature")
            
            return json.loads(payload)
        except Exception as e:
            raise ValueError(f"Webhook verification failed: {e}")


class InvoiceSync:
    """Sync Stripe invoices to accounting systems"""
    
    def __init__(self, client: StripeClient):
        self.client = client
    
    def get_invoices_for_period(self, days: int = 30) -> List[Dict]:
        """Get invoices created in the last N days"""
        since = int((datetime.now() - timedelta(days=days)).timestamp())
        
        invoices = []
        has_more = True
        starting_after = None
        
        while has_more and len(invoices) < 1000:
            params = {
                "limit": 100,
                "created[gte]": since
            }
            if starting_after:
                params["starting_after"] = starting_after
            
            result = self.client._request("GET", "invoices", params=params)
            batch = result.get("data", [])
            invoices.extend(batch)
            
            has_more = result.get("has_more", False)
            if batch:
                starting_after = batch[-1]["id"]
        
        return invoices
    
    def format_for_sevdesk(self, invoice: Dict) -> Dict:
        """Format a Stripe invoice for sevDesk"""
        customer = invoice.get("customer", {})
        
        # Get customer details if it's just an ID
        if isinstance(customer, str):
            customer = self.client.get_customer(customer)
        
        # Calculate VAT
        tax_amounts = invoice.get("tax_amounts", [])
        vat_amount = sum(ta.get("amount", 0) for ta in tax_amounts) / 100
        
        # Get line items
        lines = invoice.get("lines", {}).get("data", [])
        line_items = []
        for line in lines:
            line_items.append({
                "description": line.get("description", ""),
                "quantity": line.get("quantity", 1),
                "unit_price": line.get("price", {}).get("unit_amount", 0) / 100,
                "total": line.get("amount", 0) / 100,
            })
        
        return {
            "external_id": invoice["id"],
            "invoice_number": invoice.get("number", ""),
            "customer_email": customer.get("email", ""),
            "customer_name": customer.get("name", ""),
            "amount_total": invoice.get("amount_due", 0) / 100,
            "amount_paid": invoice.get("amount_paid", 0) / 100,
            "vat_amount": vat_amount,
            "currency": invoice.get("currency", "eur").upper(),
            "status": invoice.get("status", ""),
            "line_items": line_items,
            "created_at": datetime.fromtimestamp(invoice["created"]).isoformat(),
            "period_start": datetime.fromtimestamp(
                invoice.get("period_start", invoice["created"])
            ).isoformat() if invoice.get("period_start") else None,
            "period_end": datetime.fromtimestamp(
                invoice.get("period_end", invoice["created"])
            ).isoformat() if invoice.get("period_end") else None,
        }
    
    def generate_monthly_report(self, year: int, month: int) -> Dict:
        """Generate monthly revenue report"""
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())
        
        # Get paid invoices for period
        params = {
            "status": "paid",
            "created[gte]": start_ts,
            "created[lt]": end_ts,
            "limit": 100
        }
        
        result = self.client._request("GET", "invoices", params=params)
        invoices = result.get("data", [])
        
        # Calculate metrics
        total_revenue = sum(inv.get("amount_paid", 0) for inv in invoices) / 100
        total_vat = sum(
            sum(ta.get("amount", 0) for ta in inv.get("tax_amounts", []))
            for inv in invoices
        ) / 100
        
        return {
            "period": f"{year}-{month:02d}",
            "invoice_count": len(invoices),
            "total_revenue": total_revenue,
            "total_vat": total_vat,
            "net_revenue": total_revenue - total_vat,
            "currency": "EUR",
            "invoices": [self.format_for_sevdesk(inv) for inv in invoices[:10]]
        }


def main():
    parser = argparse.ArgumentParser(description="Stripe Integration Prototype")
    parser.add_argument("--api-key", help="Stripe API key (or set STRIPE_API_KEY env)")
    parser.add_argument("--action", required=True,
                       choices=["list_customers", "get_customer", "list_invoices",
                               "list_subscriptions", "sync_invoices", "monthly_report"])
    parser.add_argument("--customer-id", help="Customer ID")
    parser.add_argument("--days", type=int, default=30, help="Days back for sync")
    parser.add_argument("--year", type=int, default=datetime.now().year)
    parser.add_argument("--month", type=int, default=datetime.now().month)
    
    args = parser.parse_args()
    
    # Get credentials
    api_key = args.api_key or os.getenv("STRIPE_API_KEY")
    if not api_key:
        print("❌ Error: Provide --api-key or set STRIPE_API_KEY environment variable")
        sys.exit(1)
    
    config = StripeConfig(api_key=api_key)
    client = StripeClient(config)
    
    # Execute action
    if args.action == "list_customers":
        customers = client.list_customers(limit=10)
        print(f"\n👥 Customers ({len(customers)}):")
        for c in customers:
            print(f"  {c.get('name', 'N/A')} - {c['email']} ({c['id']})")
    
    elif args.action == "get_customer":
        if not args.customer_id:
            print("❌ Error: --customer-id required")
            sys.exit(1)
        customer = client.get_customer(args.customer_id)
        print(json.dumps(customer, indent=2, default=str))
    
    elif args.action == "list_invoices":
        invoices = client.list_invoices(limit=10)
        print(f"\n📄 Invoices ({len(invoices)}):")
        for inv in invoices:
            print(f"  #{inv.get('number', 'N/A')} - {inv['customer_email']} - €{inv['amount_due']/100}")
    
    elif args.action == "list_subscriptions":
        subs = client.list_subscriptions()
        print(f"\n🔄 Subscriptions ({len(subs)}):")
        for s in subs:
            print(f"  {s['id']} - Status: {s['status']} - Current period ends: {datetime.fromtimestamp(s['current_period_end'])}")
    
    elif args.action == "sync_invoices":
        sync = InvoiceSync(client)
        invoices = sync.get_invoices_for_period(days=args.days)
        print(f"\n📊 Found {len(invoices)} invoices in last {args.days} days")
        
        for inv in invoices[:5]:
            formatted = sync.format_for_sevdesk(inv)
            print(f"\n  #{formatted['invoice_number']}")
            print(f"    Customer: {formatted['customer_email']}")
            print(f"    Total: €{formatted['amount_total']}")
    
    elif args.action == "monthly_report":
        sync = InvoiceSync(client)
        report = sync.generate_monthly_report(args.year, args.month)
        print(f"\n📈 Monthly Report: {report['period']}")
        print(f"  Invoices: {report['invoice_count']}")
        print(f"  Total Revenue: €{report['total_revenue']:.2f}")
        print(f"  Total VAT: €{report['total_vat']:.2f}")
        print(f"  Net Revenue: €{report['net_revenue']:.2f}")


if __name__ == "__main__":
    main()
