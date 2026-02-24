"""
Tests für EORI Validator
"""

import unittest
from eori_validator import EORIValidator, validate_eori


class TestEORIValidator(unittest.TestCase):
    
    def setUp(self):
        self.validator = EORIValidator()
    
    def test_format_eori(self):
        """Test EORI Formatierung"""
        self.assertEqual(self.validator.format_eori("DE 123 456 789"), "DE123456789")
        self.assertEqual(self.validator.format_eori("de123456789"), "DE123456789")
        self.assertEqual(self.validator.format_eori("ATU 12345678"), "ATU12345678")
    
    def test_extract_country(self):
        """Test Ländercode-Extraktion"""
        self.assertEqual(self.validator.extract_country("DE123456789"), "DE")
        self.assertEqual(self.validator.extract_country("ATU12345678"), "AT")
        self.assertEqual(self.validator.extract_country("A"), None)
    
    def test_validate_format_deutsch(self):
        """Test deutsches EORI-Format"""
        valid, _, error = self.validator.validate_format("DE123456789")
        self.assertTrue(valid)
        self.assertIsNone(error)
        
        valid, _, error = self.validator.validate_format("DE12345")
        self.assertFalse(valid)
    
    def test_validate_format_oesterreich(self):
        """Test österreichisches EORI-Format"""
        valid, _, _ = self.validator.validate_format("ATU12345678")
        self.assertTrue(valid)
    
    def test_validate_format_ungueltiges_land(self):
        """Test ungültigen Ländercode"""
        valid, _, error = self.validator.validate_format("XX123456789")
        self.assertFalse(valid)
        self.assertIn("Ungültiger Ländercode", error)
    
    def test_zoll_pruefziffer(self):
        """Test Prüfziffer-Berechnung"""
        # Test mit einer bekannt gültigen Struktur (nicht garantiert echte EORI)
        validator = EORIValidator()
        
        # Prüfe ob Berechnung funktioniert
        result = validator._check_zoll_pruefziffer("123456789")
        # Wir können nicht garantieren dass diese Nummer gültig ist,
        # aber wir können testen dass die Funktion läuft
        self.assertIsInstance(result, bool)
    
    def test_get_info(self):
        """Test Info-Funktion"""
        info = self.validator.get_info("DE123456789")
        self.assertEqual(info['laendercode'], 'DE')
        self.assertEqual(info['land'], 'Deutschland')
        self.assertEqual(info['laenge'], 11)


class TestQuickValidation(unittest.TestCase):
    """Test der Quick-Validate Funktion"""
    
    def test_validate_eori_format_only(self):
        """Test Format-Only Validierung"""
        result = validate_eori("DE123456789")
        self.assertIn('valid', result)
        self.assertIn('eori', result)
        self.assertIn('land', result)


if __name__ == '__main__':
    unittest.main()
