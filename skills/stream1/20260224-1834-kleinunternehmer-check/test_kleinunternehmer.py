"""
Tests für Kleinunternehmer-Checker
"""

import unittest
from datetime import date
from kleinunternehmer_check import (
    KleinunternehmerChecker, 
    check_kleinunternehmer,
    KleinunternehmerStatus
)


class TestKleinunternehmerChecker(unittest.TestCase):
    
    def setUp(self):
        self.checker = KleinunternehmerChecker()
    
    def test_echter_kleinunternehmer(self):
        """Test: Echter Kleinunternehmer (unter beiden Grenzen)"""
        status = self.checker.check_status(
            umsatz_vorjahr=20_000,
            umsatz_laufendes_jahr=15_000,
            aktuelles_datum=date(2025, 6, 30)
        )
        self.assertTrue(status.ist_kleinunternehmer)
        self.assertEqual(len(status.warnungen), 0)
    
    def test_vorjahr_ueberschritten(self):
        """Test: Vorjahresgrenze überschritten"""
        status = self.checker.check_status(
            umsatz_vorjahr=25_000,
            umsatz_laufendes_jahr=15_000,
            aktuelles_datum=date(2025, 6, 30)
        )
        self.assertFalse(status.ist_kleinunternehmer)
        self.assertTrue(any('Vorjahresumsatz' in w for w in status.warnungen))
    
    def test_prognose_ueberschritten(self):
        """Test: Prognose überschreitet Grenze"""
        # An Tag 180: 30.000 € Umsatz = ~60.000 € Prognose
        status = self.checker.check_status(
            umsatz_vorjahr=20_000,
            umsatz_laufendes_jahr=30_000,
            aktuelles_datum=date(2025, 6, 30)  # Tag ~180
        )
        self.assertFalse(status.ist_kleinunternehmer)
    
    def test_grenzwert_warnung(self):
        """Test: Warnung bei Annäherung an Grenze"""
        status = self.checker.check_status(
            umsatz_vorjahr=20_000,
            umsatz_laufendes_jahr=24_000,  # An Tag 180 = ~48.000 € Prognose
            aktuelles_datum=date(2025, 6, 30)
        )
        # Sollte nicht warnen, da unter 90%
        self.assertTrue(status.ist_kleinunternehmer)
    
    def test_prognose_berechnung(self):
        """Test: Prognose-Berechnung"""
        # Tag 180, 25.000 € Umsatz
        prognose = self.checker._berechne_prognose(25_000, date(2025, 6, 30))
        # Erwartet: 25.000 / 180 * 365 = ~50.694
        self.assertGreater(prognose, 50_000)
    
    def test_schaltjahr(self):
        """Test: Schaltjahr-Berücksichtigung"""
        self.assertTrue(self.checker._ist_schaltjahr(2024))
        self.assertFalse(self.checker._ist_schaltjahr(2025))
        self.assertTrue(self.checker._ist_schaltjahr(2000))
    
    def test_rechnung_kleinunternehmer(self):
        """Test: Rechnungsberechnung Kleinunternehmer"""
        result = self.checker.calculate_rechnung(100, True)
        self.assertEqual(result['brutto'], 100)
        self.assertEqual(result['steuersatz'], 0)
        self.assertIn('Kleinunternehmer', result['hinweis'])
    
    def test_rechnung_normal(self):
        """Test: Rechnungsberechnung normal (mit USt)"""
        result = self.checker.calculate_rechnung(100, False)
        self.assertEqual(result['netto'], 100)
        self.assertEqual(result['steuersatz'], 19)
        self.assertEqual(result['steuerbetrag'], 19)
        self.assertEqual(result['brutto'], 119)
    
    def test_check_monatsgrenze(self):
        """Test: Monatliche Grenzprüfung"""
        # 4.500 €/Monat = 54.000 €/Jahr
        result = self.checker.check_monatsgrenze(4_500)
        self.assertTrue(result['grenze_erreicht'])
        self.assertEqual(result['warnstufe'], 'kritisch')


class TestQuickFunction(unittest.TestCase):
    """Test der Convenience-Funktion"""
    
    def test_check_kleinunternehmer(self):
        result = check_kleinunternehmer(20_000, 15_000)
        self.assertIn('ist_kleinunternehmer', result)
        self.assertIn('begruendung', result)
        self.assertIn('handlungsempfehlung', result)


if __name__ == '__main__':
    unittest.main()
