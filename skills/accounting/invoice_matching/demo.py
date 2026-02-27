#!/usr/bin/env python3
"""
Demo-Skript für Rechnungs-Matching
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from invoice_matching import InvoiceMatcher, DATEVExporter, quick_match
import json


def demo_exaktes_matching():
    """Demo: Exaktes Matching mit Rechnungsnummer"""
    print("=" * 60)
    print("DEMO 1: Exaktes Matching mit Rechnungsnummer")
    print("=" * 60)
    
    matcher = InvoiceMatcher()
    
    # Rechnungen laden
    matcher.lade_rechnungen([
        {'nr': 'RE-2024-001', 'kunde_id': 'K001', 'betrag': 1190.00, 'datum': '2024-01-05'},
        {'nr': 'RE-2024-002', 'kunde_id': 'K002', 'betrag': 2380.00, 'datum': '2024-01-10'},
    ])
    
    # Zahlungen mit Rechnungsnummer im Verwendungszweck
    matcher.lade_zahlungen([
        {'datum': '2024-01-15', 'betrag': 1190.00, 'zweck': 'Rechnung RE-2024-001'},
        {'datum': '2024-01-20', 'betrag': 2380.00, 'zweck': 'Zahlung fuer RE-2024-002'},
    ])
    
    ergebnis = matcher.match()
    
    print(f"✅ {ergebnis['stats']['gematcht']} von {ergebnis['stats']['total_zahlungen']} Zahlungen gematcht")
    print(f"   Match-Rate: {ergebnis['stats']['match_rate']*100:.0f}%")
    print()
    
    for match in ergebnis['matches']:
        print(f"   {match.zahlung.datum} | {match.zahlung.betrag} EUR → {match.rechnung.nr}")
        print(f"      Methode: {match.methode}, Vertrauen: {match.vertrauen}")
    print()


def demo_fuzzy_matching():
    """Demo: Fuzzy Matching mit Toleranz"""
    print("=" * 60)
    print("DEMO 2: Fuzzy Matching (Betrags-Toleranz)")
    print("=" * 60)
    
    # Mit 1% Toleranz
    ergebnis = quick_match(
        rechnungen=[
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1000.00, 'datum': '2024-01-01'},
            {'nr': 'RE-002', 'kunde_id': 'K002', 'betrag': 2000.00, 'datum': '2024-01-05'},
        ],
        zahlungen=[
            {'datum': '2024-01-10', 'betrag': 1005.00, 'zweck': 'Danke!'},  # +5 EUR = 0.5%
            {'datum': '2024-01-15', 'betrag': 1990.00, 'zweck': 'Rechnung'},  # -10 EUR = 0.5%
        ],
        toleranz_prozent=1.0
    )
    
    print(f"✅ {ergebnis['stats']['gematcht']} Matches mit 1% Toleranz")
    for match in ergebnis['matches']:
        diff = f"(+{match.differenz})" if match.differenz > 0 else f"({match.differenz})"
        print(f"   {match.zahlung.betrag} EUR {diff} → {match.rechnung.nr}")
    print()


def demo_teilzahlung():
    """Demo: Teilzahlungen erkennen"""
    print("=" * 60)
    print("DEMO 3: Teilzahlungen")
    print("=" * 60)
    
    matcher = InvoiceMatcher()
    
    matcher.lade_rechnungen([
        {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 10000.00, 'datum': '2024-01-01'},
    ])
    
    matcher.lade_zahlungen([
        {'datum': '2024-01-10', 'betrag': 3000.00, 'zweck': 'RE-001 Anzahlung'},
        {'datum': '2024-01-20', 'betrag': 4000.00, 'zweck': 'RE-001 Teilzahlung'},
    ])
    
    ergebnis = matcher.match()
    
    print(f"✅ {ergebnis['stats']['gematcht']} Teilzahlungen erkannt")
    
    rechnung = matcher.rechnungen[0]
    print(f"   Rechnung: {rechnung.nr}")
    print(f"   Gesamt: {rechnung.betrag} EUR")
    print(f"   Bezahlt: {rechnung.bezahlt} EUR")
    print(f"   Rest: {rechnung.restbetrag} EUR")
    print(f"   Status: {rechnung.status}")
    print()


def demo_doppelte_zahlung():
    """Demo: Doppelte Zahlungen erkennen"""
    print("=" * 60)
    print("DEMO 4: Doppelte Zahlungen erkennen")
    print("=" * 60)
    
    matcher = InvoiceMatcher()
    
    matcher.lade_rechnungen([
        {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1000.00, 'datum': '2024-01-01'},
    ])
    
    matcher.lade_zahlungen([
        {'datum': '2024-01-10', 'betrag': 1000.00, 'zweck': 'RE-001'},
        {'datum': '2024-01-11', 'betrag': 1000.00, 'zweck': 'RE-001'},  # Doppelt!
    ])
    
    ergebnis = matcher.match()
    
    print(f"⚠️  {ergebnis['stats']['doppelte']} doppelte Zahlung(en) erkannt!")
    for z in ergebnis['doppelte_zahlungen']:
        print(f"   {z.datum} | {z.betrag} EUR | {z.zweck}")
    print()


def demo_datev_export():
    """Demo: DATEV-Export"""
    print("=" * 60)
    print("DEMO 5: DATEV-CSV Export")
    print("=" * 60)
    
    matcher = InvoiceMatcher()
    
    matcher.lade_rechnungen([
        {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1190.00, 'datum': '2024-01-05'},
        {'nr': 'RE-002', 'kunde_id': 'K002', 'betrag': 2380.00, 'datum': '2024-01-10'},
    ])
    
    matcher.lade_zahlungen([
        {'datum': '2024-01-15', 'betrag': 1190.00, 'zweck': 'RE-001'},
        {'datum': '2024-01-20', 'betrag': 2380.00, 'zweck': 'RE-002'},
    ])
    
    ergebnis = matcher.match()
    
    # Export
    exporter = DATEVExporter()
    output_file = "/tmp/datev_export.csv"
    exporter.export_csv(ergebnis, output_file)
    
    print(f"✅ DATEV-CSV exportiert nach: {output_file}")
    print()
    
    with open(output_file, 'r') as f:
        print("📄 Inhalt:")
        print("-" * 40)
        print(f.read())
    print()


def demo_bericht():
    """Demo: Bericht generieren"""
    print("=" * 60)
    print("DEMO 6: Matching-Bericht")
    print("=" * 60)
    
    matcher = InvoiceMatcher()
    
    matcher.lade_rechnungen([
        {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1000.00, 'datum': '2024-01-01'},
        {'nr': 'RE-002', 'kunde_id': 'K002', 'betrag': 2000.00, 'datum': '2024-01-05'},
        {'nr': 'RE-003', 'kunde_id': 'K003', 'betrag': 3000.00, 'datum': '2024-01-10'},
    ])
    
    matcher.lade_zahlungen([
        {'datum': '2024-01-15', 'betrag': 1000.00, 'zweck': 'RE-001'},
        {'datum': '2024-01-20', 'betrag': 2000.00, 'zweck': 'RE-002'},
        {'datum': '2024-01-25', 'betrag': 999.00, 'zweck': 'Unbekannt'},
    ])
    
    matcher.match()
    
    print(matcher.get_bericht())


if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " Rechnungs-Matching - Demos ".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        demo_exaktes_matching()
        demo_fuzzy_matching()
        demo_teilzahlung()
        demo_doppelte_zahlung()
        demo_datev_export()
        demo_bericht()
        
        print("=" * 60)
        print("✅ ALLE DEMOS ERFOLGREICH!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
