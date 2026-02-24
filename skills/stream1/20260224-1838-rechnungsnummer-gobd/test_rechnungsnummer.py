"""
Tests für GoBD Rechnungsnummer Generator
"""

import unittest
import os
import tempfile
import json
from datetime import datetime
from rechnungsnummer_gobd import (
    GoBDRechnungsnummer, 
    RechnungsnummerConfig,
    erstelle_rechnungsnummer
)


class TestRechnungsnummerConfig(unittest.TestCase):
    
    def test_default_config(self):
        """Test Standard-Konfiguration"""
        config = RechnungsnummerConfig()
        self.assertEqual(config.prefix, "RE")
        self.assertEqual(config.jahr_format, "YYYY")
        self.assertEqual(config.trennzeichen, "-")
        self.assertEqual(config.ziffern, 5)
    
    def test_invalid_jahr_format(self):
        """Test ungültiges Jahr-Format"""
        with self.assertRaises(ValueError):
            RechnungsnummerConfig(jahr_format="INVALID")


class TestGoBDRechnungsnummer(unittest.TestCase):
    
    def setUp(self):
        """Erstelle temporäres Verzeichnis für Tests"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = RechnungsnummerConfig()
        self.generator = GoBDRechnungsnummer(self.config, self.temp_dir)
    
    def tearDown(self):
        """Räume temporäre Dateien auf"""
        counter_file = os.path.join(self.temp_dir, "rechnungsnummern_counter.json")
        if os.path.exists(counter_file):
            os.remove(counter_file)
        os.rmdir(self.temp_dir)
    
    def test_generiere_standard(self):
        """Test Standard-Nummerngenerierung"""
        nummer = self.generator.generiere()
        self.assertTrue(nummer.startswith("RE-"))
        self.assertIn(str(datetime.now().year), nummer)
    
    def test_generiere_fortlaufend(self):
        """Test fortlaufende Nummern"""
        nummer1 = self.generator.generiere()
        nummer2 = self.generator.generiere()
        
        # Extrahiere Nummernteil
        nr1 = int(nummer1.split("-")[-1])
        nr2 = int(nummer2.split("-")[-1])
        
        self.assertEqual(nr2, nr1 + 1)
    
    def test_generiere_ohne_jahr(self):
        """Test ohne Jahresangabe"""
        config = RechnungsnummerConfig(jahr_format="", prefix="INV")
        generator = GoBDRechnungsnummer(config, self.temp_dir)
        nummer = generator.generiere()
        
        self.assertTrue(nummer.startswith("INV-"))
        self.assertEqual(len(nummer.split("-")), 2)  # INV-00001
    
    def test_validiere_gueltig(self):
        """Test Validierung gültiger Nummern"""
        result = self.generator.validiere("RE-2025-00001")
        self.assertTrue(result['gueltig'])
    
    def test_validiere_leer(self):
        """Test Validierung leerer Nummer"""
        result = self.generator.validiere("")
        self.assertFalse(result['gueltig'])
        self.assertIn("Rechnungsnummer ist leer", result['fehler'])
    
    def test_validiere_ungueltige_zeichen(self):
        """Test Validierung ungültiger Zeichen"""
        result = self.generator.validiere("RE@2025#00001")
        self.assertFalse(result['gueltig'])
        self.assertTrue(any('Ungültige Zeichen' in f for f in result['fehler']))
    
    def test_validiere_zu_lang(self):
        """Test Validierung zu langer Nummer"""
        result = self.generator.validiere("RE-" + "0" * 50)
        self.assertFalse(result['gueltig'])
        self.assertTrue(any('zu lang' in f for f in result['fehler']))
    
    def test_naechste_nummer(self):
        """Test Abruf nächster Nummer"""
        nummer1 = self.generator.generiere()
        naechste = self.generator.get_naechste_nummer()
        nummer2 = self.generator.generiere()
        
        self.assertEqual(naechste, int(nummer2.split("-")[-1]))
    
    def test_statistik(self):
        """Test Statistik-Funktion"""
        self.generator.generiere()
        self.generator.generiere()
        
        stats = self.generator.get_statistik()
        self.assertEqual(stats['anzahl_ausgegeben'], 2)
        self.assertEqual(stats['letzte_nummer'], 2)


class TestSchnellfunktion(unittest.TestCase):
    """Test der Convenience-Funktion"""
    
    def test_erstelle_rechnungsnummer(self):
        """Test Schnell-Funktion"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nummer = erstelle_rechnungsnummer("RE-YYYY-NNNNN", tmpdir)
            self.assertTrue(nummer.startswith("RE-"))


if __name__ == '__main__':
    unittest.main()
