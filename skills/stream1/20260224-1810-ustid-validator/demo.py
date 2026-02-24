#!/usr/bin/env python3
"""
USt-IdNr Validator - Demo
BZSt-offizielle Validierung für deutsche USt-IdNr
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ustid_validator import validate_ustid

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def demo_basic_validation():
    """Demo: Basis-Validierung"""
    print_section("1. Basis-Validierung (Format + Online)")
    
    test_cases = [
        "DE123456789",
        "DE999999999",
        "ATU12345678",
    ]
    
    print("\n📋 Testfälle:\n")
    
    for ustid in test_cases:
        print(f"   Eingabe: {ustid}")
        try:
            result = validate_ustid(ustid)
            status = "✅ GÜLTIG" if result['valid'] else "❌ UNGÜLTIG"
            print(f"   → {status}")
            print(f"   → Status-Code: {result['status']}")
            if result.get('error_message'):
                print(f"   → Meldung: {result['error_message']}")
        except Exception as e:
            print(f"   → ⚠️  Fehler: {e}")
        print()

def demo_qualified_validation():
    """Demo: Qualifizierte Prüfung"""
    print_section("2. Qualifizierte Prüfung (mit Bestätigung)")
    
    print("📋 Mit eigenen Firmendaten:\n")
    print("   validate_ustid(")
    print("       'DE123456789',")  
    print("       eigen_ustid='DE987654321',")
    print("       firma='Muster GmbH',")
    print("       ort='Berlin',")
    print("       plz='10115'")
    print("   )")
    print()
    print("   → Liefert Bestätigung mit Adressabgleich")
    print("   → GoBD-konform dokumentierbar")

def demo_format_check():
    """Demo: Format-Check"""
    print_section("3. EU-Format-Validierung")
    
    formats = [
        ("DE123456789", "Deutschland"),
        ("ATU12345678", "Österreich"),
        ("FR12345678901", "Frankreich"),
        ("NL123456789B01", "Niederlande"),
        ("INVALID", "Ungültig"),
    ]
    
    print("\n🌍 Unterstützte EU-Formate:\n")
    
    for ustid, country in formats:
        print(f"   {country:<15} {ustid:<20}", end="")
        # Nur Format-Check simulieren
        if len(ustid) > 5 and ustid[:2].isalpha():
            print("✅ Format OK")
        else:
            print("❌ Format ungültig")

def demo_integration():
    """Demo: E-Commerce Integration"""
    print_section("4. E-Commerce Workflow")
    
    print("""
   🛒 B2B-Bestellung Workflow:
   
   1. Kunde gibt USt-IdNr ein
      ↓
   2. Automatische Validierung
      ↓
   3. Wenn gültig: Steuerfreie Lieferung
      ↓
   4. Dokumentation in Buchhaltung
   
   💡 Code-Beispiel:
   
   def process_b2b_order(order):
       if order.get('is_business'):
           result = validate_ustid(order['ustid'])
           if result['valid']:
               order['tax_free'] = True
               order['validation_proof'] = result
           else:
               raise ValueError("Ungültige USt-IdNr")
   """)

def demo_status_codes():
    """Demo: BZSt Status-Codes"""
    print_section("5. BZSt Status-Codes")
    
    codes = [
        ("200", "✅ USt-IdNr ist gültig"),
        ("201", "❌ USt-IdNr ist ungültig"),
        ("202", "⚠️  Nicht registriert"),
        ("216", "✅ Gültig (mit Abweichung)"),
        ("217", "✅ Gültig (ohne Abgleich)"),
    ]
    
    print("\n📊 Mögliche Antworten:\n")
    for code, desc in codes:
        print(f"   {code}: {desc}")

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🇩🇪 UST-IDNR VALIDATOR v1.0                            ║
    ║                                                           ║
    ║   BZSt-offizielle Validierung für deutsche Unternehmen   ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    demo_basic_validation()
    demo_qualified_validation()
    demo_format_check()
    demo_integration()
    demo_status_codes()
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   ✅ DEMO ABGESCHLOSSEN                                   ║
    ║                                                           ║
    ║   Preis: 49 EUR (einmalig)                               ║
    ║   Quelle: BZSt (Bundeszentralamt für Steuern)            ║
    ║   Lizenz: MIT                                            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

if __name__ == '__main__':
    main()
