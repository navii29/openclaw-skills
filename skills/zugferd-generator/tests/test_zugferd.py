#!/usr/bin/env python3
"""
Tests für ZUGFeRD Generator
"""

import unittest
import json
import os
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zugferd_generator import (
    ZUGFeRDGenerator, Invoice, InvoiceItem, Party, Address
)


class TestInvoiceItem(unittest.TestCase):
    """Tests für InvoiceItem"""
    
    def test_line_total_calculation(self):
        item = InvoiceItem(
            description="Test",
            quantity=2,
            unit="C62",
            price=100.00,
            vat_rate=19
        )
        self.assertEqual(item.line_total, 200.00)
    
    def test_vat_calculation(self):
        item = InvoiceItem(
            description="Test",
            quantity=1,
            unit="C62",
            price=100.00,
            vat_rate=19
        )
        self.assertEqual(item.vat_amount, 19.00)


class TestInvoice(unittest.TestCase):
    """Tests für Invoice"""
    
    def setUp(self):
        self.seller = Party(
            name="Test GmbH",
            street="Teststraße 1",
            zip="12345",
            city="Berlin",
            vat_id="DE123456789"
        )
        self.buyer = Party(
            name="Kunde AG",
            street="Kundenweg 5",
            zip="54321",
            city="München",
            vat_id="DE987654321"
        )
        self.items = [
            InvoiceItem(description="Item 1", quantity=1, price=100.00, vat_rate=19),
            InvoiceItem(description="Item 2", quantity=2, price=50.00, vat_rate=19)
        ]
    
    def test_subtotal_calculation(self):
        invoice = Invoice(
            invoice_number="RE-001",
            invoice_date="2025-02-25",
            seller=self.seller,
            buyer=self.buyer,
            items=self.items
        )
        self.assertEqual(invoice.subtotal, 200.00)
    
    def test_total_vat_calculation(self):
        invoice = Invoice(
            invoice_number="RE-001",
            invoice_date="2025-02-25",
            seller=self.seller,
            buyer=self.buyer,
            items=self.items
        )
        self.assertEqual(invoice.total_vat, 38.00)
    
    def test_total_calculation(self):
        invoice = Invoice(
            invoice_number="RE-001",
            invoice_date="2025-02-25",
            seller=self.seller,
            buyer=self.buyer,
            items=self.items
        )
        self.assertEqual(invoice.total, 238.00)


class TestZUGFeRDGenerator(unittest.TestCase):
    """Tests für ZUGFeRDGenerator"""
    
    def setUp(self):
        self.generator = ZUGFeRDGenerator()
        self.seller = Party(
            name="Navii Automation GmbH",
            street="Musterstraße 1",
            zip="12345",
            city="Berlin",
            country="DE",
            vat_id="DE123456789",
            tax_number="1234567890"
        )
        self.buyer = Party(
            name="Max Mustermann GmbH",
            street="Beispielweg 5",
            zip="54321",
            city="München",
            country="DE",
            vat_id="DE987654321",
            buyer_reference="MAX-12345"
        )
    
    def test_generate_xml_structure(self):
        invoice = Invoice(
            invoice_number="RE-2025-001",
            invoice_date="2025-02-25",
            due_date="2025-03-25",
            seller=self.seller,
            buyer=self.buyer,
            items=[
                InvoiceItem(description="Test Product", quantity=1, price=100.00, vat_rate=19)
            ]
        )
        
        xml = self.generator.generate_xml(invoice)
        
        # Prüfe XML-Struktur
        self.assertIn('<rsm:CrossIndustryInvoice', xml)
        self.assertIn('</rsm:CrossIndustryInvoice>', xml)
        self.assertIn('RE-2025-001', xml)
        self.assertIn('Navii Automation GmbH', xml)
        self.assertIn('Max Mustermann GmbH', xml)
        self.assertIn('Test Product', xml)
    
    def test_generate_zugferd(self):
        invoice = Invoice(
            invoice_number="RE-2025-001",
            invoice_date="2025-02-25",
            seller=self.seller,
            buyer=self.buyer,
            items=[
                InvoiceItem(description="Test", quantity=1, price=100.00, vat_rate=19)
            ]
        )
        
        zugferd_bytes = self.generator.generate_zugferd(invoice)
        
        # Prüfe ZIP-Struktur
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as f:
            f.write(zugferd_bytes)
            temp_path = f.name
        
        try:
            with zipfile.ZipFile(temp_path, 'r') as zf:
                files = zf.namelist()
                self.assertIn('zugferd-invoice.xml', files)
                self.assertIn('INFO.txt', files)
                
                # Prüfe XML-Inhalt
                xml_content = zf.read('zugferd-invoice.xml').decode('utf-8')
                self.assertIn('RE-2025-001', xml_content)
        finally:
            os.unlink(temp_path)
    
    def test_validate_invoice_valid(self):
        invoice = Invoice(
            invoice_number="RE-001",
            invoice_date="2025-02-25",
            seller=self.seller,
            buyer=self.buyer,
            items=[
                InvoiceItem(description="Test", quantity=1, price=100.00, vat_rate=19)
            ]
        )
        
        result = self.generator.validate_invoice(invoice)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_validate_invoice_invalid(self):
        invoice = Invoice(
            invoice_number="",
            invoice_date="",
            seller=None,
            buyer=None,
            items=[]
        )
        
        result = self.generator.validate_invoice(invoice)
        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)
    
    def test_invoice_from_json(self):
        json_data = {
            "invoice_number": "RE-JSON-001",
            "invoice_date": "2025-02-25",
            "seller": {
                "name": "JSON Seller",
                "street": "JSON Street 1",
                "zip": "11111",
                "city": "JSON City",
                "vat_id": "DE111111111"
            },
            "buyer": {
                "name": "JSON Buyer",
                "street": "Buyer Street 5",
                "zip": "22222",
                "city": "Buyer City"
            },
            "items": [
                {
                    "description": "JSON Item",
                    "quantity": 2,
                    "unit": "C62",
                    "price": 50.00,
                    "vat_rate": 19
                }
            ]
        }
        
        invoice = ZUGFeRDGenerator.invoice_from_json(json_data)
        
        self.assertEqual(invoice.invoice_number, "RE-JSON-001")
        self.assertEqual(invoice.seller.name, "JSON Seller")
        self.assertEqual(invoice.buyer.name, "JSON Buyer")
        self.assertEqual(len(invoice.items), 1)
        self.assertEqual(invoice.items[0].line_total, 100.00)


class TestCLI(unittest.TestCase):
    """Tests für CLI"""
    
    def test_cli_json_input(self):
        # Erstelle temporäre JSON-Datei
        json_data = {
            "invoice_number": "RE-CLI-001",
            "invoice_date": "2025-02-25",
            "seller": {
                "name": "CLI Seller",
                "street": "CLI Street",
                "zip": "12345",
                "city": "CLI City",
                "vat_id": "DE123456789"
            },
            "buyer": {
                "name": "CLI Buyer",
                "street": "Buyer Street",
                "zip": "54321",
                "city": "Buyer City"
            },
            "items": [
                {
                    "description": "CLI Item",
                    "quantity": 1,
                    "price": 100.00,
                    "vat_rate": 19
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            json_path = f.name
        
        output_path = json_path.replace('.json', '_zugferd.zip')
        
        try:
            # Führe CLI aus
            exit_code = os.system(f'python3 {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/zugferd_generator.py --input {json_path} --output {output_path}')
            self.assertEqual(exit_code, 0)
            self.assertTrue(os.path.exists(output_path))
            
            # Prüfe ZIP-Inhalt
            with zipfile.ZipFile(output_path, 'r') as zf:
                self.assertIn('zugferd-invoice.xml', zf.namelist())
        finally:
            if os.path.exists(json_path):
                os.unlink(json_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
