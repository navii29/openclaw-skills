#!/usr/bin/env python3
"""
Tests for SEPA-XML Generator
"""

import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
import tempfile
import os

from sepa_generator import (
    SepaCreditTransfer,
    SepaDirectDebit,
    SepaValidationError,
    validate_iban,
    validate_bic,
    validate_amount,
    format_amount,
    sanitize_text
)


class TestValidationFunctions(unittest.TestCase):
    """Test validation helper functions."""
    
    def test_validate_iban_valid(self):
        """Test valid German IBAN."""
        self.assertTrue(validate_iban("DE89370400440532013000"))
        self.assertTrue(validate_iban("de89 3704 0044 0532 0130 00"))  # lowercase with spaces
    
    def test_validate_iban_invalid(self):
        """Test invalid IBANs."""
        with self.assertRaises(SepaValidationError):
            validate_iban("")  # empty
        with self.assertRaises(SepaValidationError):
            validate_iban("FR89370400440532013000")  # non-German
        with self.assertRaises(SepaValidationError):
            validate_iban("DE8937040044053201300")  # too short
        with self.assertRaises(SepaValidationError):
            validate_iban("DE893704004405320130000")  # too long
        with self.assertRaises(SepaValidationError):
            validate_iban("DEXX370400440532013000")  # non-numeric
    
    def test_validate_bic_valid(self):
        """Test valid BIC."""
        self.assertTrue(validate_bic("COBADEFF"))
        self.assertTrue(validate_bic("COBADEFFXXX"))
        self.assertTrue(validate_bic("cobadeff"))  # lowercase
    
    def test_validate_bic_invalid(self):
        """Test invalid BICs."""
        with self.assertRaises(SepaValidationError):
            validate_bic("COBA")  # too short
        with self.assertRaises(SepaValidationError):
            validate_bic("COBADEFFXXXX")  # too long
        with self.assertRaises(SepaValidationError):
            validate_bic("12345678")  # invalid format
    
    def test_validate_amount_valid(self):
        """Test valid amounts."""
        self.assertTrue(validate_amount(0.01))
        self.assertTrue(validate_amount(1500.00))
        self.assertTrue(validate_amount(999999999.99))
    
    def test_validate_amount_invalid(self):
        """Test invalid amounts."""
        with self.assertRaises(SepaValidationError):
            validate_amount(0)
        with self.assertRaises(SepaValidationError):
            validate_amount(-100)
        with self.assertRaises(SepaValidationError):
            validate_amount(1000000000)
    
    def test_format_amount(self):
        """Test amount formatting."""
        self.assertEqual(format_amount(1500), "1500.00")
        self.assertEqual(format_amount(1500.5), "1500.50")
        self.assertEqual(format_amount(1500.555), "1500.56")  # rounding
        self.assertEqual(format_amount(0.01), "0.01")
    
    def test_sanitize_text(self):
        """Test text sanitization."""
        self.assertEqual(sanitize_text("Hello World", 50), "Hello World")
        self.assertEqual(sanitize_text("A" * 200, 140), "A" * 140)  # truncation
        self.assertEqual(sanitize_text("Test \u003c\u003e\u0026", 50), "Test +++")  # XML chars
        self.assertEqual(sanitize_text("  Trim  ", 50), "Trim")  # stripping


class TestSepaCreditTransfer(unittest.TestCase):
    """Test Credit Transfer functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sct = SepaCreditTransfer(
            msg_id="TEST-MSG-001",
            initiator_name="Test GmbH",
            creation_date_time="2024-02-25T10:00:00"
        )
        
        self.sct.add_payment_info(
            payment_info_id="PAY-001",
            debtor_name="Test GmbH",
            debtor_iban="DE89370400440532013000",
            debtor_bic="COBADEFFXXX",
            requested_execution_date="2024-02-26"
        )
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.sct.msg_id, "TEST-MSG-001")
        self.assertEqual(self.sct.initiator_name, "Test GmbH")
        self.assertEqual(self.sct.creation_date_time, "2024-02-25T10:00:00")
    
    def test_add_payment_info(self):
        """Test adding payment info."""
        self.assertEqual(len(self.sct.payment_infos), 1)
        pmt = self.sct.payment_infos[0]
        self.assertEqual(pmt["id"], "PAY-001")
        self.assertEqual(pmt["debtor_name"], "Test GmbH")
        self.assertEqual(pmt["debtor_iban"], "DE89370400440532013000")
    
    def test_add_payment_info_invalid_iban(self):
        """Test payment info with invalid IBAN."""
        with self.assertRaises(SepaValidationError):
            self.sct.add_payment_info(
                payment_info_id="PAY-002",
                debtor_name="Test",
                debtor_iban="INVALID"
            )
    
    def test_add_transaction(self):
        """Test adding transaction."""
        self.sct.add_transaction(
            end_to_end_id="E2E-001",
            amount=1500.00,
            creditor_name="Lieferant AG",
            creditor_iban="DE75512108001245126199",
            creditor_bic="INGDDEFFXXX",
            remittance_info="Rechnung 2024-001"
        )
        
        self.assertEqual(len(self.sct.transactions), 1)
        trx = self.sct.transactions[0]
        self.assertEqual(trx["end_to_end_id"], "E2E-001")
        self.assertEqual(trx["amount"], 1500.00)
        self.assertEqual(trx["creditor_name"], "Lieferant AG")
    
    def test_add_transaction_invalid_amount(self):
        """Test transaction with invalid amount."""
        with self.assertRaises(SepaValidationError):
            self.sct.add_transaction(
                end_to_end_id="E2E-001",
                amount=-100,
                creditor_name="Test",
                creditor_iban="DE75512108001245126199"
            )
    
    def test_to_xml_structure(self):
        """Test XML structure generation."""
        self.sct.add_transaction(
            end_to_end_id="E2E-001",
            amount=1500.00,
            creditor_name="Lieferant AG",
            creditor_iban="DE75512108001245126199",
            creditor_bic="INGDDEFFXXX",
            remittance_info="Rechnung 2024-001"
        )
        
        xml_string = self.sct.to_xml()
        
        # Parse and verify
        root = ET.fromstring(xml_string)
        self.assertIn("Document", root.tag)
        
        # Check namespaces
        ns = {"sepa": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"}
        
        # Verify group header
        msg_id = root.find(".//sepa:MsgId", ns)
        self.assertIsNotNone(msg_id)
        self.assertEqual(msg_id.text, "TEST-MSG-001")
        
        ctrl_sum = root.find(".//sepa:GrpHdr/sepa:CtrlSum", ns)
        self.assertIsNotNone(ctrl_sum)
        self.assertEqual(ctrl_sum.text, "1500.00")
    
    def test_to_xml_no_payment_info(self):
        """Test XML generation without payment info."""
        empty_sct = SepaCreditTransfer(
            msg_id="TEST-002",
            initiator_name="Test GmbH"
        )
        with self.assertRaises(SepaValidationError):
            empty_sct.to_xml()
    
    def test_to_xml_no_transactions(self):
        """Test XML generation without transactions."""
        with self.assertRaises(SepaValidationError):
            self.sct.to_xml()
    
    def test_to_file(self):
        """Test file output."""
        self.sct.add_transaction(
            end_to_end_id="E2E-001",
            amount=1500.00,
            creditor_name="Lieferant AG",
            creditor_iban="DE75512108001245126199"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            temp_path = f.name
        
        try:
            self.sct.to_file(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn("TEST-MSG-001", content)
            self.assertIn("?xml version", content)  # XML declaration
        finally:
            os.unlink(temp_path)
    
    def test_validate(self):
        """Test validation method."""
        self.assertFalse(self.sct.validate())  # No transactions
        
        self.sct.add_transaction(
            end_to_end_id="E2E-001",
            amount=1500.00,
            creditor_name="Lieferant AG",
            creditor_iban="DE75512108001245126199"
        )
        self.assertTrue(self.sct.validate())
    
    def test_multiple_transactions(self):
        """Test multiple transactions."""
        self.sct.add_transaction(
            end_to_end_id="E2E-001",
            amount=1000.00,
            creditor_name="Lieferant A",
            creditor_iban="DE75512108001245126199"
        )
        self.sct.add_transaction(
            end_to_end_id="E2E-002",
            amount=2000.00,
            creditor_name="Lieferant B",
            creditor_iban="DE12500105170648489890"
        )
        
        xml_string = self.sct.to_xml()
        root = ET.fromstring(xml_string)
        ns = {"sepa": "urn:iso:std:iso:20022:tech:xsd:pain.001.001.09"}
        
        # Check transaction count
        nb_of_txs = root.find(".//sepa:GrpHdr/sepa:NbOfTxs", ns)
        self.assertEqual(nb_of_txs.text, "2")
        
        # Check control sum
        ctrl_sum = root.find(".//sepa:GrpHdr/sepa:CtrlSum", ns)
        self.assertEqual(ctrl_sum.text, "3000.00")


class TestSepaDirectDebit(unittest.TestCase):
    """Test Direct Debit functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sdd = SepaDirectDebit(
            msg_id="TEST-DD-001",
            initiator_name="Test GmbH",
            creation_date_time="2024-02-25T10:00:00",
            sequence_type="RCUR"
        )
        
        self.sdd.add_payment_info(
            payment_info_id="PAY-DD-001",
            creditor_name="Test GmbH",
            creditor_iban="DE89370400440532013000",
            creditor_id="DE98ZZZ09999999999",
            creditor_bic="COBADEFFXXX",
            requested_collection_date="2024-02-26"
        )
    
    def test_init(self):
        """Test initialization."""
        self.assertEqual(self.sdd.msg_id, "TEST-DD-001")
        self.assertEqual(self.sdd.sequence_type, "RCUR")
    
    def test_invalid_sequence_type(self):
        """Test invalid sequence type."""
        with self.assertRaises(SepaValidationError):
            SepaDirectDebit(
                msg_id="TEST-001",
                initiator_name="Test",
                sequence_type="INVALID"
            )
    
    def test_add_transaction(self):
        """Test adding transaction."""
        self.sdd.add_transaction(
            end_to_end_id="E2E-DD-001",
            amount=500.00,
            debtor_name="Kunde Müller",
            debtor_iban="DE75512108001245126199",
            mandate_id="MANDATE-001",
            mandate_signing_date="2023-01-15",
            remittance_info="Rechnung 2024-002"
        )
        
        self.assertEqual(len(self.sdd.transactions), 1)
        trx = self.sdd.transactions[0]
        self.assertEqual(trx["mandate_id"], "MANDATE-001")
        self.assertEqual(trx["mandate_signing_date"], "2023-01-15")
    
    def test_to_xml_structure(self):
        """Test XML structure generation."""
        self.sdd.add_transaction(
            end_to_end_id="E2E-DD-001",
            amount=500.00,
            debtor_name="Kunde Müller",
            debtor_iban="DE75512108001245126199",
            mandate_id="MANDATE-001",
            mandate_signing_date="2023-01-15"
        )
        
        xml_string = self.sdd.to_xml()
        root = ET.fromstring(xml_string)
        
        ns = {"sepa": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.08"}
        
        # Verify sequence type
        seq_tp = root.find(".//sepa:SeqTp/sepa:Cd", ns)
        self.assertIsNotNone(seq_tp)
        self.assertEqual(seq_tp.text, "RCUR")
        
        # Verify mandate info
        mndt_id = root.find(".//sepa:MndtId", ns)
        self.assertIsNotNone(mndt_id)
        self.assertEqual(mndt_id.text, "MANDATE-001")
        
        # Verify creditor scheme ID (in the nested Othr/Id element)
        cdtr_id = root.find(".//sepa:CdtrSchmeId//sepa:Othr/sepa:Id", ns)
        self.assertIsNotNone(cdtr_id)
        self.assertEqual(cdtr_id.text, "DE98ZZZ09999999999")
    
    def test_to_xml_no_payment_info(self):
        """Test XML generation without payment info."""
        empty_sdd = SepaDirectDebit(
            msg_id="TEST-002",
            initiator_name="Test GmbH"
        )
        with self.assertRaises(SepaValidationError):
            empty_sdd.to_xml()


class TestCLI(unittest.TestCase):
    """Test command-line interface."""
    
    def test_cli_validation_valid(self):
        """Test CLI validation with valid XML."""
        sct = SepaCreditTransfer(
            msg_id="CLI-TEST",
            initiator_name="Test GmbH"
        )
        sct.add_payment_info(
            payment_info_id="PAY-001",
            debtor_name="Test",
            debtor_iban="DE89370400440532013000"
        )
        sct.add_transaction(
            end_to_end_id="E2E-001",
            amount=100.00,
            creditor_name="Creditor",
            creditor_iban="DE75512108001245126199"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            temp_path = f.name
        
        try:
            sct.to_file(temp_path)
            
            # Import and test CLI
            import subprocess
            result = subprocess.run(
                ['python3', 'sepa_generator.py', '--validate', temp_path],
                capture_output=True,
                text=True
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("valid XML", result.stdout)
        finally:
            os.unlink(temp_path)


class TestIntegration(unittest.TestCase):
    """Integration tests with realistic scenarios."""
    
    def test_full_credit_transfer_workflow(self):
        """Test complete credit transfer workflow."""
        sct = SepaCreditTransfer(
            msg_id="PAYRUN-20240225-001",
            initiator_name="Musterfirma GmbH"
        )
        
        sct.add_payment_info(
            payment_info_id="BATCH-001",
            debtor_name="Musterfirma GmbH",
            debtor_iban="DE89370400440532013000",
            debtor_bic="COBADEFFXXX",
            requested_execution_date="2024-02-26"
        )
        
        # Add multiple supplier payments
        suppliers = [
            ("Lieferant A GmbH", "DE75512108001245126199", "INGDDEFFXXX", 5000.00, "Rechnung 1001"),
            ("Lieferant B KG", "DE12500105170648489890", "INGDDEFFXXX", 3200.50, "Rechnung 1002"),
            ("Dienstleister C", "DE89370400440532013001", "COBADEFFXXX", 899.99, "Rechnung 1003"),
        ]
        
        for i, (name, iban, bic, amount, ref) in enumerate(suppliers, 1):
            sct.add_transaction(
                end_to_end_id=f"E2E-20240225-{i:04d}",
                amount=amount,
                creditor_name=name,
                creditor_iban=iban,
                creditor_bic=bic,
                remittance_info=ref
            )
        
        xml_string = sct.to_xml()
        root = ET.fromstring(xml_string)
        ns = {"sepa": "urn:iso:std:iso:20022:tech:xsd:pain.001.001:09"}
        
        # Verify totals
        ctrl_sum = root.find(".//{urn:iso:std:iso:20022:tech:xsd:pain.001.001.09}GrpHdr/{urn:iso:std:iso:20022:tech:xsd:pain.001.001.09}CtrlSum")
        self.assertIsNotNone(ctrl_sum)
        self.assertEqual(ctrl_sum.text, "9100.49")
    
    def test_full_direct_debit_workflow(self):
        """Test complete direct debit workflow."""
        sdd = SepaDirectDebit(
            msg_id="DD-20240225-001",
            initiator_name="Musterfirma GmbH",
            sequence_type="RCUR"
        )
        
        sdd.add_payment_info(
            payment_info_id="DD-BATCH-001",
            creditor_name="Musterfirma GmbH",
            creditor_iban="DE89370400440532013000",
            creditor_id="DE98ZZZ09999999999",
            creditor_bic="COBADEFFXXX",
            requested_collection_date="2024-02-28"
        )
        
        # Add customer direct debits
        customers = [
            ("Karl Müller", "DE75512108001245126199", "MANDATE-001", "2023-01-01", 99.99),
            ("Anna Schmidt", "DE12500105170648489890", "MANDATE-002", "2023-02-15", 149.50),
        ]
        
        for i, (name, iban, mandate_id, mandate_date, amount) in enumerate(customers, 1):
            sdd.add_transaction(
                end_to_end_id=f"E2E-DD-20240225-{i:04d}",
                amount=amount,
                debtor_name=name,
                debtor_iban=iban,
                mandate_id=mandate_id,
                mandate_signing_date=mandate_date,
                remittance_info=f"Rechnung {1000 + i}"
            )
        
        xml_string = sdd.to_xml()
        root = ET.fromstring(xml_string)
        
        # Verify structure
        ns = {"sepa": "urn:iso:std:iso:20022:tech:xsd:pain.008.001.08"}
        nb_of_txs = root.find(".//sepa:NbOfTxs", ns)
        self.assertEqual(nb_of_txs.text, "2")


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestValidationFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestSepaCreditTransfer))
    suite.addTests(loader.loadTestsFromTestCase(TestSepaDirectDebit))
    suite.addTests(loader.loadTestsFromTestCase(TestCLI))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_tests())
