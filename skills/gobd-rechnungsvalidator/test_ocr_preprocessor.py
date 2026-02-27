#!/usr/bin/env python3
"""
Test-Suite für GoBD OCR Preprocessor v2.5
Testet Bildvorverarbeitung, mehrsprachige OCR und Integration
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import json

# Füge das Parent-Verzeichnis zum Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent))

from ocr_preprocessor import (
    ImagePreprocessor, OCRConfig, OCRResult,
    OCRPresets, extract_text_from_pdf
)


class TestOCRPreprocessor:
    """Test-Klasse für OCR Preprocessor"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def test_config_creation(self):
        """Test: OCR-Konfiguration erstellen"""
        try:
            config = OCRConfig(
                dpi=300,
                contrast_factor=1.5,
                languages=['deu', 'eng']
            )
            assert config.dpi == 300
            assert config.contrast_factor == 1.5
            assert config.languages == ['deu', 'eng']
            print("✅ OCR-Konfiguration erstellen")
            self.passed += 1
        except Exception as e:
            print(f"❌ OCR-Konfiguration erstellen: {e}")
            self.failed += 1
    
    def test_presets(self):
        """Test: Alle OCR-Presets erstellen"""
        presets = [
            ('scanned', OCRPresets.scanned_document),
            ('low_quality', OCRPresets.low_quality_scan),
            ('invoice', OCRPresets.invoice_multilingual),
            ('fast', OCRPresets.fast_processing),
            ('max_quality', OCRPresets.maximum_quality),
        ]
        
        for name, preset_func in presets:
            try:
                config = preset_func()
                assert config.dpi > 0
                assert config.languages is not None
                print(f"✅ Preset '{name}' erstellt (DPI: {config.dpi})")
                self.passed += 1
            except Exception as e:
                print(f"❌ Preset '{name}': {e}")
                self.failed += 1
    
    def test_preprocessor_init(self):
        """Test: ImagePreprocessor Initialisierung"""
        try:
            config = OCRConfig(dpi=300)
            preprocessor = ImagePreprocessor(config)
            assert preprocessor.config.dpi == 300
            print("✅ ImagePreprocessor Initialisierung")
            self.passed += 1
        except ImportError:
            print("⚠️ PIL nicht verfügbar - Test übersprungen")
        except Exception as e:
            print(f"❌ ImagePreprocessor Initialisierung: {e}")
            self.failed += 1
    
    def test_contrast_calculation(self):
        """Test: OTSU-Schwellenwertberechnung"""
        try:
            from PIL import Image
            config = OCRConfig()
            preprocessor = ImagePreprocessor(config)
            
            # Erstelle Testbild
            test_image = Image.new('L', (100, 100), 128)
            threshold = preprocessor._calculate_otsu_threshold(test_image)
            
            assert 0 <= threshold <= 255
            print(f"✅ OTSU-Schwellenwertberechnung (Wert: {threshold})")
            self.passed += 1
        except ImportError:
            print("⚠️ PIL nicht verfügbar - Test übersprungen")
        except Exception as e:
            print(f"❌ OTSU-Schwellenwertberechnung: {e}")
            self.failed += 1
    
    def test_resize_to_dpi(self):
        """Test: DPI-Größenanpassung"""
        try:
            from PIL import Image
            config = OCRConfig(dpi=300)
            preprocessor = ImagePreprocessor(config)
            
            # 72 DPI Bild (Standard)
            original = Image.new('RGB', (100, 100))
            resized = preprocessor._resize_to_dpi(original, 300)
            
            # Sollte größer sein (ca. 4.17x)
            assert resized.width > original.width
            print(f"✅ DPI-Größenanpassung: {original.size} -> {resized.size}")
            self.passed += 1
        except ImportError:
            print("⚠️ PIL nicht verfügbar - Test übersprungen")
        except Exception as e:
            print(f"❌ DPI-Größenanpassung: {e}")
            self.failed += 1
    
    def test_enhancements(self):
        """Test: Bildverbesserungsmethoden"""
        try:
            from PIL import Image
            config = OCRConfig()
            preprocessor = ImagePreprocessor(config)
            
            test_image = Image.new('RGB', (100, 100), (128, 128, 128))
            
            # Teste Helligkeit
            bright = preprocessor._adjust_brightness(test_image, 1.5)
            assert bright is not None
            
            # Teste Kontrast
            contrast = preprocessor._adjust_contrast(test_image, 1.5)
            assert contrast is not None
            
            # Teste Schärfung
            sharp = preprocessor._sharpen(test_image, 2.0)
            assert sharp is not None
            
            print("✅ Bildverbesserungsmethoden")
            self.passed += 1
        except ImportError:
            print("⚠️ PIL nicht verfügbar - Test übersprungen")
        except Exception as e:
            print(f"❌ Bildverbesserungsmethoden: {e}")
            self.failed += 1
    
    def test_binarization(self):
        """Test: Binarisierung"""
        try:
            from PIL import Image
            config = OCRConfig(binarize=True)
            preprocessor = ImagePreprocessor(config)
            
            # Graustufen-Bild
            gray = Image.new('L', (100, 100), 128)
            binary = preprocessor._binarize(gray)
            
            assert binary.mode == '1'  # Schwarz/Weiß
            print("✅ Binarisierung")
            self.passed += 1
        except ImportError:
            print("⚠️ PIL nicht verfügbar - Test übersprungen")
        except Exception as e:
            print(f"❌ Binarisierung: {e}")
            self.failed += 1
    
    def test_denoise(self):
        """Test: Rauschunterdrückung"""
        try:
            from PIL import Image
            config = OCRConfig(denoise=True)
            preprocessor = ImagePreprocessor(config)
            
            test_image = Image.new('RGB', (100, 100))
            denoised = preprocessor._denoise(test_image)
            
            assert denoised is not None
            print("✅ Rauschunterdrückung")
            self.passed += 1
        except ImportError:
            print("⚠️ PIL nicht verfügbar - Test übersprungen")
        except Exception as e:
            print(f"❌ Rauschunterdrückung: {e}")
            self.failed += 1
    
    def test_full_preprocessing(self):
        """Test: Komplettes Preprocessing"""
        try:
            from PIL import Image
            config = OCRConfig(
                dpi=150,  # Niedriger für schnelleren Test
                contrast_factor=1.5,
                sharpness_factor=2.0,
                binarize=True,
                denoise=True
            )
            preprocessor = ImagePreprocessor(config)
            
            test_image = Image.new('RGB', (200, 200), (150, 150, 150))
            processed, steps = preprocessor.preprocess(test_image)
            
            assert processed is not None
            assert len(steps) > 0
            print(f"✅ Komplettes Preprocessing ({len(steps)} Schritte)")
            self.passed += 1
        except ImportError:
            print("⚠️ PIL nicht verfügbar - Test übersprungen")
        except Exception as e:
            print(f"❌ Komplettes Preprocessing: {e}")
            self.failed += 1
    
    def test_ocr_result_structure(self):
        """Test: OCRResult Datenstruktur"""
        try:
            result = OCRResult(
                text="Test Rechnung",
                confidence=0.95,
                language="deu",
                page_num=1,
                preprocessing_applied=['resize', 'contrast'],
                raw_image_size=(100, 100),
                processed_image_size=(400, 400)
            )
            
            assert result.text == "Test Rechnung"
            assert result.confidence == 0.95
            assert result.language == "deu"
            print("✅ OCRResult Datenstruktur")
            self.passed += 1
        except Exception as e:
            print(f"❌ OCRResult Datenstruktur: {e}")
            self.failed += 1
    
    def test_multilingual_config(self):
        """Test: Mehrsprachige Konfiguration"""
        try:
            config = OCRConfig(languages=['deu', 'eng', 'fra', 'ita', 'spa'])
            assert len(config.languages) == 5
            assert 'deu' in config.languages
            assert 'fra' in config.languages
            print("✅ Mehrsprachige Konfiguration")
            self.passed += 1
        except Exception as e:
            print(f"❌ Mehrsprachige Konfiguration: {e}")
            self.failed += 1
    
    def run_all_tests(self):
        """Führt alle Tests aus"""
        print("\n" + "="*60)
        print("🧪 GoBD OCR PREPROCESSOR TEST-SUITE")
        print("="*60 + "\n")
        
        tests = [
            self.test_config_creation,
            self.test_presets,
            self.test_preprocessor_init,
            self.test_contrast_calculation,
            self.test_resize_to_dpi,
            self.test_enhancements,
            self.test_binarization,
            self.test_denoise,
            self.test_full_preprocessing,
            self.test_ocr_result_structure,
            self.test_multilingual_config,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ {test.__name__}: {e}")
                self.failed += 1
        
        # Zusammenfassung
        print("\n" + "="*60)
        print("📊 TEST-ZUSAMMENFASSUNG")
        print("="*60)
        print(f"✅ Bestanden: {self.passed}")
        print(f"❌ Fehlgeschlagen: {self.failed}")
        print(f"📊 Erfolgsrate: {self.passed/(self.passed+self.failed)*100:.1f}%")
        
        return self.failed == 0


def create_test_rechnung_data():
    """Erstellt Testdaten für simulierte Rechnungen"""
    return {
        'deutsch': {
            'text': """
Muster GmbH
Musterstraße 123
12345 Berlin

Rechnung Nr: RE-2024-001
Datum: 15.02.2024

Kunde: Max Mustermann
Musterweg 45
54321 München

Positionen:
1x Beratung à 100,00 EUR

Gesamtbetrag: 119,00 EUR
inkl. 19% MwSt

Steuernummer: 1234567890
            """,
            'expected': {
                'lieferant': 'Muster GmbH',
                'rechnungsnummer': 'RE-2024-001',
                'gesamtbetrag': '119,00 EUR',
            }
        },
        'englisch': {
            'text': """
Sample Ltd.
123 Sample Street
London SW1A 1AA
UK

Invoice No: INV-2024-001
Date: 15/02/2024

Customer: John Doe
45 Customer Road
Manchester M1 1AA

Items:
1x Consulting @ £100.00

Total Amount: £119.00
including 20% VAT

VAT Number: GB123456789
            """,
            'expected': {
                'lieferant': 'Sample Ltd.',
                'rechnungsnummer': 'INV-2024-001',
                'gesamtbetrag': '£119.00',
            }
        },
        'französisch': {
            'text': """
Exemple S.A.R.L.
123 Rue Exemple
75001 Paris
France

Facture n°: FAC-2024-001
Date: 15/02/2024

Client: Jean Dupont
45 Avenue Client
69001 Lyon

Articles:
1x Conseil à 100,00 €

Montant total: 120,00 €
TVA 20% incluse

Numéro de TVA: FR12345678901
            """,
            'expected': {
                'lieferant': 'Exemple S.A.R.L.',
                'rechnungsnummer': 'FAC-2024-001',
                'gesamtbetrag': '120,00 €',
            }
        }
    }


def test_pattern_extraction():
    """Testet Regex-Patterns auf Testdaten"""
    print("\n" + "="*60)
    print("🔍 PATTERN-EXTRACTION TEST")
    print("="*60 + "\n")
    
    test_data = create_test_rechnung_data()
    
    # Einfache Patterns
    patterns = {
        'rechnungsnummer': [
            r'Rechnungs?(?:nummer|nr| Nr|\.Nr)[:\s.]*([A-Z0-9\-\/_]+)',
            r'Invoice\s*(?:No|Number)[:\s.]*([A-Z0-9\-\/_]+)',
            r'Facture\s*(?:n°|No|Numéro)[:\s.]*([A-Z0-9\-\/_]+)',
        ],
        'gesamtbetrag': [
            r'Gesamtbetrag[:\s]*([\d.,]+\s*[€EUR]?)',
            r'Total\s*(?:Amount)?[:\s]*([\d.,]+\s*[£$€EUR]?)',
            r'Montant\s*total[:\s]*([\d.,]+\s*[€]?)',
        ]
    }
    
    results = []
    for language, data in test_data.items():
        text = data['text']
        expected = data['expected']
        
        print(f"Testing {language}...")
        
        # Teste Rechnungsnummer
        rechnungsnummer = None
        for pattern in patterns['rechnungsnummer']:
            match = __import__('re').search(pattern, text, __import__('re').I)
            if match:
                rechnungsnummer = match.group(1)
                break
        
        # Teste Gesamtbetrag
        gesamtbetrag = None
        for pattern in patterns['gesamtbetrag']:
            match = __import__('re').search(pattern, text, __import__('re').I)
            if match:
                gesamtbetrag = match.group(1)
                break
        
        success = rechnungsnummer == expected['rechnungsnummer']
        results.append(success)
        
        if success:
            print(f"  ✅ Rechnungsnummer: {rechnungsnummer}")
        else:
            print(f"  ❌ Rechnungsnummer: {rechnungsnummer} (expected: {expected['rechnungsnummer']})")
        
        if gesamtbetrag:
            print(f"  ✅ Gesamtbetrag gefunden: {gesamtbetrag}")
        else:
            print(f"  ⚠️ Gesamtbetrag nicht gefunden")
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Pattern-Extraktion: {success_rate:.0f}% erfolgreich")
    return all(results)


if __name__ == '__main__':
    # Führe Unit-Tests aus
    tester = TestOCRPreprocessor()
    unit_success = tester.run_all_tests()
    
    # Führe Pattern-Tests aus
    pattern_success = test_pattern_extraction()
    
    # Gesamtergebnis
    print("\n" + "="*60)
    print("🎯 GESAMTERGEBNIS")
    print("="*60)
    
    if unit_success and pattern_success:
        print("✅ Alle Tests bestanden!")
        sys.exit(0)
    else:
        print("❌ Einige Tests fehlgeschlagen")
        sys.exit(1)
