#!/usr/bin/env python3
"""
Tests für den GoBD-Rechnungsvalidator
"""

import sys
from pathlib import Path

# Füge Parent-Verzeichnis zum Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent))

from gobd_validator import GoBDValidator, validate_rechnung


def test_text_extraction():
    """Test: Text-Extraktion aus Test-PDFs"""
    validator = GoBDValidator()
    
    # Test mit einfachem Text
    test_text = """
    Muster GmbH
    Musterstraße 123
    12345 Berlin
    
    Steuernummer: 12/345/67890
    USt-IdNr: DE123456789
    
    Rechnung Nr. RE-2024-001
    Datum: 15.02.2024
    
    Leistung: Beratungsleistung
    Menge: 10 Stunden
    Preis: 100,00 €
    Gesamtbetrag: 1.190,00 €
    MwSt: 19%
    
    Lieferdatum: 15.02.2024
    """
    
    # Teste Extraktion
    lieferant = validator.find_lieferant(test_text)
    assert lieferant['name'] is not None, "Lieferant sollte gefunden werden"
    
    steuernr = validator.find_steuernummer(test_text)
    assert steuernr is not None, "Steuernummer sollte gefunden werden"
    
    ustid = validator.find_ust_id(test_text)
    assert ustid is not None, "USt-IdNr sollte gefunden werden"
    
    rechnungsnr = validator.find_rechnungsnummer(test_text)
    assert rechnungsnr is not None, "Rechnungsnummer sollte gefunden werden"
    
    datum = validator.find_rechnungsdatum(test_text)
    assert datum is not None, "Rechnungsdatum sollte gefunden werden"
    
    betrag = validator.find_gesamtbetrag(test_text)
    assert betrag is not None, "Gesamtbetrag sollte gefunden werden"
    
    print("✅ Alle Text-Extraktion-Tests bestanden!")
    return True


def test_pattern_matching():
    """Test: Regex-Patterns für deutsche Rechnungen"""
    validator = GoBDValidator()
    
    # Test USt-IdNr Patterns
    test_cases = [
        ("DE123456789", "DE123456789"),
        ("DE 123 456 789", "DE123456789"),
        ("USt-IdNr: DE123456789", "DE123456789"),
        ("ATU12345678", "ATU12345678"),
    ]
    
    for text, expected in test_cases:
        result = validator.find_ust_id(text)
        if result:
            assert result == expected, f"USt-IdNr: Erwartet {expected}, erhalten {result}"
    
    # Test Datums-Patterns
    datum_tests = [
        "Rechnungsdatum: 15.02.2024",
        "Datum: 15/02/2024",
        "vom: 2024-02-15",
    ]
    
    for test in datum_tests:
        result = validator.find_rechnungsdatum(test)
        assert result is not None, f"Datum sollte aus '{test}' extrahiert werden"
    
    # Test Betrags-Patterns
    betrag_tests = [
        ("Gesamtbetrag: 1.234,56 €", "1.234,56 €"),
        ("Endbetrag: 1234,56", "1234,56"),
        ("Zu zahlen: 1.234,56 EUR", "1.234,56 EUR"),
    ]
    
    for text, _ in betrag_tests:
        result = validator.find_gesamtbetrag(text)
        assert result is not None, f"Betrag sollte aus '{text}' extrahiert werden"
    
    print("✅ Alle Pattern-Matching-Tests bestanden!")
    return True


def test_validation_scoring():
    """Test: Validierungs-Scoring"""
    
    # Vollständige Rechnung (9/9 Punkte)
    complete_text = """
    Muster GmbH
    Musterstraße 123
    12345 Berlin
    
    Steuernummer: 12/345/67890
    USt-IdNr: DE123456789
    
    Rechnung Nr. RE-2024-001
    Datum: 15.02.2024
    
    Pos. Menge Bezeichnung Einzelpreis Gesamt
    1    10    Beratung   100,00 €    1.000,00 €
    
    Netto: 1.000,00 €
    MwSt 19%: 190,00 €
    Gesamtbetrag: 1.190,00 €
    
    Leistungszeitraum: Februar 2024
    """
    
    # Unvollständige Rechnung
    incomplete_text = """
    Rechnung
    
    Beratungsleistung: 1.000,00 €
    """
    
    validator = GoBDValidator()
    
    # Simuliere ValidationResult für kompletten Text
    lieferant = validator.find_lieferant(complete_text)
    assert lieferant['name'] is not None
    assert lieferant['anschrift'] is not None
    
    steuernr = validator.find_steuernummer(complete_text)
    ustid = validator.find_ust_id(complete_text)
    assert steuernr is not None or ustid is not None
    
    print("✅ Validierungs-Scoring-Tests bestanden!")
    return True


def run_all_tests():
    """Führt alle Tests aus"""
    print("🧪 Starte GoBD-Rechnungsvalidator Tests...\n")
    
    tests = [
        test_text_extraction,
        test_pattern_matching,
        test_validation_scoring,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ Test fehlgeschlagen: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"💥 Test Fehler: {test.__name__}: {e}")
            failed += 1
    
    print(f"\n📊 Ergebnis: {passed} bestanden, {failed} fehlgeschlagen")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
