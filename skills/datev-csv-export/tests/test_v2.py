#!/usr/bin/env python3
"""
Tests für DATEV-Export v2.0
"""

import unittest
import tempfile
import json
import os
from decimal import Decimal

from datev_export_v2 import (
    DATEVExporter, Buchungssatz, SmartAccountSuggestor
)


class TestBuchungssatz(unittest.TestCase):
    """Tests für Buchungssatz"""
    
    def test_datum_normalization(self):
        """Test Datumsnormalisierung"""
        b = Buchungssatz(
            datum="15.02.2025",
            konto=8400,
            gegenkonto=1200,
            bu_schluessel="",
            umsatz=100.00,
            soll_haben="H"
        )
        self.assertEqual(b.datum, "150225")
    
    def test_umsatz_formatting(self):
        """Test Umsatz-Formatierung"""
        b = Buchungssatz(
            datum="150225",
            konto=8400,
            gegenkonto=1200,
            bu_schluessel="",
            umsatz=1234.56,
            soll_haben="H"
        )
        formatted = b._format_umsatz()
        self.assertEqual(formatted, "1234,56")


class TestSmartAccountSuggestor(unittest.TestCase):
    """Tests für SmartAccountSuggestor"""
    
    def setUp(self):
        self.suggestor = SmartAccountSuggestor(learning_file="/tmp/test_learning.json")
    
    def test_suggest_miete(self):
        """Test Vorschlag für Miete"""
        konto, conf = self.suggestor.suggest_account("Miete Büro")
        self.assertEqual(konto, 7200)
        self.assertGreater(conf, 0.8)
    
    def test_suggest_werbung(self):
        """Test Vorschlag für Werbung"""
        konto, conf = self.suggestor.suggest_account("Google Ads Kampagne")
        self.assertEqual(konto, 7700)
    
    def test_suggest_reise(self):
        """Test Vorschlag für Reisekosten"""
        konto, conf = self.suggestor.suggest_account("Hotel Buchung Messe")
        self.assertEqual(konto, 7800)
    
    def test_learning(self):
        """Test Lernfunktion"""
        self.suggestor.learn("SEO Optimierung", 7700)
        konto, conf = self.suggestor.suggest_account("SEO Optimierung")
        self.assertEqual(konto, 7700)
        self.assertGreater(conf, 0.9)


class TestDATEVExporter(unittest.TestCase):
    """Tests für DATEVExporter"""
    
    def setUp(self):
        self.exporter = DATEVExporter()
    
    def test_add_buchung(self):
        """Test Buchung hinzufügen"""
        b = Buchungssatz(
            datum="150225",
            konto=8400,
            gegenkonto=1200,
            bu_schluessel="",
            umsatz=100.00,
            soll_haben="H"
        )
        self.exporter.add_buchung(b)
        self.assertEqual(len(self.exporter.buchungen), 1)
    
    def test_add_rechnung(self):
        """Test Rechnung mit USt-Aufteilung"""
        self.exporter.add_rechnung(
            datum="15.02.2025",
            brutto=119.00,
            ust_satz=19,
            konto=8400,
            gegenkonto=1400,
            text="Test"
        )
        
        # Sollte 2 Buchungen erzeugen (Netto + USt)
        self.assertEqual(len(self.exporter.buchungen), 2)
    
    def test_add_rechnung_smart(self):
        """Test smarte Rechnungsbuchung"""
        exporter = DATEVExporter(smart_suggest=True)
        konto, conf = exporter.add_rechnung_smart(
            datum="15.02.2025",
            brutto=1000.00,
            text="Miete",
            ust_satz=19
        )
        
        self.assertEqual(konto, 7200)  # Miete-Konto
        self.assertGreater(conf, 0.5)
    
    def test_export(self):
        """Test CSV-Export"""
        self.exporter.add_buchung(Buchungssatz(
            datum="150225",
            konto=8400,
            gegenkonto=1200,
            bu_schluessel="",
            umsatz=100.00,
            soll_haben="H",
            buchungstext="Test"
        ))
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            result = self.exporter.export(temp_path)
            self.assertTrue(os.path.exists(result))
            
            # Prüfe Datei-Inhalt
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("Datum;Konto;Gegenkonto", content)
                self.assertIn("8400", content)
        finally:
            os.unlink(temp_path)
    
    def test_get_stats(self):
        """Test Statistiken"""
        self.exporter.add_buchung(Buchungssatz(
            datum="150225",
            konto=8400,
            gegenkonto=1200,
            bu_schluessel="",
            umsatz=100.00,
            soll_haben="H"
        ))
        
        stats = self.exporter.get_stats()
        self.assertEqual(stats['total_buchungen'], 1)
        self.assertEqual(stats['unique_konten'], 1)
    
    def test_validate_valid(self):
        """Test Validierung (gültig)"""
        self.exporter.add_buchung(Buchungssatz(
            datum="150225",
            konto=8400,
            gegenkonto=1200,
            bu_schluessel="",
            umsatz=100.00,
            soll_haben="H"
        ))
        
        validation = self.exporter.validate()
        self.assertTrue(validation['valid'])
    
    def test_validate_invalid(self):
        """Test Validierung (ungültig)"""
        self.exporter.add_buchung(Buchungssatz(
            datum="150225",
            konto=8400,
            gegenkonto=8400,  # Gleiches Konto = Fehler
            bu_schluessel="",
            umsatz=100.00,
            soll_haben="H"
        ))
        
        validation = self.exporter.validate()
        self.assertFalse(validation['valid'])
        self.assertGreater(len(validation['errors']), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
