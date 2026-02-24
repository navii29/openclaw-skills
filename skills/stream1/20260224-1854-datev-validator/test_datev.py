"""
Tests für DATEV Validator
"""

import unittest
from datev_validator import DATEVValidator, validate_datev


class TestDATEVValidator(unittest.TestCase):
    
    def setUp(self):
        self.validator = DATEVValidator()
    
    def test_validate_csv_gueltig(self):
        """Test gültige CSV"""
        csv_content = """Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;Konto;Gegenkonto (ohne BU-Schlüssel);Belegdatum;Buchungstext
1000,00;S;8400;1200;24022025;Erlöse
"""
        result = self.validator.validate_csv(csv_content)
        self.assertEqual(result.format, 'BUCHUNGSSTAPEL')
        self.assertEqual(result.zeilen_gesamt, 1)
    
    def test_validate_csv_fehlende_pflichtfelder(self):
        """Test CSV mit fehlenden Pflichtfeldern"""
        csv_content = """Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;Konto;Gegenkonto (ohne BU-Schlüssel);Belegdatum;Buchungstext
;;;1200;24022025;Erlöse
"""
        result = self.validator.validate_csv(csv_content)
        self.assertFalse(result.gueltig)
        self.assertGreater(len(result.fehler), 0)
    
    def test_validate_csv_ungueltiges_datum(self):
        """Test CSV mit ungültigem Datum"""
        csv_content = """Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;Konto;Gegenkonto (ohne BU-Schlüssel);Belegdatum;Buchungstext
1000,00;S;8400;1200;24.02.2025;Erlöse
"""
        result = self.validator.validate_csv(csv_content)
        self.assertFalse(result.gueltig)
        self.assertTrue(any('Datumsformat' in f['fehler'] for f in result.fehler))
    
    def test_validate_csv_ungueltige_sh_kz(self):
        """Test CSV mit ungültigem Soll/Haben-Kennzeichen"""
        csv_content = """Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;Konto;Gegenkonto (ohne BU-Schlüssel);Belegdatum;Buchungstext
1000,00;X;8400;1200;24022025;Erlöse
"""
        result = self.validator.validate_csv(csv_content)
        self.assertFalse(result.gueltig)
        self.assertTrue(any('Soll/Haben-Kennzeichen' in f['fehler'] for f in result.fehler))
    
    def test_validate_csv_ungueltiger_umsatz(self):
        """Test CSV mit ungültigem Umsatz"""
        csv_content = """Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;Konto;Gegenkonto (ohne BU-Schlüssel);Belegdatum;Buchungstext
ABC;S;8400;1200;24022025;Erlöse
"""
        result = self.validator.validate_csv(csv_content)
        self.assertFalse(result.gueltig)
        self.assertTrue(any('Umsatz-Format' in f['fehler'] for f in result.fehler))
    
    def test_validate_csv_leer(self):
        """Test leere CSV"""
        csv_content = ""
        result = self.validator.validate_csv(csv_content)
        self.assertFalse(result.gueltig)
    
    def test_validate_konto_gueltig(self):
        """Test gültige Kontonummer"""
        result = self.validator.validate_konto("8400")
        self.assertTrue(result['gueltig'])
    
    def test_validate_konto_zu_lang(self):
        """Test zu lange Kontonummer"""
        result = self.validator.validate_konto("1234567890")
        self.assertFalse(result['gueltig'])
    
    def test_validate_konto_mit_hinweis(self):
        """Test Konto mit Hinweis"""
        result = self.validator.validate_konto("8400")
        self.assertTrue(result['gueltig'])
        self.assertIsNotNone(result.get('hinweis'))
    
    def test_detect_format_buchungsstapel(self):
        """Test Format-Erkennung Buchungsstapel"""
        headers = [
            'Umsatz (ohne Soll/Haben-Kz)',
            'Soll/Haben-Kennzeichen',
            'Konto',
            'Gegenkonto (ohne BU-Schlüssel)',
            'Belegdatum',
            'Buchungstext'
        ]
        format_type = self.validator._detect_format(headers)
        self.assertEqual(format_type, 'BUCHUNGSSTAPEL')
    
    def test_generate_sample_csv(self):
        """Test Beispiel-CSV Generierung"""
        sample = self.validator.generate_sample_csv()
        self.assertIn('Umsatz (ohne Soll/Haben-Kz)', sample)
        self.assertIn('Soll/Haben-Kennzeichen', sample)
        self.assertIn('8400', sample)


class TestQuickValidation(unittest.TestCase):
    """Test Convenience-Funktion"""
    
    def test_validate_datev(self):
        """Test Schnell-Funktion"""
        csv_content = """Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;Konto;Gegenkonto (ohne BU-Schlüssel);Belegdatum;Buchungstext
1000,00;S;8400;1200;24022025;Erlöse
"""
        result = validate_datev(csv_content)
        self.assertIn('gueltig', result)
        self.assertIn('format', result)
        self.assertIn('fehler', result)


if __name__ == '__main__':
    unittest.main()
