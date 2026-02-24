"""
Tests für SEPA Validator
"""

import unittest
from sepa_validator import SEPAValidator, validate_iban, validate_bic, create_german_iban


class TestSEPAValidator(unittest.TestCase):
    
    def setUp(self):
        self.validator = SEPAValidator()
    
    def test_format_iban(self):
        """Test IBAN-Formatierung"""
        self.assertEqual(
            self.validator.format_iban("DE89 3704 0044 0532 0130 00"),
            "DE89370400440532013000"
        )
        self.assertEqual(
            self.validator.format_iban("de89370400440532013000"),
            "DE89370400440532013000"
        )
    
    def test_format_bic(self):
        """Test BIC-Formatierung"""
        self.assertEqual(
            self.validator.format_bic("cobadeffxxx"),
            "COBADEFFXXX"
        )
    
    def test_validate_iban_gueltig(self):
        """Test gültige IBAN"""
        # Dies ist eine Test-IBAN (kann echt sein oder nicht)
        result = self.validator.validate_iban("DE89370400440532013000")
        self.assertIsNotNone(result.iban)
        self.assertEqual(result.land, 'Deutschland')
        self.assertTrue(result.sepa_faehig)
    
    def test_validate_iban_ungueltiges_land(self):
        """Test ungültiger Ländercode"""
        result = self.validator.validate_iban("XX89370400440532013000")
        self.assertFalse(result.gueltig)
        self.assertTrue(any('Ungültiger Ländercode' in f for f in result.fehler))
    
    def test_validate_iban_falsche_laenge(self):
        """Test falsche Länge"""
        result = self.validator.validate_iban("DE123")
        self.assertFalse(result.gueltig)
        self.assertTrue(any('zu kurz' in f.lower() or 'Länge' in f for f in result.fehler))
    
    def test_validate_bic_gueltig_11(self):
        """Test gültiger BIC (11 Stellen)"""
        result = self.validator.validate_bic("COBADEFFXXX")
        self.assertTrue(result['gueltig'])
        self.assertEqual(result['bankcode'], 'COBA')
        self.assertEqual(result['laendercode'], 'DE')
    
    def test_validate_bic_gueltig_8(self):
        """Test gültiger BIC (8 Stellen)"""
        result = self.validator.validate_bic("COBADEFF")
        self.assertTrue(result['gueltig'])
        self.assertEqual(len(result['bic']), 8)
    
    def test_validate_bic_ungueltige_laenge(self):
        """Test BIC mit falscher Länge"""
        result = self.validator.validate_bic("COBA")
        self.assertFalse(result['gueltig'])
        self.assertTrue(any('8 oder 11' in f for f in result['fehler']))
    
    def test_validate_bic_ungueltiger_laendercode(self):
        """Test BIC mit ungültigem Ländercode"""
        result = self.validator.validate_bic("COBAXXFFXXX")
        self.assertFalse(result['gueltig'])
    
    def test_german_to_iban(self):
        """Test deutsche IBAN-Erstellung"""
        result = self.validator.german_to_iban("37040044", "532013000")
        self.assertTrue(result['gueltig'])
        self.assertTrue(result['iban'].startswith('DE'))
        self.assertEqual(result['blz'], '37040044')
    
    def test_german_to_iban_falsche_blz(self):
        """Test IBAN-Erstellung mit falscher BLZ"""
        result = self.validator.german_to_iban("123", "123456")
        self.assertFalse(result['gueltig'])
        self.assertTrue(any('BLZ muss 8' in f for f in result['fehler']))
    
    def test_format_iban_readable(self):
        """Test lesbare Formatierung"""
        formatted = self.validator.format_iban_readable("DE89370400440532013000")
        self.assertEqual(formatted, "DE89 3704 0044 0532 0130 00")
    
    def test_is_sepa_country(self):
        """Test SEPA-Länderprüfung"""
        self.assertTrue(self.validator.is_sepa_country('DE'))
        self.assertTrue(self.validator.is_sepa_country('FR'))
        self.assertTrue(self.validator.is_sepa_country('AT'))
        self.assertFalse(self.validator.is_sepa_country('US'))


class TestQuickFunctions(unittest.TestCase):
    """Test Convenience-Funktionen"""
    
    def test_validate_iban(self):
        """Test Schnell-Validierung"""
        result = validate_iban("DE89370400440532013000")
        self.assertIn('gueltig', result)
        self.assertIn('land', result)
        self.assertIn('sepa_faehig', result)
    
    def test_validate_bic_quick(self):
        """Test Schnell-BIC-Validierung"""
        result = validate_bic("COBADEFFXXX")
        self.assertIn('gueltig', result)
        self.assertIn('bankcode', result)
    
    def test_create_german_iban(self):
        """Test Schnell-IBAN-Erstellung"""
        result = create_german_iban("37040044", "532013000")
        self.assertIn('gueltig', result)
        self.assertIn('iban', result)


if __name__ == '__main__':
    unittest.main()
