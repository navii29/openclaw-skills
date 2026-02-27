#!/usr/bin/env python3
"""
Integration Test für German Accounting Suite mit erweitertem OCR
"""

import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Füge Skill-Verzeichnisse zum Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent / 'gobd-rechnungsvalidator'))
sys.path.insert(0, str(Path(__file__).parent / 'zugferd-generator'))
sys.path.insert(0, str(Path(__file__).parent / 'datev-csv-export'))
sys.path.insert(0, str(Path(__file__).parent / 'sepa_xml_generator'))


def test_suite_imports():
    """Test: Alle Module können importiert werden"""
    print("\n" + "="*60)
    print("📦 MODULE IMPORT TEST")
    print("="*60)
    
    modules = [
        ('gobd_validator_v25', 'EnhancedGoBDValidator'),
        ('ocr_preprocessor', 'MultilingualOCR'),
        ('ocr_preprocessor', 'OCRPresets'),
        ('zugferd_generator', 'ZUGFeRDGenerator'),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, class_name in modules:
        try:
            module = __import__(module_name)
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {module_name}.{class_name}: {e}")
            failed += 1
    
    return passed, failed


def test_ocr_presets():
    """Test: Alle OCR-Presets funktionieren"""
    print("\n" + "="*60)
    print("🔧 OCR PRESET TEST")
    print("="*60)
    
    try:
        from ocr_preprocessor import OCRPresets
        
        presets = [
            ('scanned_document', 300, 'scanned'),
            ('low_quality_scan', 400, 'low_quality'),
            ('invoice_multilingual', 300, 'invoice'),
            ('fast_processing', 150, 'fast'),
            ('maximum_quality', 400, 'max_quality'),
        ]
        
        passed = 0
        for func_name, expected_dpi, display_name in presets:
            preset_func = getattr(OCRPresets, func_name)
            config = preset_func()
            
            if config.dpi == expected_dpi:
                print(f"✅ Preset '{display_name}': DPI={config.dpi}")
                passed += 1
            else:
                print(f"❌ Preset '{display_name}': DPI={config.dpi} (expected {expected_dpi})")
        
        return passed, len(presets) - passed
    except Exception as e:
        print(f"❌ OCR Preset Test failed: {e}")
        return 0, 1


def test_validator_v25():
    """Test: Validator v2.5 Initialisierung"""
    print("\n" + "="*60)
    print("🔍 VALIDATOR V2.5 TEST")
    print("="*60)
    
    try:
        from gobd_validator_v25 import EnhancedGoBDValidator
        
        # Test mit Standard-Parametern
        validator = EnhancedGoBDValidator(
            use_ocr=True,
            ocr_preset='invoice',
            ocr_languages=['deu', 'eng'],
            dpi=300
        )
        print("✅ EnhancedGoBDValidator initialisiert")
        
        # Test Attribute
        assert validator.VERSION == "2.5.0"
        print(f"✅ Version: {validator.VERSION}")
        
        # Test OCR-Konfiguration
        assert validator.ocr_preset == 'invoice'
        assert validator.ocr_languages == ['deu', 'eng']
        assert validator.dpi == 300
        print("✅ OCR-Konfiguration korrekt")
        
        return 4, 0
    except Exception as e:
        print(f"❌ Validator V2.5 Test failed: {e}")
        return 0, 1


def test_multilingual_patterns():
    """Test: Mehrsprachige Pattern-Erkennung"""
    print("\n" + "="*60)
    print("🌍 MULTILINGUAL PATTERN TEST")
    print("="*60)
    
    try:
        from gobd_validator_v25 import EnhancedGoBDValidator
        
        validator = EnhancedGoBDValidator(use_ocr=False)
        
        test_cases = [
            # (text, method, expected_type)
            ("Rechnung Nr: RE-2024-001", 'find_rechnungsnummer', str),
            ("Invoice No: INV-2024-001", 'find_rechnungsnummer', str),
            ("Facture n°: FAC-2024-001", 'find_rechnungsnummer', str),
            ("Fattura n.: FT-2024-001", 'find_rechnungsnummer', str),
            ("Factura nº: FC-2024-001", 'find_rechnungsnummer', str),
            ("Gesamtbetrag: 1.234,56 €", 'find_gesamtbetrag', str),
            ("Total Amount: £1,234.56", 'find_gesamtbetrag', str),
            ("Montant total: 1 234,56 €", 'find_gesamtbetrag', str),
            ("DE123456789", 'find_ust_id', str),
            ("FR12345678901", 'find_ust_id', str),
            ("IT12345678901", 'find_ust_id', str),
        ]
        
        passed = 0
        for text, method_name, expected_type in test_cases:
            method = getattr(validator, method_name)
            result = method(text)
            
            if result is not None and isinstance(result, expected_type):
                print(f"✅ {method_name}: '{text[:30]}...' -> '{result}'")
                passed += 1
            else:
                print(f"⚠️  {method_name}: '{text[:30]}...' -> {result}")
        
        return passed, len(test_cases) - passed
    except Exception as e:
        print(f"❌ Multilingual Pattern Test failed: {e}")
        return 0, 1


def test_suite_integration():
    """Test: Suite-Integration"""
    print("\n" + "="*60)
    print("🔗 SUITE INTEGRATION TEST")
    print("="*60)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'german-accounting-suite'))
        from suite_integration import GermanAccountingSuite, AccountingWorkflowResult
        
        # Test Suite Initialisierung
        suite = GermanAccountingSuite(
            use_ocr=True,
            smart_suggest=True,
            ocr_preset='invoice',
            ocr_languages=['deu', 'eng'],
            dpi=300
        )
        print("✅ GermanAccountingSuite initialisiert")
        
        # Test Version
        assert suite.VERSION == "1.1.0"
        print(f"✅ Suite Version: {suite.VERSION}")
        
        # Test OCR-Konfiguration
        assert suite.ocr_config['preset'] == 'invoice'
        assert suite.ocr_config['languages'] == ['deu', 'eng']
        assert suite.ocr_config['dpi'] == 300
        print("✅ Suite OCR-Konfiguration korrekt")
        
        # Test AccountingWorkflowResult
        result = AccountingWorkflowResult(
            pdf_path="test.pdf",
            is_valid=True,
            zugferd_path="test.zugferd.zip",
            datev_path="test_datev.csv",
            sepa_path="test_sepa.xml",
            extracted_data={'test': 'data'},
            errors=[],
            ocr_used=True,
            ocr_language='deu',
            ocr_confidence=0.95
        )
        
        assert result.ocr_used == True
        assert result.ocr_language == 'deu'
        assert result.ocr_confidence == 0.95
        print("✅ AccountingWorkflowResult mit OCR-Daten")
        
        return 5, 0
    except Exception as e:
        print(f"❌ Suite Integration Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1


def main():
    """Haupttest-Funktion"""
    print("\n" + "="*60)
    print("🧪 GERMAN ACCOUNTING SUITE - INTEGRATION TESTS")
    print("="*60)
    print("Testet GoBD OCR v2.5 Verbesserungen")
    
    all_results = []
    
    # Führe alle Tests aus
    all_results.append(test_suite_imports())
    all_results.append(test_ocr_presets())
    all_results.append(test_validator_v25())
    all_results.append(test_multilingual_patterns())
    all_results.append(test_suite_integration())
    
    # Gesamtergebnis
    total_passed = sum(p for p, f in all_results)
    total_failed = sum(f for p, f in all_results)
    total_tests = total_passed + total_failed
    
    print("\n" + "="*60)
    print("📊 GESAMTERGEBNIS")
    print("="*60)
    print(f"✅ Bestanden: {total_passed}")
    print(f"❌ Fehlgeschlagen: {total_failed}")
    print(f"📊 Erfolgsrate: {total_passed/total_tests*100:.1f}%")
    print("="*60)
    
    if total_failed == 0:
        print("🎉 ALLE TESTS BESTANDEN!")
        print("\nGoBD OCR v2.5 ist bereit für Produktion!")
        return 0
    else:
        print("⚠️  Einige Tests sind fehlgeschlagen")
        return 1


if __name__ == '__main__':
    sys.exit(main())
