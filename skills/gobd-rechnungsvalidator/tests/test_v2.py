#!/usr/bin/env python3
"""
Tests für GoBD-Rechnungsvalidator v2.0
"""

import unittest
import tempfile
import json
import os
from pathlib import Path

from gobd_validator_v2 import GoBDValidator, ValidationResult, batch_validate


class TestGoBDValidator(unittest.TestCase):
    """Tests für GoBDValidator"""
    
    def setUp(self):
        self.validator = GoBDValidator(use_ocr=False)
    
    def test_validation_result_dataclass(self):
        """Test ValidationResult Dataclass"""
        result = ValidationResult(
            filename="test.pdf",
            is_valid=True,
            score=8,
            max_score=9,
            confidence=0.89,
            missing_fields=[],
            extracted_data={},
            warnings=[],
            zugferd_compatible=True
        )
        
        self.assertEqual(result.filename, "test.pdf")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.score, 8)
    
    def test_find_lieferant(self):
        """Test Lieferant-Erkennung"""
        text = """Muster GmbH
Musterstraße 1
12345 Berlin

Rechnung"""
        
        result = self.validator.find_lieferant(text)
        self.assertIsNotNone(result['name'])
        self.assertIn('Muster', result['name'])
    
    def test_find_steuernummer(self):
        """Test Steuernummer-Erkennung"""
        text = "St-Nr.: 123 456 7890"
        result = self.validator.find_steuernummer(text)
        self.assertIsNotNone(result)
        
        text2 = "Steuernummer: 1234567890"
        result2 = self.validator.find_steuernummer(text2)
        self.assertIsNotNone(result2)
    
    def test_find_ust_id(self):
        """Test USt-IdNr-Erkennung"""
        text = "USt-IdNr: DE123456789"
        result = self.validator.find_ust_id(text)
        self.assertEqual(result, "DE123456789")
    
    def test_find_rechnungsnummer(self):
        """Test Rechnungsnummer-Erkennung"""
        text = "Rechnungsnummer: RE-2025-001"
        result = self.validator.find_rechnungsnummer(text)
        self.assertEqual(result, "RE-2025-001")
    
    def test_find_rechnungsdatum(self):
        """Test Rechnungsdatum-Erkennung"""
        text = "Rechnungsdatum: 15.02.2025"
        result = self.validator.find_rechnungsdatum(text)
        self.assertEqual(result, "15.02.2025")
        
        # Auch ohne explizite Beschriftung
        text2 = "15.02.2025"
        result2 = self.validator.find_rechnungsdatum(text2)
        self.assertEqual(result2, "15.02.2025")
    
    def test_find_gesamtbetrag(self):
        """Test Betrags-Erkennung"""
        text = "Gesamtbetrag: 1.234,56 €"
        result = self.validator.find_gesamtbetrag(text)
        self.assertIsNotNone(result)
    
    def test_find_ust_satz(self):
        """Test USt-Satz-Erkennung"""
        text = "19% USt"
        result = self.validator.find_ust_satz(text)
        self.assertIn("19", result)
        
        text2 = "steuerfrei"
        result2 = self.validator.find_ust_satz(text2)
        self.assertEqual(result2, "steuerfrei")


class TestIntegration(unittest.TestCase):
    """Integrationstests"""
    
    def test_zugferd_compatibility_check(self):
        """Test ZUGFeRD-Kompatibilitäts-Check"""
        validator = GoBDValidator(use_ocr=False)
        
        # Simuliere Text mit allen Pflichtfeldern
        text = """Muster GmbH
Musterstraße 1, 12345 Berlin
St-Nr.: 1234567890

Rechnung Nr: RE-001
Datum: 15.02.2025

Positionen:
- Software 1x 1000,00 EUR

Gesamtbetrag: 1.190,00 EUR
19% USt"""
        
        # Manuelle Extraktion
        lieferant = validator.find_lieferant(text)
        rechnungsnr = validator.find_rechnungsnummer(text)
        rechnungsdatum = validator.find_rechnungsdatum(text)
        steuernr = validator.find_steuernummer(text)
        ustid = validator.find_ust_id(text)
        
        # Prüfe ZUGFeRD-Kompatibilität
        zugferd_compatible = (
            lieferant['name'] and
            rechnungsnr and
            rechnungsdatum and
            (steuernr or ustid)
        )
        
        self.assertTrue(zugferd_compatible)


class TestBatchProcessing(unittest.TestCase):
    """Tests für Batch-Verarbeitung"""
    
    def test_batch_validate_empty_folder(self):
        """Test Batch-Verarbeitung mit leerem Ordner"""
        with tempfile.TemporaryDirectory() as tmpdir:
            stats = batch_validate(tmpdir)
            self.assertEqual(stats['total'], 0)
    
    def test_batch_results_json(self):
        """Test dass Batch-Ergebnisse gespeichert werden"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "results.json")
            
            # Leerer Ordner
            stats = batch_validate(tmpdir, output_file)
            
            # Prüfe dass Datei existiert
            self.assertTrue(os.path.exists(output_file))
            
            # Lade und prüfe JSON
            with open(output_file, 'r') as f:
                data = json.load(f)
                self.assertIsInstance(data, list)


if __name__ == '__main__':
    unittest.main(verbosity=2)
