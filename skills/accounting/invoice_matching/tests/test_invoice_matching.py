"""
Unit Tests für Rechnungs-Matching
"""

import pytest
import os
import tempfile
import csv
from decimal import Decimal

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from invoice_matching import (
    Rechnung,
    Zahlung,
    MatchErgebnis,
    InvoiceMatcher,
    DATEVExporter,
    MatchingError,
    DuplicatePaymentError,
    InvalidFormatError,
    quick_match,
)


class TestRechnung:
    """Tests für Rechnungs-Klasse"""
    
    def test_rechnung_creation(self):
        """Test: Rechnung wird korrekt erstellt"""
        r = Rechnung(
            nr="RE-001",
            kunde_id="K001",
            betrag=1190.00,
            datum="2024-01-01",
            faellig="2024-01-31"
        )
        assert r.nr == "RE-001"
        assert r.kunde_id == "K001"
        assert r.betrag == Decimal("1190.00")
        assert r.status == "offen"
    
    def test_rechnung_restbetrag(self):
        """Test: Restbetrag wird korrekt berechnet"""
        r = Rechnung(nr="RE-001", kunde_id="K001", betrag=1000.00, datum="2024-01-01")
        assert r.restbetrag == Decimal("1000.00")
        
        r.zahlung_hinzufuegen(Decimal("500.00"))
        assert r.restbetrag == Decimal("500.00")
    
    def test_rechnung_teilbezahlt(self):
        """Test: Teilbezahlung wird erkannt"""
        r = Rechnung(nr="RE-001", kunde_id="K001", betrag=1000.00, datum="2024-01-01")
        assert not r.ist_teilbezahlt
        
        r.zahlung_hinzufuegen(Decimal("500.00"))
        assert r.ist_teilbezahlt
        assert r.status == "teilbezahlt"
    
    def test_rechnung_vollbezahlt(self):
        """Test: Vollständige Bezahlung"""
        r = Rechnung(nr="RE-001", kunde_id="K001", betrag=1000.00, datum="2024-01-01")
        r.zahlung_hinzufuegen(Decimal("1000.00"))
        
        assert r.status == "bezahlt"
        assert not r.ist_teilbezahlt
        assert r.restbetrag == Decimal("0.00")
    
    def test_rechnung_ueberzahlung(self):
        """Test: Überzahlung"""
        r = Rechnung(nr="RE-001", kunde_id="K001", betrag=1000.00, datum="2024-01-01")
        r.zahlung_hinzufuegen(Decimal("1200.00"))
        
        assert r.status == "bezahlt"
        assert r.bezahlt == Decimal("1200.00")


class TestZahlung:
    """Tests für Zahlungs-Klasse"""
    
    def test_zahlung_creation(self):
        """Test: Zahlung wird korrekt erstellt"""
        z = Zahlung(
            datum="2024-01-15",
            betrag=1190.00,
            zweck="Rechnung RE-001",
            referenz="K001-20240115"
        )
        assert z.datum == "2024-01-15"
        assert z.betrag == Decimal("1190.00")
        assert not z.gematcht
    
    def test_extrahiere_rechnungsnr_re_dash(self):
        """Test: Rechnungsnummer mit RE- extrahieren"""
        z = Zahlung(datum="2024-01-15", betrag=100.00, zweck="Zahlung fuer RE-001")
        assert z.extrahiere_rechnungsnr() == "RE-001"
    
    def test_extrahiere_rechnungsnr_re_nodash(self):
        """Test: Rechnungsnummer mit RE ohne Bindestrich"""
        z = Zahlung(datum="2024-01-15", betrag=100.00, zweck="RE001 bezahlt")
        assert z.extrahiere_rechnungsnr() == "RE001"
    
    def test_extrahiere_rechnungsnr_rechnung(self):
        """Test: Rechnungsnummer mit 'Rechnung' extrahieren"""
        z = Zahlung(datum="2024-01-15", betrag=100.00, zweck="Rechnung: 123")
        assert z.extrahiere_rechnungsnr() == "Rechnung: 123"
    
    def test_extrahiere_rechnungsnr_rnr(self):
        """Test: Rechnungsnummer mit Rnr extrahieren"""
        z = Zahlung(datum="2024-01-15", betrag=100.00, zweck="Rnr: 456")
        assert z.extrahiere_rechnungsnr() == "Rnr: 456"
    
    def test_extrahiere_rechnungsnr_nicht_gefunden(self):
        """Test: Keine Rechnungsnummer gefunden"""
        z = Zahlung(datum="2024-01-15", betrag=100.00, zweck="Danke fuer den Einkauf")
        assert z.extrahiere_rechnungsnr() is None
    
    def test_extrahiere_kundenid_k(self):
        """Test: Kunden-ID mit K extrahieren"""
        z = Zahlung(datum="2024-01-15", betrag=100.00, zweck="K001 Zahlung")
        assert z.extrahiere_kundenid() == "K001"
    
    def test_extrahiere_kundenid_kdnr(self):
        """Test: Kunden-ID mit Kd-Nr extrahieren"""
        z = Zahlung(datum="2024-01-15", betrag=100.00, zweck="Kd-Nr: 123")
        assert z.extrahiere_kundenid() == "Kd-Nr: 123"


class TestInvoiceMatcher:
    """Tests für InvoiceMatcher"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.matcher = InvoiceMatcher(
            toleranz_prozent=1.0,
            toleranz_absolut=5.0
        )
    
    def test_lade_rechnungen(self):
        """Test: Rechnungen laden"""
        self.matcher.lade_rechnungen([
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1190.00, 'datum': '2024-01-01'},
            {'nr': 'RE-002', 'kunde_id': 'K002', 'betrag': 595.00, 'datum': '2024-01-05'},
        ])
        
        assert len(self.matcher.rechnungen) == 2
        assert self.matcher.rechnungen[0].nr == "RE-001"
    
    def test_lade_rechnungen_csv_format(self):
        """Test: Rechnungen im CSV-Format laden"""
        self.matcher.lade_rechnungen([
            {'Rechnungsnr': 'RE-001', 'Kundennummer': 'K001', 'Betrag': '1190.00', 'Datum': '2024-01-01'},
        ])
        
        assert len(self.matcher.rechnungen) == 1
        assert self.matcher.rechnungen[0].betrag == Decimal("1190.00")
    
    def test_lade_zahlungen(self):
        """Test: Zahlungen laden"""
        self.matcher.lade_zahlungen([
            {'datum': '2024-01-15', 'betrag': 1190.00, 'zweck': 'RE-001'},
            {'datum': '2024-01-20', 'betrag': 595.00, 'zweck': 'RE-002'},
        ])
        
        assert len(self.matcher.zahlungen) == 2
    
    def test_match_exakt_referenz(self):
        """Test: Exaktes Matching mit Rechnungsnummer"""
        self.matcher.lade_rechnungen([
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1190.00, 'datum': '2024-01-01'},
        ])
        self.matcher.lade_zahlungen([
            {'datum': '2024-01-15', 'betrag': 1190.00, 'zweck': 'Rechnung RE-001'},
        ])
        
        ergebnis = self.matcher.match()
        
        assert ergebnis['stats']['gematcht'] == 1
        assert len(ergebnis['matches']) == 1
        assert ergebnis['matches'][0].methode == 'exakt_referenz'
    
    def test_match_exakt_betrag(self):
        """Test: Exaktes Matching mit Betrag"""
        self.matcher.lade_rechnungen([
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1000.00, 'datum': '2024-01-01'},
        ])
        self.matcher.lade_zahlungen([
            {'datum': '2024-01-15', 'betrag': 1000.00, 'zweck': 'Danke'},
        ])
        
        ergebnis = self.matcher.match()
        
        assert ergebnis['stats']['gematcht'] == 1
        assert ergebnis['matches'][0].methode == 'fuzzy_betrag'
    
    def test_match_mit_toleranz(self):
        """Test: Matching mit Toleranz"""
        self.matcher.lade_rechnungen([
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1000.00, 'datum': '2024-01-01'},
        ])
        # 1% Toleranz = 10 EUR bei 1000 EUR
        self.matcher.lade_zahlungen([
            {'datum': '2024-01-15', 'betrag': 1005.00, 'zweck': 'Danke'},
        ])
        
        ergebnis = self.matcher.match()
        
        assert ergebnis['stats']['gematcht'] == 1
        assert ergebnis['matches'][0].differenz == Decimal("5.00")
    
    def test_match_ausserhalb_toleranz(self):
        """Test: Kein Matching wenn außerhalb Toleranz"""
        self.matcher.lade_rechnungen([
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1000.00, 'datum': '2024-01-01'},
        ])
        # 20 EUR Differenz > 1% (10 EUR) und > 5 EUR
        self.matcher.lade_zahlungen([
            {'datum': '2024-01-15', 'betrag': 1020.00, 'zweck': 'Danke'},
        ])
        
        ergebnis = self.matcher.match()
        
        assert ergebnis['stats']['gematcht'] == 0
        assert len(ergebnis['unmatched_zahlungen']) == 1
    
    def test_match_teilzahlung(self):
        """Test: Teilzahlung erkennen"""
        self.matcher.lade_rechnungen([
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1000.00, 'datum': '2024-01-01'},
        ])
        self.matcher.lade_zahlungen([
            {'datum': '2024-01-15', 'betrag': 500.00, 'zweck': 'RE-001 Anzahlung'},
        ])
        
        ergebnis = self.matcher.match()
        
        assert ergebnis['stats']['gematcht'] == 1
        assert ergebnis['matches'][0].methode == 'teilzahlung'
        
        # Rechnung sollte teilbezahlt sein
        rechnung = self.matcher.rechnungen[0]
        assert rechnung.status == 'teilbezahlt'
        assert rechnung.bezahlt == Decimal("500.00")
    
    def test_match_doppelte_zahlung(self):
        """Test: Doppelte Zahlung erkennen"""
        self.matcher.lade_rechnungen([
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1000.00, 'datum': '2024-01-01'},
        ])
        self.matcher.lade_zahlungen([
            {'datum': '2024-01-15', 'betrag': 1000.00, 'zweck': 'RE-001'},
            {'datum': '2024-01-16', 'betrag': 1000.00, 'zweck': 'RE-001'},  # Doppelte
        ])
        
        ergebnis = self.matcher.match()
        
        assert ergebnis['stats']['doppelte'] == 1
        assert len(ergebnis['doppelte_zahlungen']) == 1
    
    def test_match_mehrere_rechnungen(self):
        """Test: Mehrere Rechnungen und Zahlungen"""
        self.matcher.lade_rechnungen([
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1000.00, 'datum': '2024-01-01'},
            {'nr': 'RE-002', 'kunde_id': 'K002', 'betrag': 2000.00, 'datum': '2024-01-05'},
            {'nr': 'RE-003', 'kunde_id': 'K003', 'betrag': 3000.00, 'datum': '2024-01-10'},
        ])
        self.matcher.lade_zahlungen([
            {'datum': '2024-01-15', 'betrag': 1000.00, 'zweck': 'RE-001'},
            {'datum': '2024-01-20', 'betrag': 2000.00, 'zweck': 'RE-002'},
        ])
        
        ergebnis = self.matcher.match()
        
        assert ergebnis['stats']['gematcht'] == 2
        assert ergebnis['stats']['unmatched'] == 0
        
        # RE-003 sollte noch offen sein
        offene = self.matcher.get_offene_posten()
        assert len(offene) == 1
        assert offene[0].nr == 'RE-003'
    
    def test_get_bericht(self):
        """Test: Bericht generieren"""
        self.matcher.lade_rechnungen([
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1000.00, 'datum': '2024-01-01'},
        ])
        self.matcher.lade_zahlungen([
            {'datum': '2024-01-15', 'betrag': 1000.00, 'zweck': 'RE-001'},
        ])
        
        self.matcher.match()
        bericht = self.matcher.get_bericht()
        
        assert 'MATCHING-BERICHT' in bericht
        assert 'RE-001' in bericht
        assert '1000.00' in bericht


class TestDATEVExporter:
    """Tests für DATEVExporter"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.exporter = DATEVExporter(kontenrahmen='SKR03')
    
    def test_export_csv(self):
        """Test: DATEV-CSV exportieren"""
        matcher = InvoiceMatcher()
        matcher.lade_rechnungen([
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1190.00, 'datum': '2024-01-01'},
        ])
        matcher.lade_zahlungen([
            {'datum': '2024-01-15', 'betrag': 1190.00, 'zweck': 'RE-001'},
        ])
        
        ergebnis = matcher.match()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            self.exporter.export_csv(ergebnis, temp_path)
            
            # Prüfen ob Datei existiert
            assert os.path.exists(temp_path)
            
            # Inhalt prüfen
            with open(temp_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                assert 'Datum' in content
                assert '1200' in content  # Bankkonto
                assert 'RE-001' in content
                assert '1190' in content
        finally:
            os.unlink(temp_path)
    
    def test_export_offene_posten(self):
        """Test: Offene Posten exportieren"""
        rechnungen = [
            Rechnung(nr='RE-001', kunde_id='K001', betrag=1000.00, datum='2024-01-01'),
            Rechnung(nr='RE-002', kunde_id='K002', betrag=2000.00, datum='2024-01-05'),
        ]
        rechnungen[0].zahlung_hinzufuegen(Decimal("500.00"))  # Teilbezahlt
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            self.exporter.export_offene_posten(rechnungen, temp_path)
            
            with open(temp_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                assert 'Rechnungsnr' in content
                assert 'RE-001' in content
                assert 'teilbezahlt' in content
        finally:
            os.unlink(temp_path)
    
    def test_format_datum(self):
        """Test: Datumsformatierung"""
        assert self.exporter._format_datum('2024-01-15') == '15.01.2024'
        assert self.exporter._format_datum('15.01.2024') == '15.01.2024'


class TestQuickMatch:
    """Tests für quick_match Convenience-Funktion"""
    
    def test_quick_match_basic(self):
        """Test: Schnelles Matching"""
        rechnungen = [
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1000.00, 'datum': '2024-01-01'},
            {'nr': 'RE-002', 'kunde_id': 'K002', 'betrag': 2000.00, 'datum': '2024-01-05'},
        ]
        zahlungen = [
            {'datum': '2024-01-15', 'betrag': 1000.00, 'zweck': 'RE-001'},
            {'datum': '2024-01-20', 'betrag': 2000.00, 'zweck': 'RE-002'},
        ]
        
        ergebnis = quick_match(rechnungen, zahlungen)
        
        assert ergebnis['stats']['total_rechnungen'] == 2
        assert ergebnis['stats']['total_zahlungen'] == 2
        assert ergebnis['stats']['gematcht'] == 2
        assert ergebnis['stats']['match_rate'] == 1.0
    
    def test_quick_match_mit_toleranz(self):
        """Test: Schnelles Matching mit Toleranz"""
        rechnungen = [
            {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1000.00, 'datum': '2024-01-01'},
        ]
        zahlungen = [
            {'datum': '2024-01-15', 'betrag': 1003.00, 'zweck': 'RE-001'},
        ]
        
        ergebnis = quick_match(rechnungen, zahlungen, toleranz_prozent=1.0)
        
        assert ergebnis['stats']['gematcht'] == 1


class TestFehlerbehandlung:
    """Tests für Fehlerbehandlung"""
    
    def test_invalid_format_rechnung(self):
        """Test: Ungültiges Rechnungsformat"""
        matcher = InvoiceMatcher()
        
        with pytest.raises(InvalidFormatError):
            matcher.lade_rechnungen([
                {'nr': 'RE-001', 'betrag': 'invalid'},
            ])
    
    def test_invalid_format_zahlung(self):
        """Test: Ungültiges Zahlungsformat"""
        matcher = InvoiceMatcher()
        
        with pytest.raises(InvalidFormatError):
            matcher.lade_zahlungen([
                {'datum': '2024-01-15', 'betrag': 'invalid'},
            ])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
