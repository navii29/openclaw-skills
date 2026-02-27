#!/usr/bin/env python3
"""
Beispiel-Skript für ELSTER USt-Voranmeldung Helper

Dieses Skript zeigt die Verwendung des ELSTER-Generators
mit verschiedenen Szenarien.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from elster_ustva import (
    UStVAGenerator,
    SteuernummerValidator,
    InvalidSteuernummerError,
    quick_voranmeldung,
    batch_create_voranmeldungen,
)


def demo_steuernummer_validierung():
    """Demo: Steuernummer validieren"""
    print("=" * 60)
    print("DEMO 1: Steuernummer-Validierung")
    print("=" * 60)
    
    validator = SteuernummerValidator()
    
    test_nummers = [
        "02 123 45678 901",  # Hamburg (gültig)
        "11 111 22222 333",  # Berlin (gültig)
        "123",               # Zu kurz
        "123456789012345",   # Zu lang
        "9912345678901",     # Ungültiges Bundesland
    ]
    
    for nr in test_nummers:
        try:
            validator.validate_national(nr)
            print(f"✅ GÜLTIG: {nr}")
        except InvalidSteuernummerError as e:
            print(f"❌ UNGÜLTIG: {nr}")
            print(f"   Fehler: {e}")
    
    # USt-IdNr Test
    print("\nUSt-IdNr Tests:")
    ust_ids = ["DE123456789", "de123456789", "123456789", "DE12345678"]
    for ust_id in ust_ids:
        try:
            validator.validate_ust_idnr(ust_id)
            print(f"✅ GÜLTIG: {ust_id}")
        except InvalidSteuernummerError as e:
            print(f"❌ UNGÜLTIG: {ust_id} - {e}")
    print()


def demo_einzel_voranmeldung():
    """Demo: Einzelne Voranmeldung erstellen"""
    print("=" * 60)
    print("DEMO 2: Einzelne USt-Voranmeldung")
    print("=" * 60)
    
    # Generator initialisieren
    generator = UStVAGenerator(
        steuernummer="02 123 45678 901",  # Hamburg-Format (13 Stellen)
        finanzamt="2166",                  # FA Hamburg-Hansa
        name="Muster GmbH"
    )
    
    # Voranmeldung erstellen
    xml = generator.create_voranmeldung(
        jahr=2024,
        monat=1,
        kz81=19000,   # €19.000 USt 19%
        kz86=0,       # Keine 7%
        kz66=8000,    # €8.000 Vorsteuer
        kz63=0        # Keine Berichtigung
    )
    
    print("✅ XML erstellt!")
    print(f"   Steuerpflichtiger: Muster GmbH")
    print(f"   Zeitraum: Januar 2024")
    print(f"   USt 19%: €19.000")
    print(f"   Vorsteuer: €8.000")
    print(f"   Zahllast: €11.000")
    print()
    
    # XML speichern
    output_file = "/tmp/ustva_januar_2024.xml"
    generator.save_to_file(xml, output_file)
    print(f"💾 Gespeichert unter: {output_file}")
    print()
    
    # XML-Vorschau (erste 800 Zeichen)
    print("📄 XML-Vorschau:")
    print("-" * 60)
    print(xml[:800])
    print("...")
    print()


def demo_mit_reduziertem_satz():
    """Demo: Voranmeldung mit 7% USt"""
    print("=" * 60)
    print("DEMO 3: Mit reduziertem Steuersatz (7%)")
    print("=" * 60)
    
    xml = quick_voranmeldung(
        steuernummer="02 123 45678 901",
        finanzamt="2166",
        name="Bäckerei Müller",
        jahr=2024,
        monat=2,
        kz81=5000,    # Normale USt
        kz86=700,     # Reduzierte USt (Lebensmittel)
        kz66=2000     # Vorsteuer
    )
    
    print("✅ Voranmeldung mit Kz 86 (7%) erstellt!")
    print("   Kz 81: €5.000 (19%)")
    print("   Kz 86: €700 (7%)")
    print("   Kz 66: €2.000 (Vorsteuer)")
    print()


def demo_erstattungsfall():
    """Demo: Erstattungsfall"""
    print("=" * 60)
    print("DEMO 4: Erstattungsfall (Vorsteuer > USt)")
    print("=" * 60)
    
    generator = UStVAGenerator(
        steuernummer="02 123 45678 901",
        finanzamt="2166",
        name="Startup GmbH"
    )
    
    xml = generator.create_voranmeldung(
        jahr=2024,
        monat=4,
        kz81=5000,    # Wenig Umsatzsteuer
        kz86=0,
        kz66=12000,   # Viel Vorsteuer (Investitionen)
        kz63=0
    )
    
    print("✅ Erstattungsfall erstellt!")
    print("   USt gesamt: €5.000")
    print("   Vorsteuer: €12.000")
    print("   Erstattung: €7.000")
    print()


def demo_batch():
    """Demo: Batch-Verarbeitung"""
    print("=" * 60)
    print("DEMO 5: Batch-Verarbeitung (Q1 2024)")
    print("=" * 60)
    
    generator = UStVAGenerator(
        steuernummer="02 123 45678 901",
        finanzamt="2166",
        name="Batch Test GmbH"
    )
    
    perioden = [
        {
            'jahr': 2024,
            'monat': 1,
            'kz81': 19000,
            'kz86': 0,
            'kz66': 8000,
            'kz63': 0
        },
        {
            'jahr': 2024,
            'monat': 2,
            'kz81': 22000,
            'kz86': 1400,
            'kz66': 9500,
            'kz63': 0
        },
        {
            'jahr': 2024,
            'monat': 3,
            'kz81': 25000,
            'kz86': 700,
            'kz66': 10000,
            'kz63': 500
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        files = batch_create_voranmeldungen(generator, perioden, tmpdir)
        
        print(f"✅ {len(files)} Dateien erstellt:")
        for f in files:
            print(f"   - {os.path.basename(f)}")
    print()


def demo_alle_kz():
    """Demo: Alle Kennzahlen verwenden"""
    print("=" * 60)
    print("DEMO 6: Alle Kennzahlen (Kz 81, 86, 66, 63)")
    print("=" * 60)
    
    generator = UStVAGenerator(
        steuernummer="02 123 45678 901",
        finanzamt="2166",
        name="Komplett GmbH"
    )
    
    xml = generator.create_voranmeldung(
        jahr=2024,
        monat=6,
        kz81=50000,   # USt 19%
        kz86=3500,    # USt 7%
        kz66=15000,   # Vorsteuer
        kz63=500      # Berichtigung Vorsteuer (z.B. Privatanteil)
    )
    
    print("✅ Voranmeldung mit allen Kz erstellt:")
    print("   Kz 81: €50.000 (USt 19%)")
    print("   Kz 86: €3.500 (USt 7%)")
    print("   Kz 66: €15.000 (Vorsteuer)")
    print("   Kz 63: €500 (Vorsteuerberichtigung)")
    print("   ------------------------")
    print("   USt gesamt: €53.500")
    print("   VSt gesamt: €15.500")
    print("   Zahllast: €38.000")
    print()


import tempfile

if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " ELSTER USt-Voranmeldung Helper - Demos ".center(58) + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        demo_steuernummer_validierung()
        demo_einzel_voranmeldung()
        demo_mit_reduziertem_satz()
        demo_erstattungsfall()
        demo_batch()
        demo_alle_kz()
        
        print("=" * 60)
        print("✅ ALLE DEMOS ERFOLGREICH!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
