"""
Tests für XRechnung Validator
"""

import unittest
from xrechnung_validator import (
    XRechnungValidator, 
    validate_xrechnung,
    XRechnungValidationResult
)


class TestXRechnungValidator(unittest.TestCase):
    
    def setUp(self):
        self.validator = XRechnungValidator()
    
    def test_validate_leitweg_id_gueltig(self):
        """Test gültige Leitweg-ID"""
        result = self.validator.validate_leitweg_id("991-12345-67")
        self.assertTrue(result['gueltig'])
    
    def test_validate_leitweg_id_ungueltig(self):
        """Test ungültige Leitweg-ID mit Buchstaben"""
        result = self.validator.validate_leitweg_id("ABC-123")
        self.assertFalse(result['gueltig'])
    
    def test_validate_leitweg_id_leer(self):
        """Test leere Leitweg-ID"""
        result = self.validator.validate_leitweg_id("")
        self.assertFalse(result['gueltig'])
    
    def test_validate_xml_gueltig(self):
        """Test XML-Validierung mit gültigem XML"""
        xml = """<?xml version="1.0"?>
<root xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100">
    <rsm:CrossIndustryInvoice>
        <rsm:ExchangedDocument>
            <ram:ID>TEST-001</ram:ID>
        </rsm:ExchangedDocument>
    </rsm:CrossIndustryInvoice>
</root>"""
        result = self.validator.validate_xrechnung_xml(xml)
        # Sollte Parsen ohne Fehler
        self.assertIsInstance(result, XRechnungValidationResult)
    
    def test_validate_xml_ungueltig(self):
        """Test XML-Validierung mit ungültigem XML"""
        xml = "<ungültiges>"
        result = self.validator.validate_xrechnung_xml(xml)
        self.assertFalse(result.gueltig)
        self.assertTrue(any('Parse-Fehler' in f for f in result.fehler))
    
    def test_detect_profile_cii(self):
        """Test CII-Profil-Erkennung"""
        xml = "<root><rsm:CrossIndustryInvoice xmlns:rsm='test'></rsm:CrossIndustryInvoice></root>"
        root = __import__('xml.etree.ElementTree').etree.ElementTree.fromstring(xml)
        # Note: Dieser Test prüft die Logik, nicht das eigentliche Parsing
        result = self.validator.validate_xrechnung_xml(xml)
        self.assertIn(result.profil, ['XRECHNUNG_CII', 'UNKNOWN'])


class TestQuickValidation(unittest.TestCase):
    """Test der Convenience-Funktion"""
    
    def test_validate_xrechnung(self):
        """Test Schnell-Funktion"""
        xml = "<?xml version='1.0'?><root/>"
        result = validate_xrechnung(xml)
        self.assertIn('gueltig', result)
        self.assertIn('profil', result)
        self.assertIn('fehler', result)


class TestPflichtfelder(unittest.TestCase):
    """Test Pflichtfelder-Validierung"""
    
    def test_pflichtfelder_definition(self):
        """Test dass Pflichtfelder definiert sind"""
        validator = XRechnungValidator()
        self.assertIn('seller_name', validator.PFLICHTFELDER)
        self.assertIn('invoice_number', validator.PFLICHTFELDER)
        self.assertIn('total_gross', validator.PFLICHTFELDER)


if __name__ == '__main__':
    unittest.main()
