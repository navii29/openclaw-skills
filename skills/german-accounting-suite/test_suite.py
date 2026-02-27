#!/usr/bin/env python3
"""
German Accounting Suite - Production Test Suite

End-to-End Tests für kompletten Workflow:
PDF → GoBD → ZUGFeRD → DATEV → SEPA

Tests:
- Vollständiger Workflow
- Fehlerbehandlung
- Batch-Verarbeitung
- Edge Cases
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gobd-rechnungsvalidator'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'zugferd-generator'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'datev-csv-export'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sepa_xml_generator'))

from suite_integration import (
    GermanAccountingSuite, 
    AccountingWorkflowResult
)


class MockValidationResult:
    """Mock für GoBD ValidationResult"""
    def __init__(self, is_valid=True, zugferd_compatible=True, score=8):
        self.is_valid = is_valid
        self.zugferd_compatible = zugferd_compatible
        self.score = score
        self.max_score = 9
        self.extracted_data = {
            'lieferant_name': 'Muster GmbH',
            'lieferant_anschrift': 'Musterstraße 1, 12345 Berlin',
            'empfaenger_name': 'Kunde AG',
            'steuernummer': '1234567890',
            'ust_id': 'DE123456789',
            'rechnungsdatum': '15.02.2025',
            'rechnungsnummer': 'RE-2025-001',
            'gesamtbetrag': '1.190,00 €',
            'ust_satz': '19%',
            'positionen_vorhanden': True
        }
        self.missing_fields = []


class TestAccountingWorkflowResult(unittest.TestCase):
    """Test AccountingWorkflowResult Dataclass"""
    
    def test_result_creation(self):
        """Test result creation"""
        result = AccountingWorkflowResult(
            pdf_path="/test/rechnung.pdf",
            is_valid=True,
            zugferd_path="/test/out.zugferd.zip",
            datev_path="/test/out.csv",
            sepa_path="/test/out.xml",
            extracted_data={'test': 'data'},
            errors=[]
        )
        
        self.assertEqual(result.pdf_path, "/test/rechnung.pdf")
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.zugferd_path)
    
    def test_result_summary(self):
        """Test summary output"""
        result = AccountingWorkflowResult(
            pdf_path="rechnung.pdf",
            is_valid=True,
            zugferd_path="out.zugferd.zip",
            datev_path="out.csv",
            sepa_path="out.xml",
            extracted_data={},
            errors=[]
        )
        
        summary = result.summary()
        self.assertIn("rechnung.pdf", summary)
        self.assertIn("✅", summary)
        self.assertIn("ZUGFeRD", summary)
        self.assertIn("DATEV", summary)
        self.assertIn("SEPA", summary)
    
    def test_result_summary_with_errors(self):
        """Test summary with errors"""
        result = AccountingWorkflowResult(
            pdf_path="rechnung.pdf",
            is_valid=False,
            zugferd_path=None,
            datev_path=None,
            sepa_path=None,
            extracted_data={},
            errors=["Validation failed", "PDF corrupted"]
        )
        
        summary = result.summary()
        self.assertIn("❌", summary)
        self.assertIn("Fehler", summary)


class TestSuiteInitialization(unittest.TestCase):
    """Test GermanAccountingSuite initialization"""
    
    @patch('suite_integration.SUITE_AVAILABLE', True)
    @patch('suite_integration.GoBDValidator')
    @patch('suite_integration.ZUGFeRDGenerator')
    @patch('suite_integration.DATEVExporter')
    @patch('suite_integration.SEPAGenerator')
    def test_init_success(self, mock_sepa, mock_datev, mock_zugferd, mock_gobd):
        """Successful initialization"""
        suite = GermanAccountingSuite(use_ocr=True, smart_suggest=True)
        
        self.assertIsNotNone(suite.validator)
        self.assertIsNotNone(suite.zugferd_generator)
        self.assertIsNotNone(suite.datev_exporter)
        self.assertIsNotNone(suite.sepa_generator)
        self.assertEqual(suite.VERSION, "1.0.0")
    
    @patch('suite_integration.SUITE_AVAILABLE', False)
    def test_init_without_modules(self):
        """Initialization fails without modules"""
        with self.assertRaises(RuntimeError) as context:
            GermanAccountingSuite()
        
        self.assertIn("nicht verfügbar", str(context.exception))


class TestProcessInvoice(unittest.TestCase):
    """Test complete invoice processing workflow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf = os.path.join(self.temp_dir, "test_rechnung.pdf")
        
        # Create dummy PDF
        with open(self.test_pdf, 'w') as f:
            f.write("dummy pdf content")
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('suite_integration.SUITE_AVAILABLE', True)
    @patch('suite_integration.GoBDValidator')
    @patch('suite_integration.ZUGFeRDGenerator')
    @patch('suite_integration.DATEVExporter')
    @patch('suite_integration.SEPAGenerator')
    def test_full_workflow_success(self, mock_sepa_class, mock_datev_class, mock_zugferd_class, mock_gobd_class):
        """Test complete successful workflow"""
        # Setup mocks
        mock_validator = Mock()
        mock_validator.validate.return_value = MockValidationResult(is_valid=True)
        mock_validator.generate_zugferd.return_value = "/output/test.zugferd.zip"
        mock_gobd_class.return_value = mock_validator
        
        mock_zugferd = Mock()
        mock_zugferd_class.return_value = mock_zugferd
        
        mock_exporter = Mock()
        mock_exporter.export.return_value = "/output/test_datev.csv"
        mock_datev_class.return_value = mock_exporter
        
        mock_sepa = Mock()
        mock_sepa_class.return_value = mock_sepa
        
        # Execute
        suite = GermanAccountingSuite()
        result = suite.process_invoice(
            pdf_path=self.test_pdf,
            output_dir=self.temp_dir,
            creditor_iban="DE89370400440532013000"
        )
        
        # Verify
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.zugferd_path)
        self.assertIsNotNone(result.datev_path)
        self.assertEqual(len(result.errors), 0)
        
        # Verify all components were called
        mock_validator.validate.assert_called_once()
        mock_validator.generate_zugferd.assert_called_once()
        mock_exporter.export.assert_called_once()
    
    @patch('suite_integration.SUITE_AVAILABLE', True)
    @patch('suite_integration.GoBDValidator')
    def test_workflow_invalid_pdf(self, mock_gobd_class):
        """Test workflow with invalid PDF"""
        mock_validator = Mock()
        mock_validator.validate.return_value = MockValidationResult(
            is_valid=False,
            zugferd_compatible=False,
            score=3
        )
        mock_gobd_class.return_value = mock_validator
        
        suite = GermanAccountingSuite()
        result = suite.process_invoice(
            pdf_path=self.test_pdf,
            output_dir=self.temp_dir
        )
        
        self.assertFalse(result.is_valid)
        self.assertIsNone(result.zugferd_path)
        self.assertIsNone(result.datev_path)
    
    @patch('suite_integration.SUITE_AVAILABLE', True)
    @patch('suite_integration.GoBDValidator')
    @patch('suite_integration.ZUGFeRDGenerator')
    @patch('suite_integration.DATEVExporter')
    def test_workflow_partial_failure(self, mock_datev_class, mock_zugferd_class, mock_gobd_class):
        """Test workflow where some steps fail"""
        mock_validator = Mock()
        mock_validator.validate.return_value = MockValidationResult(is_valid=True)
        mock_validator.generate_zugferd.side_effect = Exception("ZUGFeRD failed")
        mock_gobd_class.return_value = mock_validator
        
        mock_zugferd_class.return_value = Mock()
        mock_datev_class.return_value = Mock()
        
        suite = GermanAccountingSuite()
        result = suite.process_invoice(
            pdf_path=self.test_pdf,
            output_dir=self.temp_dir
        )
        
        # Should still be valid but with errors
        self.assertTrue(result.is_valid)
        self.assertGreater(len(result.errors), 0)
    
    @patch('suite_integration.SUITE_AVAILABLE', True)
    @patch('suite_integration.GoBDValidator')
    @patch('suite_integration.ZUGFeRDGenerator')
    @patch('suite_integration.DATEVExporter')
    @patch('suite_integration.SEPAGenerator')
    def test_workflow_without_sepa(self, mock_sepa, mock_datev, mock_zugferd, mock_gobd):
        """Test workflow without SEPA generation"""
        mock_validator = Mock()
        mock_validator.validate.return_value = MockValidationResult(is_valid=True)
        mock_gobd.return_value = mock_validator
        
        suite = GermanAccountingSuite()
        result = suite.process_invoice(
            pdf_path=self.test_pdf,
            output_dir=self.temp_dir,
            generate_sepa=False
        )
        
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.sepa_path)
    
    @patch('suite_integration.SUITE_AVAILABLE', True)
    @patch('suite_integration.GoBDValidator')
    @patch('suite_integration.ZUGFeRDGenerator')
    @patch('suite_integration.DATEVExporter')
    def test_workflow_without_iban(self, mock_datev, mock_zugferd, mock_gobd):
        """Test that SEPA is skipped without IBAN"""
        mock_validator = Mock()
        mock_validator.validate.return_value = MockValidationResult(is_valid=True)
        mock_gobd.return_value = mock_validator
        
        suite = GermanAccountingSuite()
        result = suite.process_invoice(
            pdf_path=self.test_pdf,
            output_dir=self.temp_dir,
            generate_sepa=True,  # Requested but no IBAN
            creditor_iban=None
        )
        
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.sepa_path)  # Should be skipped


class TestBatchProcessing(unittest.TestCase):
    """Test batch processing functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Create multiple test PDFs
        for i in range(3):
            pdf_path = os.path.join(self.temp_dir, f"rechnung_{i}.pdf")
            with open(pdf_path, 'w') as f:
                f.write(f"dummy content {i}")
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('suite_integration.SUITE_AVAILABLE', True)
    @patch('suite_integration.GoBDValidator')
    @patch('suite_integration.ZUGFeRDGenerator')
    @patch('suite_integration.DATEVExporter')
    @patch('suite_integration.SEPAGenerator')
    def test_batch_process_all_success(self, mock_sepa, mock_datev, mock_zugferd, mock_gobd):
        """Test batch processing all successful"""
        mock_validator = Mock()
        mock_validator.validate.return_value = MockValidationResult(is_valid=True)
        mock_validator.generate_zugferd.return_value = "/output/test.zugferd.zip"
        mock_gobd.return_value = mock_validator
        
        mock_exporter = Mock()
        mock_exporter.export.return_value = "/output/test.csv"
        mock_datev.return_value = mock_exporter
        
        suite = GermanAccountingSuite()
        results = suite.batch_process(
            pdf_folder=self.temp_dir,
            output_dir=self.temp_dir
        )
        
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r.is_valid for r in results))
    
    @patch('suite_integration.SUITE_AVAILABLE', True)
    @patch('suite_integration.GoBDValidator')
    def test_batch_process_mixed_results(self, mock_gobd):
        """Test batch with some failures"""
        # First two valid, third invalid
        results_sequence = [
            MockValidationResult(is_valid=True),
            MockValidationResult(is_valid=True),
            MockValidationResult(is_valid=False)
        ]
        
        mock_validator = Mock()
        mock_validator.validate.side_effect = results_sequence
        mock_gobd.return_value = mock_validator
        
        suite = GermanAccountingSuite()
        results = suite.batch_process(
            pdf_folder=self.temp_dir,
            output_dir=self.temp_dir
        )
        
        self.assertEqual(len(results), 3)
        self.assertEqual(sum(1 for r in results if r.is_valid), 2)
        self.assertEqual(sum(1 for r in results if not r.is_valid), 1)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    @patch('suite_integration.SUITE_AVAILABLE', True)
    @patch('suite_integration.GoBDValidator')
    def test_nonexistent_pdf(self, mock_gobd):
        """Test with non-existent PDF file"""
        mock_validator = Mock()
        mock_validator.validate.side_effect = FileNotFoundError("PDF not found")
        mock_gobd.return_value = mock_validator
        
        suite = GermanAccountingSuite()
        
        with self.assertRaises(FileNotFoundError):
            suite.process_invoice("/nonexistent/file.pdf")
    
    @patch('suite_integration.SUITE_AVAILABLE', True)
    @patch('suite_integration.GoBDValidator')
    @patch('suite_integration.ZUGFeRDGenerator')
    @patch('suite_integration.DATEVExporter')
    def test_empty_output_dir(self, mock_datev, mock_zugferd, mock_gobd):
        """Test with output directory creation"""
        temp_dir = tempfile.mkdtemp()
        output_dir = os.path.join(temp_dir, "nested", "output")
        
        mock_validator = Mock()
        mock_validator.validate.return_value = MockValidationResult(is_valid=True)
        mock_gobd.return_value = mock_validator
        
        try:
            suite = GermanAccountingSuite()
            result = suite.process_invoice(
                pdf_path=os.path.join(temp_dir, "test.pdf"),
                output_dir=output_dir
            )
            
            self.assertTrue(os.path.exists(output_dir))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestDataExtraction(unittest.TestCase):
    """Test data extraction from PDFs"""
    
    @patch('suite_integration.SUITE_AVAILABLE', True)
    @patch('suite_integration.GoBDValidator')
    def test_extracted_data_structure(self, mock_gobd):
        """Test that extracted data has correct structure"""
        expected_data = {
            'lieferant_name': 'Test GmbH',
            'rechnungsnummer': 'RE-001',
            'gesamtbetrag': '1000,00 €'
        }
        
        mock_result = MockValidationResult()
        mock_result.extracted_data = expected_data
        
        mock_validator = Mock()
        mock_validator.validate.return_value = mock_result
        mock_gobd.return_value = mock_validator
        
        suite = GermanAccountingSuite()
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'dummy')
            temp_pdf = f.name
        
        try:
            result = suite.process_invoice(temp_pdf)
            self.assertIn('lieferant_name', result.extracted_data)
            self.assertIn('rechnungsnummer', result.extracted_data)
        finally:
            os.unlink(temp_pdf)


def run_all_tests():
    """Run complete test suite"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAccountingWorkflowResult))
    suite.addTests(loader.loadTestsFromTestCase(TestSuiteInitialization))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessInvoice))
    suite.addTests(loader.loadTestsFromTestCase(TestBatchProcessing))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestDataExtraction))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
