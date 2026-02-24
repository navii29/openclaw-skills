"""
Tests für USt Calculator
"""

import unittest
from ust_calculator import UStCalculator, calculate_vat, UStSatz


class TestUStCalculator(unittest.TestCase):
    
    def setUp(self):
        self.calc = UStCalculator()
    
    def test_netto_zu_brutto_19_prozent(self):
        """Test Netto zu Brutto mit 19%"""
        result = self.calc.netto_zu_brutto(100.0, 19.0)
        self.assertEqual(result.netto, 100.0)
        self.assertEqual(result.ust_betrag, 19.0)
        self.assertEqual(result.brutto, 119.0)
        self.assertEqual(result.steuersatz, 19.0)
    
    def test_netto_zu_brutto_7_prozent(self):
        """Test Netto zu Brutto mit 7%"""
        result = self.calc.netto_zu_brutto(100.0, 7.0)
        self.assertEqual(result.netto, 100.0)
        self.assertEqual(result.ust_betrag, 7.0)
        self.assertEqual(result.brutto, 107.0)
    
    def test_brutto_zu_netto_19_prozent(self):
        """Test Brutto zu Netto mit 19%"""
        result = self.calc.brutto_zu_netto(119.0, 19.0)
        self.assertEqual(result.brutto, 119.0)
        self.assertEqual(result.ust_betrag, 19.0)
        self.assertEqual(result.netto, 100.0)
    
    def test_brutto_zu_netto_7_prozent(self):
        """Test Brutto zu Netto mit 7%"""
        result = self.calc.brutto_zu_netto(107.0, 7.0)
        self.assertEqual(result.brutto, 107.0)
        self.assertEqual(result.ust_betrag, 7.0)
        self.assertEqual(result.netto, 100.0)
    
    def test_skonto_berechnen(self):
        """Test Skonto-Berechnung"""
        result = self.calc.skonto_berechnen(119.0, 2.0)
        self.assertEqual(result['brutto'], 119.0)
        self.assertEqual(result['skonto_prozent'], 2.0)
        self.assertEqual(result['skonto_betrag'], 2.38)
        self.assertEqual(result['zahlungsbetrag'], 116.62)
    
    def test_rabatt_berechnen(self):
        """Test Rabatt-Berechnung"""
        result = self.calc.rabatt_berechnen(100.0, 10.0, 19.0)
        self.assertEqual(result['original_netto'], 100.0)
        self.assertEqual(result['rabatt_prozent'], 10.0)
        self.assertEqual(result['rabatt_betrag'], 10.0)
        self.assertEqual(result['netto_nach_rabatt'], 90.0)
        self.assertEqual(result['ust'], 17.1)
        self.assertEqual(result['brutto'], 107.1)
    
    def test_mehrwertsteuer_differenz(self):
        """Test USt-Differenz"""
        result = self.calc.mehrwertsteuer_differenz(100.0, 200.0, 19.0)
        self.assertEqual(result['differenz_netto'], 100.0)
        self.assertEqual(result['differenz_ust'], 19.0)
    
    def test_get_steuer_satz_fuer_produkt(self):
        """Test Steuersatz nach Produktkategorie"""
        self.assertEqual(self.calc.get_steuer_satz_für_produkt('standard'), 19.0)
        self.assertEqual(self.calc.get_steuer_satz_für_produkt('lebensmittel'), 7.0)
        self.assertEqual(self.calc.get_steuer_satz_für_produkt('buecher'), 7.0)
        self.assertEqual(self.calc.get_steuer_satz_für_produkt('steuerfrei'), 0.0)
        self.assertEqual(self.calc.get_steuer_satz_für_produkt('unbekannt'), 19.0)  # Default
    
    def test_format_euro(self):
        """Test Euro-Formatierung"""
        self.assertEqual(self.calc.format_euro(1000.50), "1.000,50 €")
        self.assertEqual(self.calc.format_euro(100.00), "100,00 €")
    
    def test_rechnungsposition(self):
        """Test Rechnungsposition"""
        result = self.calc.rechnungsposition(5, 19.99, 19.0)
        self.assertEqual(result['menge'], 5)
        self.assertEqual(result['einzelpreis_netto'], 19.99)
        self.assertEqual(result['gesamt_netto'], 99.95)
        self.assertEqual(result['ust_betrag'], 18.99)  # 99.95 * 0.19 = 18.9905
        self.assertEqual(result['gesamt_brutto'], 118.94)
    
    def test_rechnungsposition_mit_rabatt(self):
        """Test Rechnungsposition mit Rabatt"""
        result = self.calc.rechnungsposition(10, 50.0, 19.0, 10.0)
        self.assertEqual(result['gesamt_netto'], 500.0)
        self.assertEqual(result['rabatt_betrag'], 50.0)
        self.assertEqual(result['netto_nach_rabatt'], 450.0)


class TestQuickCalculation(unittest.TestCase):
    """Test Convenience-Funktionen"""
    
    def test_calculate_vat_netto(self):
        """Test calculate_vat mit Netto"""
        result = calculate_vat(net_amount=100, vat_rate=19)
        self.assertEqual(result['netto'], 100)
        self.assertEqual(result['ust_betrag'], 19)
        self.assertEqual(result['brutto'], 119)
    
    def test_calculate_vat_brutto(self):
        """Test calculate_vat mit Brutto"""
        result = calculate_vat(gross_amount=119, vat_rate=19)
        self.assertEqual(result['brutto'], 119)
        self.assertEqual(result['ust_betrag'], 19)
        self.assertEqual(result['netto'], 100)
    
    def test_calculate_vat_error(self):
        """Test calculate_vat ohne Parameter"""
        with self.assertRaises(ValueError):
            calculate_vat()


class TestRundung(unittest.TestCase):
    """Test Rundungsverhalten"""
    
    def test_rundung_2_nachkomma(self):
        """Test Standard-Rundung"""
        calc = UStCalculator(rundung=2)
        result = calc.netto_zu_brutto(100.555, 19.0)
        self.assertEqual(result.ust_betrag, 19.11)  # 100.555 * 0.19 = 19.10545
        self.assertEqual(result.brutto, 119.67)


if __name__ == '__main__':
    unittest.main()
