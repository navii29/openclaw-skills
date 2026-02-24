#!/usr/bin/env python3
"""
SevDesk Skill - Demo Script
Zeigt die wichtigsten Features des SevDesk Buchhaltungs-Skills
"""

import os
import sys

# Add skill to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sevdesk_v2 import SevDeskClient, InvoiceStatus, DunningLevel

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def demo_health_check():
    """Demo: API Health Check"""
    print_section("1. API Health Check")
    
    client = SevDeskClient(enable_cache=False)
    health = client.health_check(timeout=5.0)
    
    if health.healthy:
        print(f"✅ API ist erreichbar")
        print(f"   Response-Zeit: {health.response_time_ms:.1f}ms")
        print(f"   API-Version: {health.api_version or 'unbekannt'}")
    else:
        print(f"❌ API nicht erreichbar: {health.message}")

def demo_contacts():
    """Demo: Kontakte verwalten"""
    print_section("2. Kontakte verwalten")
    
    with SevDeskClient() as client:
        # Kontakte auflisten
        print("📋 Letzte 5 Kontakte:")
        result = client.list_contacts(limit=5)
        
        if 'objects' in result:
            for contact in result['objects'][:5]:
                name = contact.get('name', 'Unbekannt')
                category = contact.get('category', {}).get('name', 'Kunde')
                print(f"   • {name} ({category})")
        
        print("\n💡 Neuen Kontakt erstellen:")
        print("   client.create_contact('Max Mustermann', 'max@example.com')")

def demo_invoices():
    """Demo: Rechnungen verwalten"""
    print_section("3. Rechnungen verwalten")
    
    with SevDeskClient() as client:
        # Offene Rechnungen
        print("📄 Offene Rechnungen:")
        result = client.list_invoices(status='open', limit=5)
        
        if 'objects' in result:
            for inv in result['objects'][:5]:
                number = inv.get('invoiceNumber', '---')
                net = inv.get('sumNet', 0)
                contact = inv.get('contact', {}).get('name', 'Unbekannt')
                print(f"   • {number}: {net:.2f}€ ({contact})")
        
        print("\n💡 Neue Rechnung erstellen:")
        print("""   client.create_invoice(
       contact_id='12345',
       items=[{
           'name': 'Beratung',
           'price': 500.00,
           'quantity': 1,
           'tax_rate': 19.0
       }]
   )""")

def demo_dunning():
    """Demo: Mahnwesen (Dunning)"""
    print_section("4. Mahnwesen (Dunning)")
    
    with SevDeskClient() as client:
        # Überfällige Rechnungen
        print("⚠️  Überfällige Rechnungen (30+ Tage):")
        overdue = client.get_overdue_invoices(days_overdue=30)
        
        if overdue:
            for inv in overdue[:5]:
                print(f"   • {inv['invoiceNumber']}: {inv['sumNet']:.2f}€ "
                      f"({inv['days_overdue']} Tage überfällig)")
        else:
            print("   Keine überfälligen Rechnungen")
        
        # Mahnungs-Summary
        print("\n📊 Mahnungs-Übersicht:")
        summary = client.get_dunning_summary(days_overdue=30)
        print(f"   Gesamt überfällig: {summary['total_overdue']} Rechnungen")
        print(f"   Gesamtbetrag: {summary['total_amount']:.2f}€")
        
        if summary['recommendations']:
            print("\n   Empfohlene Aktionen:")
            for rec in summary['recommendations']:
                print(f"   → {rec['action']}: {rec['count']} Rechnungen")

def demo_export():
    """Demo: CSV Export"""
    print_section("5. CSV Export")
    
    with SevDeskClient() as client:
        print("📤 Kontakte exportieren:")
        print("   client.export_contacts_csv(filename='kontakte.csv')")
        
        print("\n📤 Rechnungen exportieren:")
        print("   client.export_invoices_csv(")
        print("       filename='rechnungen.csv',")
        print("       status='open',")
        print("       start_date='2024-01-01'")
        print("   )")

def demo_stats():
    """Demo: API Statistiken"""
    print_section("6. API Statistiken")
    
    with SevDeskClient() as client:
        stats = client.get_stats()
        print(f"📈 Statistiken:")
        print(f"   Anfragen: {stats.get('request_count', 0)}")
        print(f"   Cache-Treffer: {stats.get('cached_request_count', 0)}")
        print(f"   Circuit Breaker: {stats.get('circuit_state', 'unknown')}")

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🏢 SEVDESK SKILL v2.3.0 - DEMO                          ║
    ║                                                           ║
    ║   Deutsche Buchhaltung: Rechnungen, Kontakte, Mahnungen   ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check for API token
    if not os.environ.get('SEVDESK_API_TOKEN'):
        print("⚠️  HINWEIS: SEVDESK_API_TOKEN nicht gesetzt")
        print("   Setze die Umgebungsvariable für Live-Demo:")
        print("   export SEVDESK_API_TOKEN=dein_token\n")
    
    try:
        demo_health_check()
    except Exception as e:
        print(f"   ⚠️  Health Check nicht möglich: {e}")
    
    try:
        demo_contacts()
    except Exception as e:
        print(f"   ⚠️  Kontakt-Demo nicht möglich: {e}")
    
    try:
        demo_invoices()
    except Exception as e:
        print(f"   ⚠️  Rechnungs-Demo nicht möglich: {e}")
    
    try:
        demo_dunning()
    except Exception as e:
        print(f"   ⚠️  Mahnungs-Demo nicht möglich: {e}")
    
    demo_export()
    
    try:
        demo_stats()
    except Exception as e:
        print(f"   ⚠️  Statistik-Demo nicht möglich: {e}")
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ✅ DEMO ABGESCHLOSSEN                                   ║
    ║                                                           ║
    ║   Weitere Infos: skills/sevdesk/SKILL.md                  ║
    ║   Preis: 299 EUR (einmalig)                               ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

if __name__ == '__main__':
    main()
