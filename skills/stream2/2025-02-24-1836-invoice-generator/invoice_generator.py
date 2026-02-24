#!/usr/bin/env python3
"""
Quick Invoice Generator
Generate invoices from command line.
Markdown export with automatic numbering.
"""

import json
import os
from datetime import datetime, timedelta

INVOICE_DIR = os.path.expanduser("~/.openclaw/workspace/skills/stream2/2025-02-24-1836-invoice-generator")
INVOICES_FILE = os.path.join(INVOICE_DIR, "invoices.json")

def ensure_dir():
    if not os.path.exists(INVOICE_DIR):
        os.makedirs(INVOICE_DIR)

def load_invoices():
    if os.path.exists(INVOICES_FILE):
        with open(INVOICES_FILE) as f:
            return json.load(f)
    return {"invoices": [], "next_number": 1}

def save_invoices(data):
    with open(INVOICES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_invoice_number():
    """Generate next invoice number"""
    data = load_invoices()
    year = datetime.now().strftime('%Y')
    num = data.get('next_number', 1)
    return f"RE-{year}-{num:04d}", num

def create_invoice(client, items, notes="", due_days=14, tax_rate=19):
    """Create new invoice"""
    ensure_dir()
    
    invoice_num, num = generate_invoice_number()
    
    # Calculate totals
    subtotal = sum(item['qty'] * item['price'] for item in items)
    tax = subtotal * (tax_rate / 100)
    total = subtotal + tax
    
    invoice_date = datetime.now().strftime('%Y-%m-%d')
    due_date = (datetime.now() + timedelta(days=due_days)).strftime('%Y-%m-%d')
    
    invoice = {
        'number': invoice_num,
        'seq_number': num,
        'client': client,
        'date': invoice_date,
        'due_date': due_date,
        'items': items,
        'subtotal': round(subtotal, 2),
        'tax_rate': tax_rate,
        'tax': round(tax, 2),
        'total': round(total, 2),
        'notes': notes,
        'status': 'draft',
        'created_at': datetime.now().isoformat()
    }
    
    # Save to registry
    data = load_invoices()
    data['invoices'].append(invoice)
    data['next_number'] = num + 1
    save_invoices(data)
    
    # Generate markdown
    md_file = generate_markdown(invoice)
    
    return invoice, md_file

def generate_markdown(invoice):
    """Generate markdown invoice"""
    filename = f"{invoice['number']}.md"
    filepath = os.path.join(INVOICE_DIR, filename)
    
    md = f"""# RECHNUNG

**Rechnungsnummer:** {invoice['number']}  
**Datum:** {invoice['date']}  
**Fällig bis:** {invoice['due_date']}

---

## Rechnungsempfänger

{invoice['client']}

---

## Leistungen

| Pos. | Beschreibung | Menge | Einzelpreis | Gesamt |
|------|--------------|-------|-------------|--------|
"""
    
    for i, item in enumerate(invoice['items'], 1):
        line_total = item['qty'] * item['price']
        md += f"| {i} | {item['desc']} | {item['qty']} | {item['price']:.2f} € | {line_total:.2f} € |\n"
    
    md += f"""
---

## Zusammenfassung

| | Betrag |
|---|--------|
| Zwischensumme | {invoice['subtotal']:.2f} € |
| MwSt. ({invoice['tax_rate']}%) | {invoice['tax']:.2f} € |
| **Gesamtbetrag** | **{invoice['total']:.2f} €** |

---

## Zahlungsinformationen

Bitte überweisen Sie den Betrag innerhalb von 14 Tagen auf:

Bank: [Ihre Bank]  
IBAN: [Ihre IBAN]  
BIC: [Ihre BIC]

**Verwendungszweck:** {invoice['number']}

---

{invoice['notes']}

---

*Mit freundlichen Grüßen*  
Fridolin Edlmair  
Navii Automation
"""
    
    with open(filepath, 'w') as f:
        f.write(md)
    
    return filepath

def list_invoices(status=None):
    """List all invoices"""
    data = load_invoices()
    invoices = data['invoices']
    
    if status:
        invoices = [i for i in invoices if i['status'] == status]
    
    return invoices

def format_invoice_line(inv):
    """Format invoice for list view"""
    status_emoji = {
        'draft': '📝',
        'sent': '📤',
        'paid': '✅',
        'overdue': '⚠️'
    }.get(inv['status'], '📝')
    
    return f"{status_emoji} {inv['number']} | {inv['date']} | {inv['client'][:20]:20} | {inv['total']:.2f} €"

def generate_report():
    """Generate financial report"""
    data = load_invoices()
    invoices = data['invoices']
    
    total_revenue = sum(i['total'] for i in invoices if i['status'] == 'paid')
    outstanding = sum(i['total'] for i in invoices if i['status'] == 'sent')
    draft_total = sum(i['total'] for i in invoices if i['status'] == 'draft')
    
    report = f"""💰 *FINANZ ÜBERSICHT*

📊 Rechnungen gesamt: {len(invoices)}
💵 Bezahlt: {total_revenue:.2f} €
⏳ Ausstehend: {outstanding:.2f} €
📝 Entwürfe: {draft_total:.2f} €

📈 Umsatz: {total_revenue:.2f} €
"""
    
    return report

def mark_paid(invoice_number):
    """Mark invoice as paid"""
    data = load_invoices()
    
    for inv in data['invoices']:
        if inv['number'] == invoice_number:
            inv['status'] = 'paid'
            inv['paid_at'] = datetime.now().isoformat()
            save_invoices(data)
            return True
    
    return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Quick Invoice Generator')
    parser.add_argument('action', choices=['create', 'list', 'report', 'paid'])
    parser.add_argument('--client', '-c', help='Client name')
    parser.add_argument('--item', '-i', action='append', nargs=3,
                       metavar=('DESC', 'QTY', 'PRICE'),
                       help='Add item (description qty price)')
    parser.add_argument('--number', '-n', help='Invoice number')
    parser.add_argument('--status', '-s', choices=['draft', 'sent', 'paid', 'overdue'])
    parser.add_argument('--notes', help='Invoice notes')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        if args.client and args.item:
            items = []
            for item in args.item:
                items.append({
                    'desc': item[0],
                    'qty': int(item[1]),
                    'price': float(item[2])
                })
            
            invoice, md_file = create_invoice(
                args.client,
                items,
                notes=args.notes or ""
            )
            
            print(f"\n✅ Invoice created!")
            print(f"   Number: {invoice['number']}")
            print(f"   Total: {invoice['total']:.2f} €")
            print(f"   File: {md_file}")
        else:
            print("Usage: invoice_generator.py create --client 'Firma GmbH' -i 'Beratung' 10 150")
    
    elif args.action == 'list':
        invoices = list_invoices(args.status)
        print(f"\n📋 Invoices ({len(invoices)}):\n")
        for inv in invoices:
            print(format_invoice_line(inv))
    
    elif args.action == 'report':
        print(generate_report())
    
    elif args.action == 'paid':
        if args.number:
            if mark_paid(args.number):
                print(f"✅ Invoice {args.number} marked as paid")
            else:
                print(f"❌ Invoice {args.number} not found")
        else:
            print("Usage: invoice_generator.py paid --number RE-2026-0001")
    
    else:
        print("🧾 Quick Invoice Generator")
        print("\nUsage:")
        print("  create --client 'Name' -i 'Service' 5 100")
        print("  list [--status draft]")
        print("  report")
        print("  paid --number RE-2026-0001")
