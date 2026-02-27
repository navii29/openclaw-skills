"""
Unit Tests für GoBD Compliance Checker
"""

import pytest
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gobd_checker import (
    Rechnung,
    Rechnungsposition,
    PruefErgebnis,
    GoBDChecker,
    ChronologiePruefer,
    quick_check,
    InvalidRechnungError,
)


class TestRechnungsposition:
    """Tests für Rechnungsposition"""
    
    def test_position_berechnungen(self):
        """Test: Berechnungen der Position"""
        pos = Rechnungsposition(
            bezeichnung="Beratung",
            menge=10,
            preis=100.00,
            steuersatz=19
        )
        
        assert pos.netto == 1000.00
        assert pos.ust == 190.00
        assert pos.brutto == 1190.00
    
    def test_position_steuerbefreiung(self):
        """Test: Steuerbefreite Position"""
        pos = Rechnungsposition(
            bezeichnung="Buch",
            menge=1,
            preis=20.00,
            steuersatz=7  # Reduzierter Satz
        )
        
        assert abs(pos.ust - 1.40) < 0.01
        assert abs(pos.brutto - 21.40) < 0.01


class TestRechnung:
    """Tests für Rechnung"""
    
    def test_rechnung_gesamtbetrage(self):
        """Test: Gesamtbeträge berechnen"""
        rechnung = Rechnung(
            rechnungsnr="RE-001",
            ausstellungsdatum="2024-01-15",
            lieferdatum="2024-01-10",
            steller_name="Muster GmbH",
            steller_anschrift="Musterstraße 1",
            empfaenger_name="Kunde AG",
            empfaenger_anschrift="Kundenweg 42",
            positionen=[
                Rechnungsposition("Beratung", 10, 100, 19),
                Rechnungsposition("Software", 1, 500, 19),
            ]
        )
        
        assert rechnung.netto_gesamt == 1500.00
        assert rechnung.ust_gesamt == 285.00
        assert rechnung.brutto_gesamt == 1785.00
    
    def test_rechnung_hin_steuerbefreiung(self):
        """Test: Erkennung von Steuerbefreiung"""
        rechnung = Rechnung(
            rechnungsnr="RE-001",
            ausstellungsdatum="2024-01-15",
            lieferdatum="2024-01-10",
            steller_name="Muster GmbH",
            steller_anschrift="Musterstraße 1",
            empfaenger_name="Kunde AG",
            empfaenger_anschrift="Kundenweg 42",
            positionen=[
                Rechnungsposition("Export", 1, 1000, 0),  # Steuerfrei
            ]
        )
        
        assert rechnung.hat_steuerbefreiung == True
        assert rechnung.ust_gesamt == 0
    
    def test_rechnung_zu_dict(self):
        """Test: Konvertierung zu Dictionary"""
        rechnung = Rechnung(
            rechnungsnr="RE-001",
            ausstellungsdatum="2024-01-15",
            lieferdatum="2024-01-10",
            steller_name="Muster GmbH",
            steller_anschrift="Musterstraße 1",
            steller_ustid="DE123456789",
            empfaenger_name="Kunde AG",
            empfaenger_anschrift="Kundenweg 42",
            positionen=[
                Rechnungsposition("Beratung", 10, 100, 19),
            ]
        )
        
        d = rechnung.zu_dict()
        assert d['rechnungsnr'] == "RE-001"
        assert d['steller_ustid'] == "DE123456789"
        assert len(d['positionen']) == 1


class TestGoBDChecker:
    """Tests für GoBDChecker"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.checker = GoBDChecker()
        self.gueltige_rechnung = Rechnung(
            rechnungsnr="RE-2024-001",
            ausstellungsdatum="2024-01-15",
            lieferdatum="2024-01-10",
            steller_name="Muster GmbH",
            steller_anschrift="Musterstraße 1, 20095 Hamburg",
            steller_ustid="DE123456789",
            empfaenger_name="Kunde AG",
            empfaenger_anschrift="Kundenweg 42, 10115 Berlin",
            positionen=[
                Rechnungsposition("Beratung", 10, 100, 19),
            ]
        )
    
    def test_vollstaendige_rechnung(self):
        """Test: Vollständige Rechnung ist konform"""
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert ergebnis.ist_konform == True
        assert len(ergebnis.mangel) == 0
        assert ergebnis.hash is not None
    
    def test_fehlender_steller_name(self):
        """Test: Fehlender Rechnungssteller wird erkannt"""
        self.gueltige_rechnung.steller_name = ""
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert ergebnis.ist_konform == False
        assert any("Name des leistenden Unternehmers" in m for m in ergebnis.mangel)
    
    def test_fehlende_steller_anschrift(self):
        """Test: Fehlende Anschrift des Stellers wird erkannt"""
        self.gueltige_rechnung.steller_anschrift = ""
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert ergebnis.ist_konform == False
        assert any("Anschrift des leistenden Unternehmers" in m for m in ergebnis.mangel)
    
    def test_fehlender_empfaenger_name(self):
        """Test: Fehlender Empfänger wird erkannt"""
        self.gueltige_rechnung.empfaenger_name = ""
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert ergebnis.ist_konform == False
        assert any("Leistungsempfängers" in m for m in ergebnis.mangel)
    
    def test_fehlende_ustid_und_steuernummer(self):
        """Test: Fehlende Steuer-ID wird erkannt"""
        self.gueltige_rechnung.steller_ustid = None
        self.gueltige_rechnung.steller_steuernummer = None
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert ergebnis.ist_konform == False
        assert any("USt-IdNr oder Steuernummer" in m for m in ergebnis.mangel)
    
    def test_ungueltige_ustid(self):
        """Test: Ungültige USt-IdNr wird erkannt"""
        self.gueltige_rechnung.steller_ustid = "INVALID"
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert ergebnis.ist_konform == False
    
    def test_steuernummer_statt_ustid(self):
        """Test: Steuernummer ist auch gültig"""
        self.gueltige_rechnung.steller_ustid = None
        self.gueltige_rechnung.steller_steuernummer = "1234567890123"
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert ergebnis.pflichtangaben['steller_steuerid'] == True
    
    def test_ungueltiges_datum(self):
        """Test: Ungültiges Datum wird erkannt"""
        self.gueltige_rechnung.ausstellungsdatum = "invalid"
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert ergebnis.ist_konform == False
        assert any("Ausstellungsdatum" in m for m in ergebnis.mangel)
    
    def test_fehlende_rechnungsnummer(self):
        """Test: Fehlende Rechnungsnummer wird erkannt"""
        self.gueltige_rechnung.rechnungsnr = ""
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert ergebnis.ist_konform == False
        assert any("Rechnungsnummer" in m for m in ergebnis.mangel)
    
    def test_keine_positionen(self):
        """Test: Fehlende Positionen werden erkannt"""
        self.gueltige_rechnung.positionen = []
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert ergebnis.ist_konform == False
        assert any("Rechnungspositionen" in m for m in ergebnis.mangel)
    
    def test_position_ohne_bezeichnung(self):
        """Test: Position ohne Bezeichnung wird erkannt"""
        self.gueltige_rechnung.positionen = [
            Rechnungsposition("", 1, 100, 19),
        ]
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert any("Bezeichnung" in m for m in ergebnis.mangel)
    
    def test_position_mit_negativer_menge(self):
        """Test: Negative Menge wird erkannt"""
        self.gueltige_rechnung.positionen = [
            Rechnungsposition("Beratung", -1, 100, 19),
        ]
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert any("Menge" in m for m in ergebnis.mangel)
    
    def test_position_mit_negativem_preis(self):
        """Test: Negativer Preis wird erkannt"""
        self.gueltige_rechnung.positionen = [
            Rechnungsposition("Beratung", 1, -100, 19),
        ]
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert any("Negativer Preis" in m for m in ergebnis.mangel)
    
    def test_fehlendes_lieferdatum(self):
        """Test: Fehlendes Lieferdatum wird erkannt"""
        self.gueltige_rechnung.lieferdatum = ""
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        
        assert ergebnis.ist_konform == False
        assert any("Lieferdatum" in m for m in ergebnis.mangel)
    
    def test_hash_berechnung(self):
        """Test: Hash wird korrekt berechnet"""
        hash1 = self.checker.berechne_hash(self.gueltige_rechnung)
        hash2 = self.checker.berechne_hash(self.gueltige_rechnung)
        
        assert hash1.startswith("sha256:")
        assert hash1 == hash2  # Deterministisch
    
    def test_hash_aenderungserkennung(self):
        """Test: Hash ändert sich bei Änderung"""
        hash1 = self.checker.berechne_hash(self.gueltige_rechnung)
        
        self.gueltige_rechnung.steller_name = "Geänderter Name"
        hash2 = self.checker.berechne_hash(self.gueltige_rechnung)
        
        assert hash1 != hash2
    
    def test_hash_verifikation(self):
        """Test: Hash-Verifikation funktioniert"""
        hash_wert = self.checker.berechne_hash(self.gueltige_rechnung)
        
        assert self.checker.verifiziere_hash(self.gueltige_rechnung, hash_wert) == True
        assert self.checker.verifiziere_hash(self.gueltige_rechnung, "falscher_hash") == False
    
    def test_batch_pruefung(self):
        """Test: Batch-Prüfung"""
        rechnungen = [
            self.gueltige_rechnung,
            Rechnung(
                rechnungsnr="RE-002",
                ausstellungsdatum="2024-01-20",
                lieferdatum="2024-01-15",
                steller_name="",  # Ungültig!
                steller_anschrift="Test",
                empfaenger_name="Kunde",
                empfaenger_anschrift="Adresse",
                positionen=[Rechnungsposition("Test", 1, 100, 19)],
            ),
        ]
        
        ergebnis = self.checker.pruefe_batch(rechnungen)
        
        assert ergebnis['gesamt'] == 2
        assert ergebnis['konform'] == 1
        assert ergebnis['nicht_konform'] == 1
        assert ergebnis['konformitaetsrate'] == 0.5
    
    def test_generiere_bericht(self):
        """Test: Berichtsgenerierung"""
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        bericht = self.checker.generiere_bericht(ergebnis, self.gueltige_rechnung)
        
        assert "GoBD-PRÜFUNGSBERICHT" in bericht
        assert "RE-2024-001" in bericht
        assert "GoBD-KONFORM" in bericht
    
    def test_bericht_mit_mangeln(self):
        """Test: Bericht mit Mängeln"""
        self.gueltige_rechnung.steller_name = ""
        ergebnis = self.checker.pruefe_rechnung(self.gueltige_rechnung)
        bericht = self.checker.generiere_bericht(ergebnis, self.gueltige_rechnung)
        
        assert "NICHT GoBD-KONFORM" in bericht
        assert "MÄNGEL" in bericht


class TestChronologiePruefer:
    """Tests für ChronologiePruefer"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.pruefer = ChronologiePruefer(prefix="RE-")
    
    def test_fortlaufende_nummern(self):
        """Test: Fortlaufende Nummern sind OK"""
        ergebnis = self.pruefer.pruefe_fortlaufend([
            "RE-001", "RE-002", "RE-003", "RE-004"
        ])
        
        assert ergebnis['ist_fortlaufend'] == True
        assert len(ergebnis['luecken']) == 0
        assert len(ergebnis['doppelte']) == 0
    
    def test_luecke_erkennen(self):
        """Test: Lücke wird erkannt"""
        ergebnis = self.pruefer.pruefe_fortlaufend([
            "RE-001", "RE-002", "RE-004"  # RE-003 fehlt
        ])
        
        assert ergebnis['ist_fortlaufend'] == False
        assert "RE-003" in ergebnis['luecken']
        assert any("Lücke" in w for w in ergebnis['warnungen'])
    
    def test_doppelte_erkennen(self):
        """Test: Doppelte Nummer wird erkannt"""
        ergebnis = self.pruefer.pruefe_fortlaufend([
            "RE-001", "RE-002", "RE-002", "RE-003"
        ])
        
        assert ergebnis['ist_fortlaufend'] == False
        assert "RE-002" in ergebnis['doppelte']
    
    def test_leere_liste(self):
        """Test: Leere Liste ist gültig"""
        ergebnis = self.pruefer.pruefe_fortlaufend([])
        
        assert ergebnis['ist_fortlaufend'] == True
    
    def test_generiere_vorschlag(self):
        """Test: Nächste Nummer wird vorgeschlagen"""
        vorschlag = self.pruefer.generiere_vorschlag("RE-005")
        assert vorschlag == "RE-006"
    
    def test_generiere_vorschlag_leer(self):
        """Test: Vorschlag ohne letzte Nummer"""
        vorschlag = self.pruefer.generiere_vorschlag("")
        assert vorschlag == "RE-001"


class TestQuickCheck:
    """Tests für quick_check Convenience-Funktion"""
    
    def test_quick_check_gueltig(self):
        """Test: Schnelle Prüfung gültiger Rechnung"""
        ergebnis = quick_check({
            'rechnungsnr': 'RE-001',
            'ausstellungsdatum': '2024-01-15',
            'lieferdatum': '2024-01-10',
            'steller_name': 'Muster GmbH',
            'steller_anschrift': 'Musterstraße 1',
            'steller_ustid': 'DE123456789',
            'empfaenger_name': 'Kunde AG',
            'empfaenger_anschrift': 'Kundenweg 42',
            'positionen': [
                {'bezeichnung': 'Beratung', 'menge': 10, 'preis': 100, 'steuersatz': 19},
            ],
        })
        
        assert isinstance(ergebnis, PruefErgebnis)
        assert ergebnis.ist_konform == True
    
    def test_quick_check_ungueltig(self):
        """Test: Schnelle Prüfung ungültiger Rechnung"""
        ergebnis = quick_check({
            'rechnungsnr': '',
            'ausstellungsdatum': '',
            'lieferdatum': '',
            'steller_name': '',
            'steller_anschrift': '',
            'empfaenger_name': '',
            'empfaenger_anschrift': '',
            'positionen': [],
        })
        
        assert ergebnis.ist_konform == False
        assert len(ergebnis.mangel) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
