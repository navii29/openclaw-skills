#!/usr/bin/env python3
"""
GoBD-Rechnungsvalidator v2.5
Mit erweitertem OCR-Preprocessing und mehrsprachiger Unterstützung

§14 UStG Pflichtangaben:
1. Name und Anschrift des Lieferanten
2. Name und Anschrift des Empfängers
3. Steuernummer oder USt-IdNr
4. Ausstellungsdatum
5. Rechnungsnummer
6. Menge und Bezeichnung der Leistungen
7. Lieferdatum/Leistungszeitraum
8. Entgelt und Steuerbeträge
9. Steuersatz oder Steuerbefreiung
10. Hinweis §13b UStG (optional)
11. Mängelhinweis §14c UStG (optional)

Version 2.5 - PRODUCTION READY
- Tesseract-Integration mit Bildvorverarbeitung
- DPI-Optimierung, Kontrast, Schärfung
- Mehrsprachige Rechnungen (DE, EN, FR, IT, ES, ...)
- Adaptive OCR-Strategien
"""

import re
import json
import argparse
import sys
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

# PDF Support
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pdfplumber = None
    PDFPLUMBER_AVAILABLE = False

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None

# OCR Preprocessor Integration
sys.path.insert(0, str(Path(__file__).parent))
try:
    from ocr_preprocessor import (
        MultilingualOCR, OCRConfig, OCRPresets,
        ImagePreprocessor, extract_text_from_pdf
    )
    ADVANCED_OCR_AVAILABLE = True
except ImportError:
    ADVANCED_OCR_AVAILABLE = False

# ZUGFeRD Integration
sys.path.insert(0, str(Path(__file__).parent.parent / 'zugferd-generator'))
try:
    from zugferd_generator import ZUGFeRDGenerator, Invoice, InvoiceItem, Party
    ZUGFERD_AVAILABLE = True
except ImportError:
    ZUGFERD_AVAILABLE = False


@dataclass
class ValidationResult:
    """Ergebnis der GoBD-Validierung"""
    filename: str
    is_valid: bool
    score: int
    max_score: int
    confidence: float
    missing_fields: List[str]
    extracted_data: Dict[str, Any]
    warnings: List[str]
    zugferd_compatible: bool = False
    ocr_used: bool = False
    ocr_confidence: float = 0.0
    ocr_language: str = ""
    preprocessing_applied: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class EnhancedGoBDValidator:
    """
    GoBD-Validator mit erweitertem OCR-Preprocessing
    
    Features:
    - Automatische Bildvorverarbeitung (DPI, Kontrast, Schärfung)
    - Mehrsprachige Texterkennung
    - Adaptive OCR-Strategien je nach Dokumentqualität
    """
    
    VERSION = "2.5.0"
    
    # Deutsche Datums-Patterns
    DATE_PATTERNS = [
        r'\b(\d{1,2})[.](\d{1,2})[.](\d{2,4})\b',  # 15.02.2024
        r'\b(\d{1,2})[/](\d{1,2})[/](\d{2,4})\b',  # 15/02/2024
        r'\b(\d{4})-(\d{2})-(\d{2})\b',            # 2024-02-15
    ]
    
    # Steuernummern-Patterns
    STEUERNR_PATTERNS = [
        r'S(?:t\.?|teuer)?-?Nr\.?[:\s]*([\d\s/\-]+)',
        r'Steuernummer[:\s]*([\d\s/\-]+)',
        r'Finanzamt[:\s]*.*?([\d]{2,3}[\s/\-][\d]{3}[\s/\-][\d]{4})',
    ]
    
    USTID_PATTERN = r'(DE\d{9}|ATU\d{8}|CH\d{9}(?:MWST|TVA|IVA)?|FR[A-Z0-9]{2}\s?\d{9})'
    
    RECHNUNGNR_PATTERNS = [
        r'Rechnungs?(?:nummer|nr| Nr|\.Nr)[:\s.]*([A-Z0-9\-\/_]+)',
        r'Rechnung[:\s.]*(?:Nr\.?|Nummer)?[:\s.]*([A-Z0-9\-\/_]+)',
        r'Invoice[:\s.]*(?:No\.?|Number)?[:\s.]*([A-Z0-9\-\/_]+)',
        r'Facture[:\s.]*(?:n°|No\.?|Numéro)?[:\s.]*([A-Z0-9\-\/_]+)',
        r'Fattura[:\s.]*(?:n\.?|N\.?|Numero)?[:\s.]*([A-Z0-9\-\/_]+)',
    ]
    
    BETRAG_PATTERNS = [
        r'Gesamtbetrag(?: netto)?[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Endbetrag[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Zu zahlen[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Total[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Summe[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Total amount[:\s]*([\d.,]+\s*[€EUR$]?)',
        r'Montant total[:\s]*([\d.,]+\s*[€EUR]?)',
        r'([\d]{1,3}(?:[.,][\d]{3})*[.,][\d]{2})\s*[€EUR]',
    ]
    
    UST_SATZ_PATTERNS = [
        r'(\d{1,2})\s*%\s*(?:USt|MwSt|VAT|IVA|TVA)',
        r'(?:USt|MwSt|VAT|IVA|TVA)[:\s]*(\d{1,2})\s*%',
        r'steuerfrei|tax free|exempt|exonéré',
        r'0\s*%',
    ]
    
    # Mehrsprachige Keywords
    KEYWORDS = {
        'deu': {
            'rechnung': ['Rechnung', 'Rechnungsnummer', 'Rechnungsdatum'],
            'lieferant': ['Lieferant', 'Lieferadresse', 'von'],
            'empfaenger': ['Empfänger', 'Rechnung an', 'Kunde'],
            'gesamtbetrag': ['Gesamtbetrag', 'Endbetrag', 'Zu zahlen', 'Summe'],
        },
        'eng': {
            'rechnung': ['Invoice', 'Invoice Number', 'Invoice Date', 'Bill'],
            'lieferant': ['Supplier', 'Vendor', 'From', 'Seller'],
            'empfaenger': ['Customer', 'Bill To', 'Ship To', 'Buyer'],
            'gesamtbetrag': ['Total', 'Total Amount', 'Grand Total', 'Amount Due'],
        },
        'fra': {
            'rechnung': ['Facture', 'Numéro de facture', 'Date de facture'],
            'lieferant': ['Fournisseur', 'Vendeur', 'De'],
            'empfaenger': ['Client', 'Facturer à', 'Destinataire'],
            'gesamtbetrag': ['Total', 'Montant total', 'Montant à payer'],
        },
        'ita': {
            'rechnung': ['Fattura', 'Numero fattura', 'Data fattura'],
            'lieferant': ['Fornitore', 'Venditore', 'Da'],
            'empfaenger': ['Cliente', 'Destinatario', 'Intestatario'],
            'gesamtbetrag': ['Totale', 'Importo totale', 'Importo da pagare'],
        },
        'spa': {
            'rechnung': ['Factura', 'Número de factura', 'Fecha de factura'],
            'lieferant': ['Proveedor', 'Vendedor', 'De'],
            'empfaenger': ['Cliente', 'Destinatario', 'Facturar a'],
            'gesamtbetrag': ['Total', 'Importe total', 'Cantidad a pagar'],
        }
    }
    
    def __init__(
        self,
        use_ocr: bool = True,
        ocr_preset: str = 'invoice',
        ocr_languages: List[str] = None,
        dpi: int = 300,
        logger: Optional[logging.Logger] = None
    ):
        self.warnings: List[str] = []
        self.use_ocr = use_ocr
        self.ocr_preset = ocr_preset
        self.ocr_languages = ocr_languages or ['deu', 'eng']
        self.dpi = dpi
        self.logger = logger or logging.getLogger(__name__)
        
        # OCR Initialisierung
        self.ocr_engine = None
        if self.use_ocr and ADVANCED_OCR_AVAILABLE:
            try:
                preset_config = self._get_preset_config(ocr_preset)
                preset_config.dpi = dpi
                preset_config.languages = self.ocr_languages
                self.ocr_engine = MultilingualOCR(preset_config)
                self.warnings.append(f"✅ Erweitertes OCR aktiviert ({', '.join(self.ocr_languages)})")
            except Exception as e:
                self.warnings.append(f"⚠️ OCR-Initialisierung fehlgeschlagen: {e}")
                self.use_ocr = False
        elif use_ocr and not ADVANCED_OCR_AVAILABLE:
            self.warnings.append("⚠️ Erweitertes OCR nicht verfügbar (ocr_preprocessor nicht installiert)")
            self.use_ocr = False
    
    def _get_preset_config(self, preset: str) -> OCRConfig:
        """Gibt die OCR-Konfiguration für ein Preset zurück"""
        presets = {
            'scanned': OCRPresets.scanned_document(),
            'low_quality': OCRPresets.low_quality_scan(),
            'invoice': OCRPresets.invoice_multilingual(),
            'fast': OCRPresets.fast_processing(),
            'max_quality': OCRPresets.maximum_quality(),
        }
        return presets.get(preset, OCRPresets.invoice_multilingual())
    
    def extract_text(self, pdf_path: str) -> Tuple[str, bool, float, str, List[str]]:
        """
        Extrahiert Text aus PDF mit erweitertem OCR-Fallback
        
        Returns:
            Tuple von (text, used_ocr, confidence, language, preprocessing_steps)
        """
        text_parts = []
        used_ocr = False
        confidence = 0.0
        language = ""
        preprocessing_steps = []
        
        # Versuche pdfplumber
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                
                combined_text = '\n'.join(text_parts)
                if len(combined_text) > 100:
                    self.logger.info("Text erfolgreich mit pdfplumber extrahiert")
                    return combined_text, False, 1.0, "native", []
            except Exception as e:
                self.warnings.append(f"pdfplumber Fehler: {e}")
        
        # Fallback zu PyPDF2
        if PdfReader:
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    text_parts.append(page.extract_text() or "")
                
                combined_text = '\n'.join(text_parts)
                if len(combined_text) > 100:
                    self.logger.info("Text erfolgreich mit PyPDF2 extrahiert")
                    return combined_text, False, 1.0, "native", []
            except Exception as e:
                self.warnings.append(f"PyPDF2 Fehler: {e}")
        
        # OCR als letzter Fallback
        if self.use_ocr and self.ocr_engine:
            try:
                self.warnings.append(f"🔍 Starte erweiterte OCR-Erkennung (Preset: {self.ocr_preset})...")
                results = self.ocr_engine.extract_from_pdf(pdf_path)
                
                ocr_texts = []
                total_confidence = 0.0
                detected_language = ""
                all_preprocessing = []
                
                for result in results:
                    ocr_texts.append(result.text)
                    total_confidence += result.confidence
                    detected_language = result.language
                    all_preprocessing.extend(result.preprocessing_applied)
                
                if ocr_texts:
                    used_ocr = True
                    confidence = total_confidence / len(results) if results else 0.0
                    preprocessing_steps = list(set(all_preprocessing))
                    language = detected_language
                    
                    self.warnings.append(f"✅ OCR abgeschlossen (Konfidenz: {confidence:.1%}, Sprache: {language})")
                    
                    return '\n'.join(ocr_texts), used_ocr, confidence, language, preprocessing_steps
                    
            except Exception as e:
                self.warnings.append(f"OCR Fehler: {e}")
        
        return "", False, 0.0, "", []
    
    def find_lieferant(self, text: str, language: str = 'deu') -> Dict[str, Optional[str]]:
        """Findet Lieferant (Name und Anschrift)"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        firma = None
        anschrift = None
        
        # Suche nach Firmenbezeichnungen
        company_indicators = [
            r'\b(GmbH|UG|AG|OHG|KG|Gbr|e\.K\.?|e\.Kfr\.|Ltd\.|Inc\.|S\.A\.?|S\.R\.L\.?)\b',
            r'\b(Limited|Corporation|Company|Gesellschaft)\b',
            r'\b(S\.à r\.l\.|Sarl|SNC|SCS)\b',
        ]
        
        for i, line in enumerate(lines[:25]):
            for pattern in company_indicators:
                if re.search(pattern, line, re.I):
                    firma = line.strip()
                    # Suche nach Adresse in den nächsten Zeilen
                    for j in range(i+1, min(i+6, len(lines))):
                        next_line = lines[j]
                        if re.search(r'\d{4,5}\s+\w+', next_line) or \
                           re.search(r'St\.|Strasse|straße|Platz|weg|street|road|strada|avenue|rue|boulevard', next_line, re.I):
                            anschrift = next_line.strip()
                            if re.search(r'\d{4,5}', anschrift):
                                break
                    break
            if firma:
                break
        
        # Fallback: Erste nicht-leere Zeile
        if not firma and lines:
            firma = lines[0]
        
        return {'name': firma, 'anschrift': anschrift}
    
    def find_empfaenger(self, text: str, language: str = 'deu') -> Dict[str, Optional[str]]:
        """Findet Empfänger (Name und Anschrift)"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Mehrsprachige Patterns
        recipient_patterns = [
            r'\b(Rechnung an|Lieferadresse|Kunde|Kundennr|Abweichende Lieferadresse)[:\s]',
            r'\b(Bill To|Ship To|Customer|Sold To)[:\s]',
            r'\b(Facturer à|Livrer à|Client)[:\s]',
            r'\b(Fatturare a|Spedire a|Cliente)[:\s]',
            r'\b(Facturar a|Enviar a|Cliente)[:\s]',
        ]
        
        for i, line in enumerate(lines):
            for pattern in recipient_patterns:
                if re.search(pattern, line, re.I):
                    empfaenger_lines = []
                    for j in range(i+1, min(i+5, len(lines))):
                        empfaenger_lines.append(lines[j])
                    if empfaenger_lines:
                        return {
                            'name': empfaenger_lines[0] if len(empfaenger_lines) > 0 else None,
                            'anschrift': ' '.join(empfaenger_lines[1:]) if len(empfaenger_lines) > 1 else None
                        }
        
        return {'name': None, 'anschrift': None}
    
    def find_steuernummer(self, text: str) -> Optional[str]:
        """Findet Steuernummer (international)"""
        patterns = [
            # Deutschland
            r'S(?:t\.?|teuer)?-?Nr\.?[:\s]*([\d\s/\-]+)',
            r'Steuernummer[:\s]*([\d\s/\-]+)',
            r'Finanzamt[:\s]*.*?([\d]{2,3}[\s/\-][\d]{3}[\s/\-][\d]{4})',
            # Österreich
            r'(?:UID|U\.St\.?-?Id\.?Nr\.?)[:\s]*(ATU\d{8})',
            # Schweiz
            r'(?:MWST|Mehrwertsteuer)[-: Nr\.]*([\d\s]+)',
            # International
            r'Tax Number[:\s]*([A-Z0-9\s\-/]+)',
            r'Numéro de TVA[:\s]*([A-Z]{2}\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        return None
    
    def find_ust_id(self, text: str) -> Optional[str]:
        """Findet USt-IdNr (international)"""
        patterns = [
            r'(DE\d{9})',
            r'(ATU\d{8})',
            r'(CH\d{9}(?:MWST|TVA|IVA)?)',
            r'(FR[A-Z0-9]{2}\s?\d{9})',
            r'(IT\d{11})',
            r'(ES[A-Z]\d{8}[A-Z])',
            r'(NL\d{9}B\d{2})',
            r'(BE\d{10})',
            r'(PL\d{10})',
            r'(CZ\d{8,10})',
            r'(GB\d{9})',
            r'USt-?IdNr?\.?[:\s]*([A-Z]{2}\d{8,12})',
            r'VAT[-: ]*([A-Z]{2}[\s]?\d[\s]?\d[\s]?\d[\s]?\d[\s]?\d[\s]?\d[\s]?\d[\s]?\d[\s]?\d)',
            r'TVA[-: ]*([A-Z]{2}[\s]?\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip().replace(' ', '')
        return None
    
    def find_rechnungsdatum(self, text: str) -> Optional[str]:
        """Findet Rechnungsdatum (mehrsprachig)"""
        patterns = [
            r'(?:Rechnungsdatum|Datum|Date)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            r'(?:Invoice Date|Date of Invoice)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            r'(?:Date de facture)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            r'(?:Data fattura)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            r'(?:Fecha de factura)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            r'(?:vom|from|du|del)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1)
        
        # Fallback: Suche nach Datumsformaten
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    return '.'.join(matches[0])
                return matches[0]
        
        return None
    
    def find_rechnungsnummer(self, text: str) -> Optional[str]:
        """Findet Rechnungsnummer (mehrsprachig)"""
        for pattern in self.RECHNUNGNR_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        return None
    
    def find_positionen(self, text: str) -> bool:
        """Prüft ob Leistungspositionen vorhanden"""
        position_indicators = [
            r'\d+[\s,]\d*\s*(?:Stk|Stück|St\.|pcs|Einheit|Std|h|hours|heures|ore)',
            r'\b(?:Pos|Position|Artikel|Bezeichnung|Item|Description|Article|Posizione|Artículo)\b',
            r'\d+,\d{2}\s*(?:EUR|€)\s*(?:x|\*)\s*\d+',
            r'\d+[\s,]*\d*\s*x\s*[\d.,]+',
        ]
        
        for pattern in position_indicators:
            if re.search(pattern, text, re.I):
                return True
        
        return False
    
    def find_lieferdatum(self, text: str) -> Optional[str]:
        """Findet Lieferdatum oder Leistungszeitraum (mehrsprachig)"""
        patterns = [
            r'(?:Lieferdatum|Leistungsdatum|Leistungszeitraum|Lieferzeit)[:\s]*(.*?)(?:\n|$)',
            r'(?:gewährt am|erbracht am|geliefert am)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            r'(?:Delivery Date|Date of Supply)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            r'(?:Date de livraison)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            r'(?:Data di consegna)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
            r'(?:Fecha de entrega)[:\s]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                result = match.group(1).strip()
                if len(result) < 50:
                    return result
        
        return None
    
    def find_gesamtbetrag(self, text: str) -> Optional[str]:
        """Findet Gesamtbetrag (mehrsprachig)"""
        for pattern in self.BETRAG_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        
        # Fallback: Suche nach Betragsmustern
        amounts = re.findall(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})\s*[€EUR$]?', text)
        if amounts:
            max_amount = 0
            max_str = None
            for amount in amounts:
                try:
                    # Versuche deutsches Format
                    clean = amount.replace('.', '').replace(',', '.')
                    val = float(clean)
                    if val > max_amount:
                        max_amount = val
                        max_str = amount
                except ValueError:
                    continue
            return max_str
        
        return None
    
    def find_ust_satz(self, text: str) -> Optional[str]:
        """Findet USt-Satz (mehrsprachig)"""
        for pattern in self.UST_SATZ_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                if any(x in match.group(0).lower() for x in ['steuerfrei', 'tax free', 'exempt', 'exonéré']):
                    return 'steuerfrei'
                return match.group(1) + '%' if match.groups() else match.group(0)
        
        return None
    
    def validate(self, pdf_path: str) -> ValidationResult:
        """Validiert eine Rechnungs-PDF mit erweitertem OCR"""
        self.warnings = []
        
        # Text-Extraktion mit OCR-Metadaten
        text, used_ocr, ocr_confidence, ocr_language, preprocessing = self.extract_text(pdf_path)
        
        if used_ocr:
            self.warnings.append(f"✅ OCR verwendet ({ocr_language}, Konfidenz: {ocr_confidence:.1%})")
        
        if not text:
            return ValidationResult(
                filename=Path(pdf_path).name,
                is_valid=False,
                score=0,
                max_score=11,
                confidence=0.0,
                missing_fields=['alle'],
                extracted_data={},
                warnings=['Kein Text extrahierbar'],
                zugferd_compatible=False,
                ocr_used=used_ocr,
                ocr_confidence=ocr_confidence,
                ocr_language=ocr_language,
                preprocessing_applied=preprocessing
            )
        
        # Extrahiere Daten
        lieferant = self.find_lieferant(text, ocr_language or 'deu')
        empfaenger = self.find_empfaenger(text, ocr_language or 'deu')
        
        extracted = {
            'lieferant_name': lieferant['name'],
            'lieferant_anschrift': lieferant['anschrift'],
            'empfaenger_name': empfaenger['name'],
            'empfaenger_anschrift': empfaenger['anschrift'],
            'steuernummer': self.find_steuernummer(text),
            'ust_id': self.find_ust_id(text),
            'rechnungsdatum': self.find_rechnungsdatum(text),
            'rechnungsnummer': self.find_rechnungsnummer(text),
            'lieferdatum': self.find_lieferdatum(text),
            'gesamtbetrag': self.find_gesamtbetrag(text),
            'ust_satz': self.find_ust_satz(text),
            'positionen_vorhanden': self.find_positionen(text),
            'erkannte_sprache': ocr_language,
        }
        
        # Validierungs-Checks
        checks = [
            ('lieferant_name', extracted['lieferant_name'] is not None),
            ('lieferant_anschrift', extracted['lieferant_anschrift'] is not None),
            ('steuernummer_oder_ustid', extracted['steuernummer'] is not None or extracted['ust_id'] is not None),
            ('rechnungsdatum', extracted['rechnungsdatum'] is not None),
            ('rechnungsnummer', extracted['rechnungsnummer'] is not None),
            ('positionen', extracted['positionen_vorhanden']),
            ('lieferdatum', extracted['lieferdatum'] is not None),
            ('gesamtbetrag', extracted['gesamtbetrag'] is not None),
            ('ust_satz', extracted['ust_satz'] is not None),
        ]
        
        score = sum(1 for _, passed in checks if passed)
        max_score = len(checks)
        missing = [field for field, passed in checks if not passed]
        
        # Berechne Gesamtkonfidenz
        base_confidence = score / max_score if max_score > 0 else 0
        if used_ocr:
            total_confidence = (base_confidence * 0.6) + (ocr_confidence * 0.4)
        else:
            total_confidence = base_confidence
        
        is_valid = score >= 7
        
        # ZUGFeRD-Kompatibilität
        zugferd_compatible = (
            extracted['lieferant_name'] and
            extracted['rechnungsnummer'] and
            extracted['rechnungsdatum'] and
            (extracted['steuernummer'] or extracted['ust_id'])
        )
        
        return ValidationResult(
            filename=Path(pdf_path).name,
            is_valid=is_valid,
            score=score,
            max_score=max_score,
            confidence=total_confidence,
            missing_fields=missing,
            extracted_data=extracted,
            warnings=self.warnings,
            zugferd_compatible=zugferd_compatible,
            ocr_used=used_ocr,
            ocr_confidence=ocr_confidence,
            ocr_language=ocr_language,
            preprocessing_applied=preprocessing
        )
    
    def generate_zugferd(self, pdf_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """Generiert ZUGFeRD aus validiertem PDF"""
        if not ZUGFERD_AVAILABLE:
            print("❌ ZUGFeRD-Generator nicht verfügbar")
            return None
        
        result = self.validate(pdf_path)
        
        if not result.zugferd_compatible:
            print("❌ Rechnung ist nicht ZUGFeRD-kompatibel")
            print(f"   Fehlende Felder: {result.missing_fields}")
            return None
        
        data = result.extracted_data
        
        # Parse Betrag
        betrag_str = data['gesamtbetrag'] or "0"
        betrag_str = betrag_str.replace('.', '').replace(',', '.').replace('€', '').strip()
        try:
            gesamtbetrag = float(betrag_str)
        except ValueError:
            gesamtbetrag = 0.0
        
        # Parse USt-Satz
        ust_satz = 19.0
        if data['ust_satz']:
            match = re.search(r'(\d+)', data['ust_satz'])
            if match:
                ust_satz = float(match.group(1))
        
        # Erstelle Invoice
        seller = Party(
            name=data['lieferant_name'] or "Unbekannt",
            street=data['lieferant_anschrift'] or "",
            zip="",
            city="",
            vat_id=data['ust_id'],
            tax_number=data['steuernummer']
        )
        
        buyer = Party(
            name=data['empfaenger_name'] or "Unbekannt",
            street=data['empfaenger_anschrift'] or "",
            zip="",
            city=""
        )
        
        invoice = Invoice(
            invoice_number=data['rechnungsnummer'] or "UNBEKANNT",
            invoice_date=data['rechnungsdatum'] or datetime.now().strftime("%Y-%m-%d"),
            seller=seller,
            buyer=buyer,
            items=[
                InvoiceItem(
                    description="Rechnungsbetrag",
                    quantity=1,
                    price=gesamtbetrag / (1 + ust_satz/100),
                    vat_rate=ust_satz
                )
            ]
        )
        
        # Generiere ZUGFeRD
        generator = ZUGFeRDGenerator()
        zugferd_bytes = generator.generate_zugferd(invoice)
        
        # Speichere
        if not output_path:
            output_path = str(Path(pdf_path).with_suffix('.zugferd.zip'))
        
        with open(output_path, 'wb') as f:
            f.write(zugferd_bytes)
        
        return output_path


def batch_validate(
    folder_path: str,
    output_json: str = "validation_results.json",
    ocr_preset: str = 'invoice',
    languages: List[str] = None
) -> Dict:
    """Validiert alle PDFs in einem Ordner mit erweitertem OCR"""
    folder = Path(folder_path)
    pdfs = list(folder.glob("*.pdf"))
    
    results = []
    validator = EnhancedGoBDValidator(
        use_ocr=True,
        ocr_preset=ocr_preset,
        ocr_languages=languages or ['deu', 'eng']
    )
    
    print(f"🔍 Validiere {len(pdfs)} PDF-Dateien mit erweitertem OCR...")
    print(f"   OCR-Preset: {ocr_preset}")
    print(f"   Sprachen: {', '.join(languages or ['deu', 'eng'])}\n")
    
    for i, pdf in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] Verarbeite: {pdf.name}")
        result = validator.validate(str(pdf))
        results.append(result.to_dict())
        
        status = "✅" if result.is_valid else "❌"
        ocr_info = f"(OCR: {result.ocr_language}, {result.ocr_confidence:.0%})" if result.ocr_used else "(Native)"
        print(f"   {status} {result.score}/{result.max_score} Punkte {ocr_info}")
    
    # Speichere Ergebnisse
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Ergebnisse gespeichert in: {output_json}")
    
    valid_count = sum(1 for r in results if r['is_valid'])
    zugferd_count = sum(1 for r in results if r['zugferd_compatible'])
    ocr_count = sum(1 for r in results if r['ocr_used'])
    
    return {
        'total': len(results),
        'valid': valid_count,
        'invalid': len(results) - valid_count,
        'zugferd_compatible': zugferd_count,
        'ocr_used': ocr_count,
        'results_file': output_json
    }


def main():
    parser = argparse.ArgumentParser(
        description=f'GoBD-Rechnungsvalidator v{EnhancedGoBDValidator.VERSION}',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
OCR Presets:
  scanned      - Optimal für gescannte Dokumente (300 DPI)
  low_quality  - Für schlechte Scan-Qualität (400 DPI)
  invoice      - Für mehrsprachige Rechnungen (Standard)
  fast         - Schnelle Verarbeitung (150 DPI)
  max_quality  - Maximale Qualität (langsam)

Beispiele:
  %(prog)s rechnung.pdf
  %(prog)s gescannt.pdf --preset scanned --lang deu eng
  %(prog)s ./rechnungen/ --batch --preset invoice --lang deu eng fra
  %(prog)s rechnung.pdf --zugferd --output rechnung.zugferd.zip
        """
    )
    parser.add_argument('pdf', nargs='?', help='PDF-Datei oder Ordner')
    parser.add_argument('--batch', action='store_true', help='Batch-Verarbeitung')
    parser.add_argument('--zugferd', action='store_true', help='ZUGFeRD generieren')
    parser.add_argument('--output', '-o', help='Ausgabedatei')
    parser.add_argument('--no-ocr', action='store_true', help='OCR deaktivieren')
    parser.add_argument('--preset', default='invoice',
                       choices=['scanned', 'low_quality', 'invoice', 'fast', 'max_quality'],
                       help='OCR-Preset (Standard: invoice)')
    parser.add_argument('--lang', nargs='+', default=['deu', 'eng'],
                       help='Sprachen für OCR (z.B. deu eng fra)')
    parser.add_argument('--dpi', type=int, default=300,
                       help='DPI für OCR (Standard: 300)')
    parser.add_argument('--json', action='store_true', help='JSON-Output')
    
    args = parser.parse_args()
    
    if not args.pdf:
        parser.print_help()
        return 1
    
    if args.batch:
        stats = batch_validate(
            args.pdf,
            args.output or "validation_results.json",
            ocr_preset=args.preset,
            languages=args.lang
        )
        print(f"\n{'='*50}")
        print(f"📊 ZUSAMMENFASSUNG")
        print(f"{'='*50}")
        print(f"Geprüft:      {stats['total']}")
        print(f"✅ Valide:     {stats['valid']}")
        print(f"❌ Unvalide:   {stats['invalid']}")
        print(f"🧾 ZUGFeRD:    {stats['zugferd_compatible']}")
        print(f"🔍 OCR genutzt: {stats['ocr_used']}")
        return 0
    
    # Einzelverarbeitung
    validator = EnhancedGoBDValidator(
        use_ocr=not args.no_ocr,
        ocr_preset=args.preset,
        ocr_languages=args.lang,
        dpi=args.dpi
    )
    
    result = validator.validate(args.pdf)
    
    if args.zugferd and result.zugferd_compatible:
        zugferd_path = validator.generate_zugferd(args.pdf, args.output)
        if zugferd_path:
            print(f"✅ ZUGFeRD erstellt: {zugferd_path}")
    
    if args.json:
        print(result.to_json())
    else:
        print(f"\n{'='*50}")
        print(f"📄 {result.filename}")
        print(f"{'='*50}")
        print(f"Status:      {'✅ VALIDE' if result.is_valid else '❌ UNVALIDE'}")
        print(f"Score:       {result.score}/{result.max_score} ({result.confidence:.0%})")
        print(f"ZUGFeRD:     {'✅' if result.zugferd_compatible else '❌'}")
        
        if result.ocr_used:
            print(f"OCR:         ✅ Ja")
            print(f"  Sprache:   {result.ocr_language}")
            print(f"  Konfidenz: {result.ocr_confidence:.1%}")
            if result.preprocessing_applied:
                print(f"  Preprocessing: {', '.join(result.preprocessing_applied)}")
        
        if result.missing_fields:
            print(f"\nFehlende Pflichtfelder:")
            for field in result.missing_fields:
                print(f"  - {field}")
        
        print(f"\nExtrahierte Daten:")
        for key, value in result.extracted_data.items():
            if value:
                print(f"  {key}: {value}")
        
        if result.warnings:
            print(f"\nWarnungen:")
            for warning in result.warnings:
                print(f"  ⚠️  {warning}")
    
    return 0 if result.is_valid else 1


if __name__ == '__main__':
    sys.exit(main())
