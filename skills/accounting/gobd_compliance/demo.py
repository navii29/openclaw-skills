#!/usr/bin/env python3
"""
Demo-Skript für GoBD Compliance Checker
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gobd_checker import (
    Rechnung, Rechnungsposition, GoBDChecker, ChronologiePruefer, quick_check
)


def demo_gueltige_rechnung():
    """Demo: Vollständige GoBD-konforme Rechnung"""
    print("=" * 60)
    print("DEMO 1: Vollständige GoBD-konforme Rechnung")
    print("=" * 60)
    
    checker = GoBDChecker()
    
    rechnung = Rechnung(
        rechnungsnr="RE-2024-001",
        ausstellungsdatum="2024-01-15",
        lieferdatum="2024-01-10",
        steller_name="Muster GmbH",
        steller_anschrift="Musterstraße 1, 20095 Hamburg",
        steller_ustid="DE123456789",
        empfaenger_name="Kunde AG",
        empfaenger_anschrift="Kundenweg 42, 10115 Berlin",
        positionen=[
            Rechnungsposition("Beratung", 10, 100.00, 19),
            Rechnungsposition("Reisekosten", 1, 150.00, 19),
        ]
    )
    
    ergebnis = checker.pruefe_rechnung(rechnung)
    
    print(f"✅ GoBD-konform: {ergebnis.ist_konform}")
    print(f"   Rechnungsnummer: {rechnung.rechnungsnr}")
    print(f"   Netto: {rechnung.netto_gesamt:.2f} EUR")
    print(f"   USt: {rechnung.ust_gesamt:.2f} EUR")
    print(f"   Brutto: {rechnung.brutto_gesamt:.2f} EUR")
    print(f"   Hash: {ergebnis.hash[:40]}...")
    print()


def demo_mangelhafte_rechnung():
    """Demo: Rechnung mit GoBD-Mängeln"""
    print("=" * 60)
    print("DEMO 2: Rechnung mit GoBD-Mängeln")
    print("=" * 60)
    
    checker = GoBDChecker()
    
    rechnung = Rechnung(
        rechnungsnr="",  # Fehlend!
        ausstellungsdatum="2024-02-05",
        lieferdatum="",
        steller_name="",  # Fehlend!
        steller_anschrift="Unbekannt",
        empfaenger_name="Kunde AG",
        empfaenger_anschrift="Berlin",
        positionen=[
            Rechnungsposition("", 1, 500.00, 19),  # Keine Bezeichnung!
        ]
    )
    
    ergebnis = checker.pruefe_rechnung(rechnung)
    
    print(f"❌ GoBD-konform: {ergebnis.ist_konform}")
    print()
    print("Gefundene Mängel:")
    for mangel in ergebnis.mangel:
        print(f"   • {mangel}")
    print()


def demo_chronologie():
    """Demo: Chronologische Rechnungsnummern prüfen"""
    print("=" * 60)
    print("DEMO 3: Chronologische Rechnungsnummern")
    print("=" * 60)
    
    pruefer = ChronologiePruefer(prefix="RE-")
    
    # Fortlaufende Nummern
    print("\n1. Fortlaufende Nummern:")
    ergebnis = pruefer.pruefe_fortlaufend(["RE-001", "RE-002", "RE-003", "RE-004"])
    print(f"   ✅ Fortlaufend: {ergebnis['ist_fortlaufend']}")
    
    # Lücke erkennen
    print("\n2. Mit Lücke:")
    ergebnis = pruefer.pruefe_fortlaufend(["RE-001", "RE-002", "RE-004"])
    print(f"   ❌ Fortlaufend: {ergebnis['ist_fortlaufend']}")
    print(f"   Fehlende Nummern: {ergebnis['luecken']}")
    
    # Doppelte erkennen
    print("\n3. Mit Doppelter:")
    ergebnis = pruefer.pruefe_fortlaufend(["RE-001", "RE-002", "RE-002", "RE-003"])
    print(f"   ❌ Fortlaufend: {ergebnis['ist_fortlaufend']}")
    print(f"   Doppelte: {ergebnis['doppelte']}")
    
    # Nächste Nummer vorschlagen
    print("\n4. Nächste Nummer vorschlagen:")
    vorschlag = pruefer.generiere_vorschlag("RE-042")
    print(f"   Nach RE-042 kommt: {vorschlag}")
    print()


def demo_hash_unveraenderbarkeit():
    """Demo: Hash für Unveränderbarkeit"""
    print("=" * 60)
    print("DEMO 4: Unveränderbarkeit (Hash)")
    print("=" * 60)
    
    checker = GoBDChecker()
    
    rechnung = Rechnung(
        rechnungsnr="RE-2024-099",
        ausstellungsdatum="2024-01-15",
        lieferdatum="2024-01-10",
        steller_name="Muster GmbH",
        steller_anschrift="Musterstraße 1",
        steller_ustid="DE123456789",
        empfaenger_name="Kunde AG",
        empfaenger_anschrift="Kundenweg 42",
        positionen=[
            Rechnungsposition("Software", 1, 5000.00, 19),
        ]
    )
    
    # Original-Hash
    hash1 = checker.berechne_hash(rechnung)
    print(f"Original-Hash: {hash1[:50]}...")
    
    # Verifizieren
    gueltig = checker.verifiziere_hash(rechnung, hash1)
    print(f"Hash verifiziert: {gueltig}")
    
    # Rechnung ändern
    rechnung.steller_name = "Geänderter Name"
    
    # Neuer Hash
    hash2 = checker.berechne_hash(rechnung)
    print(f"Neuer Hash: {hash2[:50]}...")
    
    # Verifizierung mit altem Hash schlägt fehl
    gueltig = checker.verifiziere_hash(rechnung, hash1)
    print(f"Alter Hash verifiziert: {gueltig} (Änderung erkannt!)")
    print()


def demo_batch_pruefung():
    """Demo: Batch-Prüfung mehrerer Rechnungen"""
    print("=" * 60)
    print("DEMO 5: Batch-Prüfung")
    print("=" * 60)
    
    checker = GoBDChecker()
    
    rechnungen = [
        Rechnung(
            rechnungsnr="RE-001",
            ausstellungsdatum="2024-01-15",
            lieferdatum="2024-01-10",
            steller_name="Muster GmbH",
            steller_anschrift="Musterstraße 1",
            steller_ustid="DE123456789",
            empfaenger_name="Kunde AG",
            empfaenger_anschrift="Berlin",
            positionen=[Rechnungsposition("Beratung", 1, 100, 19)],
        ),
        Rechnung(
            rechnungsnr="RE-002",
            ausstellungsdatum="2024-01-20",
            lieferdatum="2024-01-15",
            steller_name="",  # Fehler!
            steller_anschrift="Musterstraße 1",
            empfaenger_name="Kunde AG",
            empfaenger_anschrift="Berlin",
            positionen=[Rechnungsposition("Service", 1, 200, 19)],
        ),
        Rechnung(
            rechnungsnr="RE-003",
            ausstellungsdatum="2024-01-25",
            lieferdatum="2024-01-20",
            steller_name="Bäckerei Müller",
            steller_anschrift="Brotweg 5",
            steller_steuernummer="1234567890123",
            empfaenger_name="Kunde AG",
            empfaenger_anschrift="Berlin",
            positionen=[Rechnungsposition("Brötchen", 10, 0.50, 7)],
        ),
    ]
    
    ergebnis = checker.pruefe_batch(rechnungen)
    
    print(f"Geprüfte Rechnungen: {ergebnis['gesamt']}")
    print(f"✅ GoBD-konform: {ergebnis['konform']}")
    print(f"❌ Nicht konform: {ergebnis['nicht_konform']}")
    print(f"Konformitätsrate: {ergebnis['konformitaetsrate']*100:.0f}%")
    print()


def demo_bericht():
    """Demo: Ausführlicher Bericht"""
    print("=" * 60)
    print("DEMO 6: Ausführlicher Prüfbericht")
    print("=" * 60)
    
    checker = GoBDChecker()
    
    rechnung = Rechnung(
        rechnungsnr="RE-2024-050",
        ausstellungsdatum="2024-02-15",
        lieferdatum="2024-02-10",
        steller_name="Muster GmbH",
        steller_anschrift="Musterstraße 1, 20095 Hamburg",
        steller_ustid="DE123456789",
        empfaenger_name="Kunde AG",
        empfaenger_anschrift="Kundenweg 42, 10115 Berlin",
        positionen=[
            Rechnungsposition("Software-Lizenz", 1, 5000.00, 19),
            Rechnungsposition("Support", 12, 100.00, 19),
        ]
    )
    
    ergebnis = checker.pruefe_rechnung(rechnung)
    bericht = checker.generiere_bericht(ergebnis, rechnung)
    
    print(bericht)


def demo_quick_check():
    """Demo: Schnelle Prüfung mit Dictionary"""
    print("=" * 60)
    print("DEMO 7: Quick-Check (Dictionary)")
    print("=" * 60)
    
    rechnung_dict = {
        'rechnungsnr': 'RE-QUICK-001',
        'ausstellungsdatum': '2024-03-01',
        'lieferdatum': '2024-02-25',
        'steller_name': 'Quick GmbH',
        'steller_anschrift': 'Schnellstraße 1',
        'steller_ustid': 'DE123456789',
        'empfaenger_name': 'Kunde AG',
        'empfaenger_anschrift': 'Berlin',
        'positionen': [
            {'bezeichnung': 'Dienstleistung', 'menge': 5, 'preis': 200, 'steuersatz': 19},
        ],
    }
    
    ergebnis = quick_check(rechnung_dict)
    
    print(f"Schnellprüfung Ergebnis:")
    print(f"   GoBD-konform: {ergebnis.ist_konform}")
    print(f"   Geprüfte Pflichtangaben: {len(ergebnis.pflichtangaben)}")
    print(f"   Hash: {ergebnis.hash[:40]}...")
    print()


if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " GoBD Compliance Checker - Demos ".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        demo_gueltige_rechnung()
        demo_mangelhafte_rechnung()
        demo_chronologie()
        demo_hash_unveraenderbarkeit()
        demo_batch_pruefung()
        demo_bericht()
        demo_quick_check()
        
        print("=" * 60)
        print("✅ ALLE DEMOS ERFOLGREICH!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
