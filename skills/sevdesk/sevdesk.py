#!/usr/bin/env python3
"""
SevDesk Skill - German Accounting Automation
Handles invoices, contacts, vouchers, and banking via SevDesk API
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

# API Configuration
BASE_URL = "https://my.sevdesk.de/api/v1"
API_TOKEN = os.environ.get("SEVDESK_API_TOKEN", "")

class SevDeskClient:
    """Client for SevDesk API interactions"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or API_TOKEN
        if not self.token:
            raise ValueError("SevDesk API token required. Set SEVDESK_API_TOKEN environment variable.")
        self.headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """Make API request to SevDesk"""
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                return {"error": "Invalid API token. Check your SEVDESK_API_TOKEN."}
            elif response.status_code == 404:
                return {"error": f"Resource not found: {endpoint}"}
            else:
                return {"error": f"API Error {response.status_code}: {str(e)}"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    # ==================== CONTACTS ====================
    
    def list_contacts(self, search: Optional[str] = None, limit: int = 100) -> Dict:
        """List all contacts (customers/suppliers)"""
        params = {"limit": limit}
        if search:
            params["name"] = search
        return self._request("GET", "/Contact", params=params)
    
    def get_contact(self, contact_id: str) -> Dict:
        """Get specific contact details"""
        return self._request("GET", f"/Contact/{contact_id}")
    
    def create_contact(self, name: str, email: Optional[str] = None, 
                       phone: Optional[str] = None, address: Optional[Dict] = None) -> Dict:
        """Create a new contact"""
        data = {
            "name": name,
            "category": {"id": 3, "objectName": "Category"}  # 3 = Customer
        }
        if email:
            data["email"] = email
        if phone:
            data["phone"] = phone
        if address:
            data["addresses"] = [address]
        
        return self._request("POST", "/Contact", data=data)
    
    # ==================== INVOICES ====================
    
    def list_invoices(self, status: Optional[str] = None, limit: int = 100) -> Dict:
        """List invoices with optional status filter"""
        params = {"limit": limit}
        if status:
            params["status"] = status  # 100=draft, 200=open, 1000=paid
        return self._request("GET", "/Invoice", params=params)
    
    def get_invoice(self, invoice_id: str) -> Dict:
        """Get specific invoice details"""
        return self._request("GET", f"/Invoice/{invoice_id}", params={"embed": "contact,invoicePos"})
    
    def create_invoice(self, contact_id: str, items: List[Dict], 
                       invoice_type: str = "RE", due_date_days: int = 14) -> Dict:
        """Create a new invoice
        
        Args:
            contact_id: SevDesk contact ID
            items: List of {"name": str, "quantity": int, "price": float, "tax_rate": float}
            invoice_type: RE=Invoice, AR=Advance, TR=Partial, ER=Final
            due_date_days: Days until invoice is due
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
                "status": 100,  # Draft
                "invoiceType": invoice_type,
                "currency": "EUR",
                "mapAll": True
            },
            "invoicePosSave": invoice_pos,
            "invoicePosDelete": []
        }
        
        return self._request("POST", "/Invoice/Factory/saveInvoice", data=data)
    
    def send_invoice_email(self, invoice_id: str, email: Optional[str] = None) -> Dict:
        """Send invoice via email"""
        data = {"invoiceId": invoice_id}
        if email:
            data["email"] = email
        return self._request("POST", f"/Invoice/{invoice_id}/sendViaEmail", data=data)
    
    def get_unpaid_invoices(self, days_overdue: Optional[int] = None) -> List[Dict]:
        """Get all unpaid (open) invoices"""
        result = self.list_invoices(status="200")  # 200 = Open/Overdue
        invoices = result.get("objects", [])
        
        if days_overdue:
            cutoff = datetime.now() - timedelta(days=days_overdue)
            invoices = [inv for inv in invoices 
                       if datetime.strptime(inv.get("deliveryDate", "2025-01-01"), "%Y-%m-%d") < cutoff]
        
        return invoices
    
    # ==================== VOUCHERS ====================
    
    def list_vouchers(self, limit: int = 100) -> Dict:
        """List expense vouchers"""
        return self._request("GET", "/Voucher", params={"limit": limit})
    
    def create_voucher(self, supplier_id: str, amount: float, description: str,
                       tax_rate: float = 19.0, voucher_date: Optional[str] = None) -> Dict:
        """Create a new expense voucher"""
        if not voucher_date:
            voucher_date = datetime.now().strftime("%Y-%m-%d")
        
        data = {
            "voucher": {
                "supplier": {"id": supplier_id, "objectName": "Contact"},
                "voucherDate": voucher_date,
                "description": description,
                "status": 100,  # Draft
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
        
        # Get first account if none specified
        accounts = self.list_bank_accounts()
        if accounts.get("objects"):
            return accounts["objects"][0]
        return {"error": "No bank accounts found"}
    
    def list_transactions(self, account_id: Optional[str] = None, limit: int = 100) -> Dict:
        """List bank transactions"""
        params = {"limit": limit}
        if account_id:
            params["checkAccount"] = account_id
        return self._request("GET", "/CheckAccountTransaction", params=params)
    
    # ==================== REPORTS ====================
    
    def get_revenue_report(self, start_date: str, end_date: str) -> Dict:
        """Get revenue report for date range"""
        params = {
            "startDate": start_date,
            "endDate": end_date,
            "reportType": "revenue"
        }
        return self._request("GET", "/Report", params=params)


# ==================== CLI INTERFACE ====================

def format_invoice(invoice: Dict) -> str:
    """Format invoice for display"""
    contact = invoice.get("contact", {})
    status_map = {100: "📝 Entwurf", 200: "📤 Gesendet", 1000: "✅ Bezahlt"}
    status = status_map.get(invoice.get("status"), f"Status {invoice.get('status')}")
    
    return f"""
📄 Rechnung {invoice.get('invoiceNumber', '---')}
   Kunde: {contact.get('name', '---')}
   Betrag: {invoice.get('sumNet', 0):.2f} € (Netto)
   Status: {status}
   Datum: {invoice.get('invoiceDate', '---')}
"""

def format_contact(contact: Dict) -> str:
    """Format contact for display"""
    category = {3: "Kunde", 4: "Lieferant"}.get(contact.get("category", {}).get("id"), "Kontakt")
    return f"👤 {contact.get('name')} ({category}) - ID: {contact.get('id')}"

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("""
SevDesk Accounting Skill

Usage: python sevdesk.py <command> [args]

Commands:
  contacts [search]              - List contacts
  contact <id>                   - Get contact details
  invoices [status]              - List invoices (draft/open/paid)
  invoice <id>                   - Get invoice details
  unpaid [days]                  - Show unpaid invoices
  create-invoice <contact_id>    - Create invoice (interactive)
  bank-accounts                  - List bank accounts
  transactions [account_id]      - List bank transactions
  vouchers                       - List vouchers
  help                           - Show this help

Environment:
  SEVDESK_API_TOKEN    - Your SevDesk API token
        """)
        return
    
    command = sys.argv[1]
    
    try:
        client = SevDeskClient()
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    if command == "contacts":
        search = sys.argv[2] if len(sys.argv) > 2 else None
        result = client.list_contacts(search=search)
        contacts = result.get("objects", [])
        print(f"\n📇 {len(contacts)} Kontakte gefunden:\n")
        for c in contacts[:20]:
            print(format_contact(c))
    
    elif command == "contact":
        if len(sys.argv) < 3:
            print("❌ Usage: contact <id>")
            return
        result = client.get_contact(sys.argv[2])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "invoices":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        status_map = {"draft": "100", "open": "200", "paid": "1000"}
        result = client.list_invoices(status=status_map.get(status, status))
        invoices = result.get("objects", [])
        print(f"\n📄 {len(invoices)} Rechnungen:\n")
        for inv in invoices[:20]:
            print(format_invoice(inv))
    
    elif command == "invoice":
        if len(sys.argv) < 3:
            print("❌ Usage: invoice <id>")
            return
        result = client.get_invoice(sys.argv[2])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "unpaid":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else None
        invoices = client.get_unpaid_invoices(days_overdue=days)
        total = sum(inv.get("sumNet", 0) for inv in invoices)
        print(f"\n💰 {len(invoices)} unbezahlte Rechnungen (Gesamt: {total:.2f} €)\n")
        for inv in invoices[:20]:
            print(format_invoice(inv))
    
    elif command == "create-invoice":
        if len(sys.argv) < 3:
            print("❌ Usage: create-invoice <contact_id>")
            return
        # Interactive invoice creation
        print("📝 Neue Rechnung erstellen")
        items = []
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
            result = client.create_invoice(sys.argv[2], items)
            print(f"\n✅ Rechnung erstellt:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("❌ Keine Positionen eingegeben")
    
    elif command == "bank-accounts":
        result = client.list_bank_accounts()
        accounts = result.get("objects", [])
        print(f"\n🏦 {len(accounts)} Bankkonten:\n")
        for acc in accounts:
            print(f"  {acc.get('name')}: {acc.get('balance', 0):.2f} €")
    
    elif command == "transactions":
        account_id = sys.argv[2] if len(sys.argv) > 2 else None
        result = client.list_transactions(account_id=account_id)
        transactions = result.get("objects", [])
        print(f"\n💳 {len(transactions)} Transaktionen:\n")
        for t in transactions[:20]:
            amount = t.get("amount", 0)
            print(f"  {t.get('date')}: {amount:>10.2f} € - {t.get('payeePayerName', '---')[:30]}")
    
    elif command == "vouchers":
        result = client.list_vouchers()
        vouchers = result.get("objects", [])
        print(f"\n🧾 {len(vouchers)} Belege:\n")
        for v in vouchers[:20]:
            print(f"  {v.get('voucherDate')}: {v.get('sumNet', 0):.2f} € - {v.get('description', '---')[:40]}")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run without arguments for help.")

if __name__ == "__main__":
    main()
