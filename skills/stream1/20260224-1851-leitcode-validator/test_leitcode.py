"""
Tests für Deutsche Post Validator
"""

import unittest
from leitcode_validator import (
    DeutschePostValidator,
    validate_leitcode,
    validate_sendungsnummer
)


class TestDeutschePostValidator(unittest.TestCase):
    
    def setUp(self):
        self.validator = DeutschePostValidator()
    
    def test_format_code(self):
        """Test Code-Formatierung"""
        self.assertEqual(
            self.validator.format_code("12 34 567 1234 567"),
            "12345671234567"
        )
        self.assertEqual(
            self.validator.format_code("rx123456789de"),
            "RX123456789DE"
        )
    
    def test_validate_leitcode_laenge(self):
        """Test Leitcode Länge"""
        result = self.validator.validate_leitcode("1234567890123")
        self.assertFalse(result.gueltig)
        self.assertTrue(any('14 Ziffern' in f for f in result.fehler))
    
    def test_validate_leitcode_nur_zahlen(self):
        """Test Leitcode nur Zahlen"""
        result = self.validator.validate_leitcode("1234567ABCD567")
        self.assertFalse(result.gueltig)
        self.assertTrue(any('nur Ziffern' in f for f in result.fehler))
    
    def test_validate_sendungsnummer_dhl_packet(self):
        """Test DHL Packet Format"""
        result = self.validator.validate_sendungsnummer("003404341606")
        self.assertEqual(result.typ, 'DHL_PACKET')
    
    def test_validate_sendungsnummer_international(self):
        """Test DHL Packet International"""
        result = self.validator.validate_sendungsnummer("RX123456789DE")
        self.assertEqual(result.typ, 'DHL_PACKET_INTERNATIONAL')
        self.assertTrue(result.gueltig)
    
    def test_validate_sendungsnummer_deutsche_post(self):
        """Test Deutsche Post Format"""
        result = self.validator.validate_sendungsnummer("LX123456789DE")
        self.assertEqual(result.typ, 'DHL_PACKET_INTERNATIONAL')
    
    def test_validate_sendungsnummer_express(self):
        """Test DHL Express"""
        result = self.validator.validate_sendungsnummer("1234567890")
        self.assertEqual(result.typ, 'DHL_EXPRESS')
    
    def test_validate_sendungsnummer_unknown(self):
        """Test unbekanntes Format"""
        result = self.validator.validate_sendungsnummer("XYZ123")
        self.assertEqual(result.typ, 'UNKNOWN')
        self.assertFalse(result.gueltig)
    
    def test_validate_identcode(self):
        """Test Identcode"""
        result = self.validator.validate_identcode("12345678901")
        self.assertTrue(result.gueltig)
        self.assertEqual(result.typ, 'IDENTCODE')
    
    def test_validate_identcode_falsche_laenge(self):
        """Test Identcode falsche Länge"""
        result = self.validator.validate_identcode("1234567890")
        self.assertFalse(result.gueltig)
    
    def test_get_tracking_url_dhl(self):
        """Test Tracking URL für DHL"""
        url = self.validator.get_tracking_url("003404341606")
        self.assertIsNotNone(url)
        self.assertIn('dhl.de', url)
    
    def test_get_tracking_url_international(self):
        """Test Tracking URL für International"""
        url = self.validator.get_tracking_url("RX123456789DE")
        self.assertIsNotNone(url)
        self.assertIn('dhl.de', url)
    
    def test_get_tracking_url_unknown(self):
        """Test Tracking URL für unbekannt"""
        url = self.validator.get_tracking_url("UNKNOWN")
        self.assertIsNone(url)


class TestQuickFunctions(unittest.TestCase):
    """Test Convenience-Funktionen"""
    
    def test_validate_leitcode(self):
        """Test Schnell-Funktion Leitcode"""
        result = validate_leitcode("12345678901234")
        self.assertIn('gueltig', result)
        self.assertIn('frachtpost', result)
    
    def test_validate_sendungsnummer(self):
        """Test Schnell-Funktion Sendungsnummer"""
        result = validate_sendungsnummer("003404341606")
        self.assertIn('gueltig', result)
        self.assertIn('typ', result)
        self.assertIn('tracking_url', result)


if __name__ == '__main__':
    unittest.main()
