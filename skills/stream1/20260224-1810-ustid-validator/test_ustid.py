"""
Tests für USt-IdNr Validator
"""

import unittest
from ustid_validator import UStIdValidator, validate_ustid


class TestUStIdValidator(unittest.TestCase):
    
    def setUp(self):
        self.validator = UStIdValidator()
    
    def test_format_ustid_deutsch(self):
        """Test Deutsche USt-IdNr Formatierung"""
        self.assertEqual(self.validator.format_ustid("123456789"), "DE123456789")
        self.assertEqual(self.validator.format_ustid("DE 123 456 789"), "DE123456789")
        self.assertEqual(self.validator.format_ustid("de123456789"), "DE123456789")
    
    def test_format_ustid_eu(self):
        """Test EU USt-IdNr Formatierung"""
        self.assertEqual(self.validator.format_ustid("ATU12345678"), "ATU12345678")
        self.assertEqual(self.validator.format_ustid("FR 12 345 678 901"), "FR12345678901")
    
    def test_validate_format_deutsch(self):
        """Test Format-Validierung Deutschland"""
        valid, _ = self.validator.validate_format("DE123456789")
        self.assertTrue(valid)
        
        valid, _ = self.validator.validate_format("DE12345")
        self.assertFalse(valid)
    
    def test_validate_format_eu(self):
        """Test Format-Validierung EU"""
        valid, _ = self.validator.validate_format("ATU12345678")
        self.assertTrue(valid)
        
        valid, _ = self.validator.validate_format("FRXX12345678")
        self.assertTrue(valid)
    
    def test_land_zuordnung(self):
        """Test EU-Länder-Zuordnung"""
        self.assertEqual(self.validator.EU_COUNTRIES.get('DE'), 'Deutschland')
        self.assertEqual(self.validator.EU_COUNTRIES.get('AT'), 'Österreich')
        self.assertEqual(self.validator.EU_COUNTRIES.get('FR'), 'Frankreich')


class TestIntegration(unittest.TestCase):
    """Integration Tests - benötigen Internet"""
    
    def test_online_check_gueltige_ustid(self):
        """Test mit bekannter gültiger USt-IdNr"""
        # Dies ist ein Test-Endpunkt, kein garantiert gültiger Wert
        validator = UStIdValidator()
        result = validator.validate_online("DE123456789")
        
        # Sollte eine Antwort liefern (nicht None)
        self.assertIn('status', result)
        self.assertIn('valid', result)
    
    def test_online_check_eu_ustid(self):
        """Test mit EU USt-IdNr (nicht DE)"""
        result = validate_ustid("ATU12345678")
        
        # Sollte Format-Validierung durchführen, aber kein Online-Check
        self.assertTrue(result.get('format_check'))
        self.assertFalse(result.get('online_check'))
        self.assertEqual(result.get('status'), 'EU_FORMAT_VALID')


if __name__ == '__main__':
    unittest.main()
