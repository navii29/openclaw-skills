#!/usr/bin/env python3
"""
Tests für DATEV-CSV-Export
"""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from datev_export import DATEVExporter, Buchungssatz, validate_datev_csv


def test_datum_normalisierung():
    """Test: Datumsformat-Konvertierung"""
    test_cases = [
        ("150224", "150224"),  # Bereits korrekt
        ("15.02.2024", "150224"),
        ("15.02.24", "150224"),
        ("2024-02-15", "150224"),
        ("15/02/2024", "150224"),
    ]
    
    for input_datum, expected in test_cases:
        b = Buchungssatz(
            datum=input_datum,
            konto=8400,
            gegenkonto=1200,
            bu_schluessel="",
            umsatz=100.00,
            soll_haben="H"
        )
        assert b.datum == expected, f"Erwartet {expected}, erhalten {b.datum}"
    
    print("✅ Datums-Normalisierung-Tests bestanden")
    return True


def test_buchungssatz_validierung():
    """Test: Validierung von Buchungssätzen"""
    
    # Gültiger Buchungssatz
    try:
        b = Buchungssatz(
            datum="15.02.2024",
            konto=8400,
            gegenkonto=1200,
            bu_schluessel="",
            umsatz=1000.00,
            soll_haben="H",
            buchungstext="Test"
        )
        assert b.soll_haben == "H"
        assert isinstance(b.umsatz, Decimal)
    except Exception as e:
        raise AssertionError(f"Gültiger Satz sollte nicht fehlschlagen: {e}")
    
    # Ungültiges Soll/Haben
    try:
        b = Buchungssatz(
            datum="15.02.2024",
            konto=8400,
            gegenkonto=1200,
            bu_schluessel="",
            umsatz=100.00,
            soll_haben="X"  # Ungültig
        )
        raise AssertionError("Sollte ValueError werfen")
    except ValueError:
        pass  # Erwartet
    
    print("✅ Buchungssatz-Validierungs-Tests bestanden")
    return True


def test_exporter_kontenrahmen():
    """Test: SKR03 und SKR04 Kontenrahmen"""
    
    exporter_skr03 = DATEVExporter(kontenrahmen="SKR03")
    assert exporter_skr03.kontenrahmen == "SKR03"
    assert 8400 in exporter_skr03.konten  # Erlöse 19%
    assert 1576 in exporter_skr03.konten  # Vorsteuer 19%
    
    exporter_skr04 = DATEVExporter(kontenrahmen="SKR04")
    assert exporter_skr04.kontenrahmen == "SKR04"
    assert 4400 in exporter_skr04.konten  # Erlöse 19%
    assert 1401 in exporter_skr04.konten  # Vorsteuer 19%
    
    # Ungültiger Kontenrahmen
    try:
        DATEVExporter(kontenrahmen="SKR99")
        raise AssertionError("Sollte ValueError werfen")
    except ValueError:
        pass
    
    print("✅ Kontenrahmen-Tests bestanden")
    return True


def test_rechnung_buchung():
    """Test: Automatische Rechnungsbuchung mit USt"""
    
    exporter = DATEVExporter(kontenrahmen="SKR03")
    
    # Eingangsrechnung: 119€ brutto, 19% USt
    exporter.add_rechnung(
        datum="15.02.2024",
        brutto=119.00,
        ust_satz=19,
        konto=7020,  # Bezogene Waren
        gegenkonto=1600,  # Verbindlichkeiten
        text="Einkauf",
        ist_eingangsrechnung=True
    )
    
    # Sollte 2 Buchungen erzeugen:
    # 1. 7020 (Soll) an 1600 (Haben): 100,00€
    # 2. 1576 (Soll) an 1600 (Haben): 19,00€
    assert len(exporter.buchungen) == 2
    
    # Prüfe erste Buchung (Netto)
    b1 = exporter.buchungen[0]
    assert b1.konto == 7020
    assert b1.gegenkonto == 1600
    assert b1.umsatz == Decimal("100.00")
    
    # Prüfe zweite Buchung (Vorsteuer)
    b2 = exporter.buchungen[1]
    assert b2.konto == 1576  # Vorsteuer 19%
    assert b2.gegenkonto == 1600
    assert b2.umsatz == Decimal("19.00")
    
    print("✅ Rechnungsbuchungs-Tests bestanden")
    return True


def test_csv_export():
    """Test: CSV-Export und Formatierung"""
    import tempfile
    import csv
    
    exporter = DATEVExporter(kontenrahmen="SKR03")
    exporter.add_buchung(Buchungssatz(
        datum="15.02.2024",
        konto=8400,
        gegenkonto=1400,
        bu_schluessel="",
        umsatz=Decimal("1234.56"),
        soll_haben="H",
        buchungstext="Test Verkauf",
        belegnummer="RE-001"
    ))
    
    # Exportiere zu temporärer Datei
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig', newline='') as f:
        temp_path = f.name
    
    try:
        exporter.export(temp_path)
        
        # Lese und prüfe
        with open(temp_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
            
            assert len(rows) == 1
            row = rows[0]
            assert row['Datum'] == '150224'
            assert row['Konto'] == '8400'
            assert row['Gegenkonto'] == '1400'
            assert row['Umsatz (ohne Soll/Haben-Kz)'] == '1234,56'  # Komma als Dezimal!
            assert row['Soll/Haben-Kennzeichen'] == 'H'
            assert row['Belegfeld 1'] == 'RE-001'
    finally:
        Path(temp_path).unlink(missing_ok=True)
    
    print("✅ CSV-Export-Tests bestanden")
    return True


def test_csv_validierung():
    """Test: CSV-Validierung"""
    import tempfile
    
    # Erstelle fehlerhafte CSV
    csv_content = """Datum;Konto;Gegenkonto;BU-Schlüssel;Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;Währung;Buchungstext;Belegfeld 1
150224;8400;1400;;1000,00;H;EUR;Test;RE-001
INVALID;8400;1400;;1000,00;H;EUR;Test;RE-002
150224;8400;1400;;1000,00;X;EUR;Test;RE-003
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig', newline='') as f:
        f.write(csv_content)
        temp_path = f.name
    
    try:
        errors = validate_datev_csv(temp_path)
        assert len(errors) == 2  # Ungültiges Datum, ungültiges S/H
        assert any("Ungültiges Datum" in e for e in errors)
        assert any("Ungültiges Soll/Haben" in e for e in errors)
    finally:
        Path(temp_path).unlink(missing_ok=True)
    
    print("✅ CSV-Validierungs-Tests bestanden")
    return True


def test_json_roundtrip():
    """Test: JSON Export/Import"""
    import tempfile
    import json
    
    exporter = DATEVExporter(kontenrahmen="SKR03")
    exporter.add_buchung(Buchungssatz(
        datum="15.02.2024",
        konto=8400,
        gegenkonto=1400,
        bu_schluessel="",
        umsatz=1000.00,
        soll_haben="H"
    ))
    
    # JSON Export
    json_str = exporter.to_json()
    data = json.loads(json_str)
    assert len(data) == 1
    assert data[0]['konto'] == 8400
    
    # JSON Import
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        f.write(json_str)
        temp_path = f.name
    
    try:
        exporter2 = DATEVExporter(kontenrahmen="SKR03")
        exporter2.load_json(temp_path)
        assert len(exporter2.buchungen) == 1
        assert exporter2.buchungen[0].konto == 8400
    finally:
        Path(temp_path).unlink(missing_ok=True)
    
    print("✅ JSON-Roundtrip-Tests bestanden")
    return True


def run_all_tests():
    """Führt alle Tests aus"""
    print("🧪 Starte DATEV-Export Tests...\n")
    
    tests = [
        test_datum_normalisierung,
        test_buchungssatz_validierung,
        test_exporter_kontenrahmen,
        test_rechnung_buchung,
        test_csv_export,
        test_csv_validierung,
        test_json_roundtrip,
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
