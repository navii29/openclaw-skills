#!/usr/bin/env python3
"""
Test-Skript für Lieferschein-Generator
"""

import sys
import os

# Füge das Skill-Verzeichnis zum Path hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lieferschein_generator import LieferscheinGenerator, LieferscheinPosition


def test_basic_generation():
    """Test: Basis-Lieferschein ohne externe Datei"""
    print("\n" + "="*60)
    print("TEST 1: Basis-Lieferschein (Python API)")
    print("="*60)
    
    gen = LieferscheinGenerator()
    
    # Metadaten
    gen.lieferschein_nummer = "LS-TEST-001"
    gen.lieferschein_datum = "26.02.2025"
    gen.lieferdatum = "28.02.2025"
    gen.auftragsnummer = "A-2025-999"
    gen.kundennummer = "K-TEST"
    
    # Absender
    gen.set_absender(
        name="NAVII Automation GmbH",
        strasse="Technologiepark 12",
        plz_ort="10115 Berlin",
        telefon="030 12345678",
        email="info@navii-automation.de",
        steuernr="DE123456789"
    )
    
    # Empfänger
    gen.set_empfaenger(
        name="Test Kunde AG",
        strasse="Teststraße 1",
        plz_ort="20095 Hamburg"
    )
    
    # Positionen
    gen.add_position(LieferscheinPosition(
        artikelnr="ART-001",
        bezeichnung="Testprodukt A",
        menge=2,
        seriennummern=["SN001", "SN002"]
    ))
    
    gen.add_position(LieferscheinPosition(
        artikelnr="ART-002",
        bezeichnung="Testprodukt B",
        menge=5
    ))
    
    # Validierung
    validation = gen.validate()
    print(f"✅ Validierung: {'Erfolgreich' if validation['valid'] else 'Fehlgeschlagen'}")
    if validation['warnings']:
        print(f"   Warnungen: {validation['warnings']}")
    
    # PDF generieren
    output = "/tmp/test_lieferschein_basic.pdf"
    success = gen.generate(output)
    
    if success and os.path.exists(output):
        size = os.path.getsize(output)
        print(f"✅ PDF erstellt: {output} ({size} bytes)")
        return True
    else:
        print("❌ PDF konnte nicht erstellt werden")
        return False


def test_json_import():
    """Test: Lieferschein aus JSON-Datei"""
    print("\n" + "="*60)
    print("TEST 2: Lieferschein aus JSON")
    print("="*60)
    
    gen = LieferscheinGenerator()
    
    # JSON laden
    json_path = os.path.join(os.path.dirname(__file__), "example_lieferschein.json")
    gen.load_from_json(json_path)
    
    print(f"✅ JSON geladen: {len(gen.positionen)} Positionen")
    print(f"   Lieferschein-Nr: {gen.lieferschein_nummer}")
    print(f"   Empfänger: {gen.empfaenger.name if gen.empfaenger else 'N/A'}")
    
    # Validierung
    validation = gen.validate()
    print(f"✅ Validierung: {'Erfolgreich' if validation['valid'] else 'Fehlgeschlagen'}")
    
    # PDF generieren
    output = "/tmp/test_lieferschein_json.pdf"
    success = gen.generate(output)
    
    if success and os.path.exists(output):
        size = os.path.getsize(output)
        print(f"✅ PDF erstellt: {output} ({size} bytes)")
        return True
    else:
        print("❌ PDF konnte nicht erstellt werden")
        return False


def test_with_signature():
    """Test: Lieferschein mit Unterschriftenfeld"""
    print("\n" + "="*60)
    print("TEST 3: Lieferschein mit Unterschrift")
    print("="*60)
    
    gen = LieferscheinGenerator()
    
    # JSON laden
    json_path = os.path.join(os.path.dirname(__file__), "example_lieferschein.json")
    gen.load_from_json(json_path)
    
    # Unterschrift aktivieren
    gen.enable_unterschrift_feld(datum=True, name=True, stempel=True)
    
    # PDF generieren
    output = "/tmp/test_lieferschein_signature.pdf"
    success = gen.generate(output)
    
    if success and os.path.exists(output):
        size = os.path.getsize(output)
        print(f"✅ PDF mit Unterschriftenfeld erstellt: {output} ({size} bytes)")
        return True
    else:
        print("❌ PDF konnte nicht erstellt werden")
        return False


def test_validation_errors():
    """Test: Validierung erkennt Fehler"""
    print("\n" + "="*60)
    print("TEST 4: Validierung (erwartet Fehler)")
    print("="*60)
    
    gen = LieferscheinGenerator()
    
    # Absender ohne Steuernummer
    gen.set_absender(
        name="Test GmbH",
        strasse="Teststraße 1",
        plz_ort="10115 Berlin"
    )
    
    # Keine weiteren Daten → sollte Fehler geben
    validation = gen.validate()
    
    print(f"Validierung gültig: {validation['valid']}")
    print(f"Fehler: {validation['errors']}")
    print(f"Warnungen: {validation['warnings']}")
    
    # Wir erwarten Fehler
    if not validation['valid'] and len(validation['errors']) > 0:
        print("✅ Validierung erkennt Fehler korrekt")
        return True
    else:
        print("❌ Validierung sollte Fehler erkennen")
        return False


def test_cli_mode():
    """Test: CLI-Modus simulieren"""
    print("\n" + "="*60)
    print("TEST 5: CLI-Modus")
    print("="*60)
    
    import subprocess
    
    json_path = os.path.join(os.path.dirname(__file__), "example_lieferschein.json")
    output_path = "/tmp/test_lieferschein_cli.pdf"
    
    # CLI-Aufruf simulieren
    cmd = [
        sys.executable,
        os.path.join(os.path.dirname(__file__), "lieferschein_generator.py"),
        "--input", json_path,
        "--output", output_path,
        "--signature"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"Return Code: {result.returncode}")
    print(f"Stdout:\n{result.stdout}")
    if result.stderr:
        print(f"Stderr:\n{result.stderr}")
    
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"✅ CLI-Modus erfolgreich: {output_path} ({size} bytes)")
        return True
    else:
        print("❌ CLI-Modus fehlgeschlagen")
        return False


def main():
    print("\n" + "="*60)
    print("LIEFERSCHEIN-GENERATOR TESTSUITE")
    print("="*60)
    
    results = []
    
    try:
        results.append(("Basis-Generation", test_basic_generation()))
    except Exception as e:
        print(f"❌ Fehler: {e}")
        results.append(("Basis-Generation", False))
    
    try:
        results.append(("JSON-Import", test_json_import()))
    except Exception as e:
        print(f"❌ Fehler: {e}")
        results.append(("JSON-Import", False))
    
    try:
        results.append(("Unterschrift", test_with_signature()))
    except Exception as e:
        print(f"❌ Fehler: {e}")
        results.append(("Unterschrift", False))
    
    try:
        results.append(("Validierung", test_validation_errors()))
    except Exception as e:
        print(f"❌ Fehler: {e}")
        results.append(("Validierung", False))
    
    try:
        results.append(("CLI-Modus", test_cli_mode()))
    except Exception as e:
        print(f"❌ Fehler: {e}")
        results.append(("CLI-Modus", False))
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nErgebnis: {passed}/{total} Tests bestanden")
    
    if passed == total:
        print("🎉 Alle Tests erfolgreich!")
        return 0
    else:
        print("⚠️ Einige Tests fehlgeschlagen")
        return 1


if __name__ == '__main__':
    sys.exit(main())
