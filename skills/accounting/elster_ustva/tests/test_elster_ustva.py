"""
Unit Tests für ELSTER USt-Voranmeldung Helper
"""

import pytest
import os
import tempfile
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from elster_ustva import (
    UStVAGenerator,
    SteuernummerValidator,
    UStVABetrage,
    InvalidSteuernummerError,
    InvalidZeitraumError,
    InvalidBetragError,
    XMLGenerationError,
    ElsterError,
    quick_voranmeldung,
    batch_create_voranmeldungen,
)


class TestSteuernummerValidator:
    """Tests für Steuernummer-Validierung"""
    
    def test_valid_national_steuernummer(self):
        """Test: Gültige nationale Steuernummer wird akzeptiert"""
        validator = SteuernummerValidator()
        # Hamburg-Format (02 = Hamburg) - 13 Stellen
        assert validator.validate_national("02 123 45678 901") == True
        assert validator.validate_national("0212345678901") == True
    
    def test_valid_national_with_formatting(self):
        """Test: Steuernummer mit Formatierung wird akzeptiert"""
        validator = SteuernummerValidator()
        assert validator.validate_national("123 456 78901 23") == True
        assert validator.validate_national("123-456-78901-23") == True
    
    def test_invalid_steuernummer_too_short(self):
        """Test: Zu kurze Steuernummer wird abgelehnt"""
        validator = SteuernummerValidator()
        with pytest.raises(InvalidSteuernummerError) as exc_info:
            validator.validate_national("123456")
        assert "13 Stellen" in str(exc_info.value)
    
    def test_invalid_steuernummer_too_long(self):
        """Test: Zu lange Steuernummer wird abgelehnt"""
        validator = SteuernummerValidator()
        with pytest.raises(InvalidSteuernummerError) as exc_info:
            validator.validate_national("123456789012345")
        assert "13 Stellen" in str(exc_info.value)
    
    def test_invalid_bundesland(self):
        """Test: Ungültiges Bundesland wird erkannt"""
        validator = SteuernummerValidator()
        with pytest.raises(InvalidSteuernummerError) as exc_info:
            validator.validate_national("9912345678901")
        assert "Bundesland" in str(exc_info.value)
    
    def test_valid_ust_idnr(self):
        """Test: Gültige USt-IdNr wird akzeptiert"""
        validator = SteuernummerValidator()
        assert validator.validate_ust_idnr("DE123456789") == True
        assert validator.validate_ust_idnr("de123456789") == True
    
    def test_invalid_ust_idnr_no_de(self):
        """Test: USt-IdNr ohne DE wird abgelehnt"""
        validator = SteuernummerValidator()
        with pytest.raises(InvalidSteuernummerError) as exc_info:
            validator.validate_ust_idnr("123456789")
        assert "DE" in str(exc_info.value)
    
    def test_invalid_ust_idnr_wrong_length(self):
        """Test: USt-IdNr mit falscher Länge wird abgelehnt"""
        validator = SteuernummerValidator()
        with pytest.raises(InvalidSteuernummerError) as exc_info:
            validator.validate_ust_idnr("DE12345678")
        assert "9 Ziffern" in str(exc_info.value)
    
    def test_format_national(self):
        """Test: Formatierung der Steuernummer"""
        validator = SteuernummerValidator()
        assert validator.format_national("1234567890123") == "1234567890123"
        assert validator.format_national("123 456 78901 23") == "1234567890123"
        assert validator.format_national("123-456-78901-23") == "1234567890123"


class TestUStVABetrage:
    """Tests für USt-VA Beträge"""
    
    def test_valid_betrage(self):
        """Test: Gültige Beträge werden akzeptiert"""
        betrage = UStVABetrage(kz81=10000, kz86=5000, kz66=3000, kz63=0)
        betrage.validate()  # Sollte nicht werfen
    
    def test_zero_betrage(self):
        """Test: Null-Beträge sind gültig"""
        betrage = UStVABetrage()
        betrage.validate()
        assert betrage.kz81 == 0
        assert betrage.kz86 == 0
    
    def test_negative_betrag(self):
        """Test: Negative Beträge werden abgelehnt"""
        betrage = UStVABetrage(kz81=-100)
        with pytest.raises(InvalidBetragError) as exc_info:
            betrage.validate()
        assert "negativ" in str(exc_info.value)
    
    def test_betrag_too_large(self):
        """Test: Zu große Beträge werden abgelehnt"""
        betrage = UStVABetrage(kz81=100_000_000_000)
        with pytest.raises(InvalidBetragError) as exc_info:
            betrage.validate()
        assert "zu groß" in str(exc_info.value)
    
    def test_non_numeric_betrag(self):
        """Test: Nicht-numerische Beträge werden abgelehnt"""
        betrage = UStVABetrage(kz81="invalid")
        with pytest.raises(InvalidBetragError) as exc_info:
            betrage.validate()
    
    def test_ust_gesamt_calculation(self):
        """Test: Berechnung der Gesamt-USt"""
        betrage = UStVABetrage(kz81=19000, kz86=7000)
        assert betrage.ust_gesamt == 26000
    
    def test_vorsteuer_gesamt_calculation(self):
        """Test: Berechnung der Gesamt-Vorsteuer"""
        betrage = UStVABetrage(kz66=5000, kz63=1000)
        assert betrage.vorsteuer_gesamt == 6000
    
    def test_zahllast_calculation_positive(self):
        """Test: Positive Zahllast (Zahlung ans FA)"""
        betrage = UStVABetrage(kz81=19000, kz66=5000)
        assert betrage.zahllast == 14000
    
    def test_zahllast_calculation_negative(self):
        """Test: Negative Zahllast (Erstattung)"""
        betrage = UStVABetrage(kz81=5000, kz66=10000)
        assert betrage.zahllast == -5000


class TestUStVAGenerator:
    """Tests für USt-VA Generator"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.generator = UStVAGenerator(
            steuernummer="0212345678901",
            finanzamt="2166",
            name="Test GmbH"
        )
    
    def test_generator_initialization(self):
        """Test: Generator wird korrekt initialisiert"""
        assert self.generator.steuernummer == "0212345678901"
        assert self.generator.finanzamt == "2166"
        assert self.generator.name == "Test GmbH"
    
    def test_generator_invalid_steuernummer(self):
        """Test: Generator mit ungültiger Steuernummer"""
        with pytest.raises(InvalidSteuernummerError):
            UStVAGenerator(
                steuernummer="123",  # Zu kurz
                finanzamt="2166",
                name="Test GmbH"
            )
    
    def test_generator_invalid_finanzamt(self):
        """Test: Generator mit ungültigem Finanzamt"""
        with pytest.raises(ElsterError):
            UStVAGenerator(
                steuernummer="0212345678901",
                finanzamt="12345",  # Zu lang
                name="Test GmbH"
            )
    
    def test_create_voranmeldung_basic(self):
        """Test: Einfache Voranmeldung erstellen"""
        xml = self.generator.create_voranmeldung(
            jahr=2024,
            monat=1,
            kz81=19000,
            kz86=0,
            kz66=5000,
            kz63=0
        )
        
        assert '<?xml version="1.0"' in xml
        assert '<Elster' in xml
        assert 'UmsatzsteuerVoranmeldung' in xml
        assert '0212345678901' in xml
        assert '2166' in xml
        assert 'Test GmbH' in xml
        assert '2024' in xml
        assert '1' in xml
    
    def test_create_voranmeldung_all_kz(self):
        """Test: Voranmeldung mit allen Kennzahlen"""
        xml = self.generator.create_voranmeldung(
            jahr=2024,
            monat=6,
            kz81=19000,
            kz86=7000,
            kz66=5000,
            kz63=1000
        )
        
        assert 'Kz81' in xml
        assert 'Kz86' in xml
        assert 'Kz66' in xml
        assert 'Kz63' in xml
        assert 'UStGesamt' in xml
        assert 'VorsteuerGesamt' in xml
        assert 'Zahllast' in xml
    
    def test_create_voranmeldung_zero_values_omitted(self):
        """Test: Null-Werte werden im XML weggelassen"""
        xml = self.generator.create_voranmeldung(
            jahr=2024,
            monat=1,
            kz81=19000,
            kz86=0,
            kz66=0,
            kz63=0
        )
        
        # Nur Kz81 sollte vorhanden sein
        assert 'Kz81' in xml
        assert '<Kz86>' not in xml
        assert '<Kz66>' not in xml
        assert '<Kz63>' not in xml
    
    def test_invalid_monat(self):
        """Test: Ungültiger Monat wird abgelehnt"""
        with pytest.raises(InvalidZeitraumError):
            self.generator.create_voranmeldung(jahr=2024, monat=0)
        
        with pytest.raises(InvalidZeitraumError):
            self.generator.create_voranmeldung(jahr=2024, monat=13)
        
        with pytest.raises(InvalidZeitraumError):
            self.generator.create_voranmeldung(jahr=2024, monat=-1)
    
    def test_invalid_jahr(self):
        """Test: Ungültiges Jahr wird abgelehnt"""
        with pytest.raises(InvalidZeitraumError):
            self.generator.create_voranmeldung(jahr=1999, monat=1)
        
        with pytest.raises(InvalidZeitraumError):
            self.generator.create_voranmeldung(jahr=2050, monat=1)
    
    def test_invalid_betrag_in_voranmeldung(self):
        """Test: Ungültiger Betrag in Voranmeldung"""
        with pytest.raises(InvalidBetragError):
            self.generator.create_voranmeldung(
                jahr=2024,
                monat=1,
                kz81=-100
            )
    
    def test_custom_erstellungsdatum(self):
        """Test: Eigenes Erstellungsdatum"""
        xml = self.generator.create_voranmeldung(
            jahr=2024,
            monat=1,
            erstellungsdatum="2024-02-15"
        )
        
        assert '2024-02-15' in xml
    
    def test_save_to_file(self):
        """Test: Speichern in Datei"""
        with tempfile.TemporaryDirectory() as tmpdir:
            xml = self.generator.create_voranmeldung(jahr=2024, monat=1)
            filepath = os.path.join(tmpdir, "test.xml")
            
            result = self.generator.save_to_file(xml, filepath)
            
            assert os.path.exists(result)
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
                assert '<Elster' in content


class TestQuickFunctions:
    """Tests für Convenience-Funktionen"""
    
    def test_quick_voranmeldung(self):
        """Test: Schnelle Voranmeldung"""
        xml = quick_voranmeldung(
            steuernummer="0212345678901",
            finanzamt="2166",
            name="Schnell Test",
            jahr=2024,
            monat=3,
            kz81=10000,
            kz66=2000
        )
        
        assert 'Schnell Test' in xml
        assert '10000' in xml
        assert '2000' in xml
    
    def test_batch_create(self):
        """Test: Batch-Erstellung"""
        generator = UStVAGenerator(
            steuernummer="0212345678901",
            finanzamt="2166",
            name="Batch Test"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            perioden = [
                {'jahr': 2024, 'monat': 1, 'kz81': 10000, 'kz66': 2000},
                {'jahr': 2024, 'monat': 2, 'kz81': 15000, 'kz66': 3000},
                {'jahr': 2024, 'monat': 3, 'kz81': 12000, 'kz66': 2500},
            ]
            
            files = batch_create_voranmeldungen(generator, perioden, tmpdir)
            
            assert len(files) == 3
            for f in files:
                assert os.path.exists(f)


class TestXMLStructure:
    """Tests für XML-Struktur"""
    
    def test_xml_namespaces(self):
        """Test: XML Namespaces sind vorhanden"""
        generator = UStVAGenerator(
            steuernummer="0212345678901",
            finanzamt="2166",
            name="NS Test"
        )
        
        xml = generator.create_voranmeldung(jahr=2024, monat=1)
        
        assert 'xmlns=' in xml
        assert 'xmlns:xsi' in xml
        assert 'http://www.elster.de' in xml
    
    def test_transfer_header_structure(self):
        """Test: Transfer-Header Struktur"""
        generator = UStVAGenerator(
            steuernummer="0212345678901",
            finanzamt="2166",
            name="Header Test"
        )
        
        xml = generator.create_voranmeldung(jahr=2024, monat=1)
        
        assert '<TransferHeader' in xml
        assert '<Verfahren>' in xml
        assert 'ElsterBRM' in xml
        assert '<DatenArt>' in xml
        assert 'USt-Voranmeldung' in xml
        assert '<Vorgang>' in xml
    
    def test_steuerfall_structure(self):
        """Test: Steuerfall Struktur"""
        generator = UStVAGenerator(
            steuernummer="0212345678901",
            finanzamt="2166",
            name="Steuerfall Test"
        )
        
        xml = generator.create_voranmeldung(jahr=2024, monat=1)
        
        assert '<TransferBody' in xml
        assert '<DatenLieferant>' in xml
        assert '<Steuerfall>' in xml
        assert '<UmsatzsteuerVoranmeldung' in xml


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
