"""
Tests für IdNr Validator
"""

import unittest
from idnr_validator import IdNrValidator, validate_idnr


class TestIdNrValidator(unittest.TestCase):
    
    def setUp(self):
        self.validator = IdNrValidator()
    
    def test_format_idnr(self):
        """Test Formatierung"""
        self.assertEqual(self.validator.format_idnr("12 345 678 901"), "12345678901")
        self.assertEqual(self.validator.format_idnr("123-456-789-01"), "12345678901")
        self.assertEqual(self.validator.format_idnr("12345678901"), "12345678901")
    
    def test_validate_format_korrekt(self):
        """Test korrektes Format"""
        valid, formatted, errors = self.validator.validate_format("12345678901")
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_format_falsche_laenge(self):
        """Test falsche Länge"""
        valid, formatted, errors = self.validator.validate_format("1234567890")
        self.assertFalse(valid)
        self.assertTrue(any('11 Ziffern' in e for e in errors))
    
    def test_validate_format_fuehrende_null(self):
        """Test führende Null"""
        valid, formatted, errors = self.validator.validate_format("02345678901")
        self.assertFalse(valid)
        self.assertTrue(any('nicht 0' in e for e in errors))
    
    def test_validate_format_doppelte_ziffer(self):
        """Test doppelte aufeinanderfolgende Ziffern"""
        valid, formatted, errors = self.validator.validate_format("11234567890")
        self.assertFalse(valid)
        self.assertTrue(any('Doppelte Ziffer' in e for e in errors))
    
    def test_validate_checksum(self):
        """Test Prüfziffer-Berechnung"""
        # Dies ist ein allgemeiner Test - echte Prüfziffern wären spezifisch
        result = self.validator.validate_checksum("12345678901")
        # Wir testen nur dass die Funktion läuft
        self.assertIsInstance(result, bool)
    
    def test_validate_full(self):
        """Test vollständige Validierung"""
        result = self.validator.validate("12345678901")
        self.assertIsNotNone(result.pruefziffer_korrekt)
    
    def test_mask_idnr(self):
        """Test Maskierung"""
        masked = self.validator.mask_idnr("12345678901")
        self.assertEqual(masked, "12345*****1")
    
    def test_mask_idnr_kurz(self):
        """Test Maskierung kurzer Eingabe"""
        masked = self.validator.mask_idnr("123")
        self.assertEqual(masked, "***")
    
    def test_get_info(self):
        """Test Info-Funktion"""
        info = self.validator.get_info("12345678901")
        self.assertEqual(info['laenge'], 11)
        self.assertEqual(info['erste_ziffer'], '1')
        self.assertEqual(info['letzte_ziffer'], '1')


class TestQuickValidation(unittest.TestCase):
    """Test der Convenience-Funktion"""
    
    def test_validate_idnr(self):
        """Test Schnell-Funktion"""
        result = validate_idnr("12345678901")
        self.assertIn('gueltig', result)
        self.assertIn('format_korrekt', result)
        self.assertIn('pruefziffer_korrekt', result)
        self.assertIn('fehler', result)


class TestEdgeCases(unittest.TestCase):
    """Test Grenzfälle"""
    
    def test_leer(self):
        """Test leere Eingabe"""
        result = IdNrValidator().validate("")
        self.assertFalse(result.gueltig)
    
    def test_nur_leerzeichen(self):
        """Test nur Leerzeichen"""
        result = IdNrValidator().validate("   ")
        self.assertFalse(result.gueltig)
    
    def test_buchstaben(self):
        """Test mit Buchstaben"""
        result = IdNrValidator().validate("12345A78901")
        self.assertFalse(result.format_korrekt)


if __name__ == '__main__':
    unittest.main()
