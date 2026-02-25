#!/usr/bin/env python3
"""
GoBD-Rechnungsvalidator v2.0
Mit ZUGFeRD-Export und OCR-Unterstützung

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
"""

import re
import json
import argparse
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

# OCR Support
try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

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
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class GoBDValidator:
    """Validiert Rechnungs-PDFs auf GoBD-Konformität"""
    
    VERSION = "2.0.0"
    
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
    ]
    
    BETRAG_PATTERNS = [
        r'Gesamtbetrag(?: netto)?[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Endbetrag[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Zu zahlen[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Total[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Summe[:\s]*([\d.,]+\s*[€EUR]?)',
        r'([\d]{1,3}(?:[.,][\d]{3})*[.,][\d]{2})\s*[€EUR]',
    ]
    
    UST_SATZ_PATTERNS = [
        r'(\d{1,2})\s*%\s*(?:USt|MwSt|VAT)',
        r'(?:USt|MwSt|VAT)[:\s]*(\d{1,2})\s*%',
        r'steuerfrei',
        r'0\s*%',
    ]
    
    def __init__(self, use_ocr: bool = True):
        self.warnings: List[str] = []
        self.use_ocr = use_ocr and OCR_AVAILABLE
        
        if self.use_ocr:
            self.warnings.append("✅ OCR aktiviert (Tesseract)")
        elif use_ocr and not OCR_AVAILABLE:
            self.warnings.append("⚠️  OCR nicht verfügbar (pytesseract/pdf2image nicht installiert)")
    
    def extract_text(self, pdf_path: str) -> Tuple[str, bool]:
        """Extrahiert Text aus PDF (mit OCR-Fallback)
        
        Returns:
            Tuple[text, used_ocr]
        """
        text_parts = []
        used_ocr = False
        
        # Versuche pdfplumber
        if PDFPLUMBER_AVAILABLE:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                
                if text_parts and len(''.join(text_parts)) > 100:
                    return '\n'.join(text_parts), False
            except Exception as e:
                self.warnings.append(f"pdfplumber Fehler: {e}")
        
        # Fallback zu PyPDF2
        if PdfReader:
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    text_parts.append(page.extract_text() or "")
                
                full_text = '\n'.join(text_parts)
                if len(full_text) > 100:
                    return full_text, False
            except Exception as e:
                self.warnings.append(f"PyPDF2 Fehler: {e}")
        
        # OCR als letzter Fallback
        if self.use_ocr:
            try:
                self.warnings.append("🔍 Starte OCR-Erkennung...")
                images = convert_from_path(pdf_path, dpi=300)
                ocr_texts = []
                for i, image in enumerate(images):
                    text = pytesseract.image_to_string(image, lang='deu')
                    ocr_texts.append(text)
                
                if ocr_texts:
                    used_ocr = True
                    return '\n'.join(ocr_texts), True
            except Exception as e:
                self.warnings.append(f"OCR Fehler: {e}")
        
        return "", False
    
    def find_lieferant(self, text: str) -> Dict[str, Optional[str]]:
        """Findet Lieferant (Name und Anschrift)"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        firma = None
        anschrift = None
        
        for i, line in enumerate(lines[:20]):
            if re.search(r'\b(GmbH|UG|AG|OHG|KG|Gbr|e\.K\.?|e\.Kfr\.)\b', line, re.I):
                firma = line.strip()
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j]
                    if re.search(r'\d{5}\s+\w+', next_line) or re.search(r'St\.|Strasse|straße|Platz|weg\b', next_line, re.I):
                        anschrift = next_line.strip()
                        if re.search(r'\d{5}', anschrift):
                            break
                break
        
        if not firma and lines:
            firma = lines[0]
        
        return {'name': firma, 'anschrift': anschrift}
    
    def find_empfaenger(self, text: str) -> Dict[str, Optional[str]]:
        """Findet Empfänger (Name und Anschrift)"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        for i, line in enumerate(lines):
            if re.search(r'\b(Rechnung an|Lieferadresse|Kunde|Kundennr)[:\s]', line, re.I):
                empfaenger_lines = []
                for j in range(i+1, min(i+4, len(lines))):
                    empfaenger_lines.append(lines[j])
                if empfaenger_lines:
                    return {
                        'name': empfaenger_lines[0] if len(empfaenger_lines) > 0 else None,
                        'anschrift': ' '.join(empfaenger_lines[1:]) if len(empfaenger_lines) > 1 else None
                    }
        
        return {'name': None, 'anschrift': None}
    
    def find_steuernummer(self, text: str) -> Optional[str]:
        """Findet Steuernummer"""
        for pattern in self.STEUERNR_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        return None
    
    def find_ust_id(self, text: str) -> Optional[str]:
        """Findet USt-IdNr"""
        match = re.search(self.USTID_PATTERN, text, re.I)
        if match:
            return match.group(1).strip()
        
        match = re.search(r'USt-?IdNr?\.?[:\s]*([A-Z]{2}\d{8,12})', text, re.I)
        if match:
            return match.group(1)
        
        return None
    
    def find_rechnungsdatum(self, text: str) -> Optional[str]:
        """Findet Rechnungsdatum"""
        date_patterns = [
            r'(?:Rechnungsdatum|Datum|Date)[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
            r'(?:vom|from)[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1)
        
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    return '.'.join(matches[0])
                return matches[0]
        
        return None
    
    def find_rechnungsnummer(self, text: str) -> Optional[str]:
        """Findet Rechnungsnummer"""
        for pattern in self.RECHNUNGNR_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        return None
    
    def find_positionen(self, text: str) -> bool:
        """Prüft ob Leistungspositionen vorhanden"""
        position_indicators = [
            r'\d+[\s,]\d*\s*(?:Stk|Stück|St\.|pcs|Einheit|Std|h)',
            r'\b(?:Pos|Position|Artikel|Bezeichnung)\b',
            r'\d+,\d{2}\s*(?:EUR|€)\s*(?:x|\*)\s*\d+',
        ]
        
        for pattern in position_indicators:
            if re.search(pattern, text, re.I):
                return True
        
        return False
    
    def find_lieferdatum(self, text: str) -> Optional[str]:
        """Findet Lieferdatum oder Leistungszeitraum"""
        patterns = [
            r'(?:Lieferdatum|Leistungsdatum|Leistungszeitraum|Lieferzeit)[:\s]*(.*?)(?:\n|$)',
            r'(?:gewährt am|erbracht am|geliefert am)[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                result = match.group(1).strip()
                if len(result) < 50:
                    return result
        
        return None
    
    def find_gesamtbetrag(self, text: str) -> Optional[str]:
        """Findet Gesamtbetrag"""
        for pattern in self.BETRAG_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        
        amounts = re.findall(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})\s*[€EUR]?', text)
        if amounts:
            max_amount = 0
            max_str = None
            for amount in amounts:
                try:
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
        """Findet USt-Satz"""
        for pattern in self.UST_SATZ_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                if 'steuerfrei' in match.group(0).lower():
                    return 'steuerfrei'
                return match.group(1) + '%' if match.groups() else match.group(0)
        
        return None
    
    def validate(self, pdf_path: str) -> ValidationResult:
        """Validiert eine Rechnungs-PDF"""
        self.warnings = []
        
        text, used_ocr = self.extract_text(pdf_path)
        
        if used_ocr:
            self.warnings.append("✅ OCR wurde verwendet")
        
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
                zugferd_compatible=False
            )
        
        lieferant = self.find_lieferant(text)
        empfaenger = self.find_empfaenger(text)
        
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
        }
        
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
        
        is_valid = score >= 7
        confidence = score / max_score
        
        # ZUGFeRD-Kompatibilität prüfen
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
            confidence=confidence,
            missing_fields=missing,
            extracted_data=extracted,
            warnings=self.warnings,
            zugferd_compatible=zugferd_compatible
        )
    
    def generate_zugferd(self, pdf_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """Generiert ZUGFeRD aus validiertem PDF
        
        Returns:
            Pfad zur generierten ZUGFeRD-Datei oder None bei Fehler
        """
        if not ZUGFERD_AVAILABLE:
            print("❌ ZUGFeRD-Generator nicht verfügbar")
            return None
        
        # Validiere zuerst
        result = self.validate(pdf_path)
        
        if not result.zugferd_compatible:
            print("❌ Rechnung ist nicht ZUGFeRD-kompatibel")
            print(f"   Fehlende Felder: {result.missing_fields}")
            return None
        
        # Extrahiere Daten
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
        
        # Erstelle Invoice-Objekt
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


def batch_validate(folder_path: str, output_json: str = "validation_results.json") -> Dict:
    """Validiert alle PDFs in einem Ordner"""
    folder = Path(folder_path)
    pdfs = list(folder.glob("*.pdf"))
    
    results = []
    validator = GoBDValidator(use_ocr=True)
    
    print(f"🔍 Validiere {len(pdfs)} PDF-Dateien...\n")
    
    for pdf in pdfs:
        result = validator.validate(str(pdf))
        results.append(result.to_dict())
        
        status = "✅" if result.is_valid else "❌"
        print(f"{status} {pdf.name}: {result.score}/{result.max_score} Punkte")
    
    # Speichere Ergebnisse
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Ergebnisse gespeichert in: {output_json}")
    
    valid_count = sum(1 for r in results if r['is_valid'])
    zugferd_count = sum(1 for r in results if r['zugferd_compatible'])
    
    return {
        'total': len(results),
        'valid': valid_count,
        'invalid': len(results) - valid_count,
        'zugferd_compatible': zugferd_count,
        'results_file': output_json
    }


def main():
    parser = argparse.ArgumentParser(description='GoBD-Rechnungsvalidator v2.0')
    parser.add_argument('pdf', nargs='?', help='PDF-Datei oder Ordner')
    parser.add_argument('--batch', action='store_true', help='Batch-Verarbeitung')
    parser.add_argument('--zugferd', action='store_true', help='ZUGFeRD generieren')
    parser.add_argument('--output', '-o', help='Ausgabedatei')
    parser.add_argument('--no-ocr', action='store_true', help='OCR deaktivieren')
    parser.add_argument('--json', action='store_true', help='JSON-Output')
    
    args = parser.parse_args()
    
    if not args.pdf:
        parser.print_help()
        return 1
    
    if args.batch:
        # Batch-Verarbeitung
        stats = batch_validate(args.pdf, args.output or "validation_results.json")
        print(f"\n{'='*50}")
        print(f"📊 ZUSAMMENFASSUNG")
        print(f"{'='*50}")
        print(f"Geprüft:      {stats['total']}")
        print(f"✅ Valide:     {stats['valid']}")
        print(f"❌ Unvalide:   {stats['invalid']}")
        print(f"🧾 ZUGFeRD:    {stats['zugferd_compatible']}")
        return 0
    
    # Einzelverarbeitung
    validator = GoBDValidator(use_ocr=not args.no_ocr)
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
        print(f"Status:     {'✅ VALIDE' if result.is_valid else '❌ UNVALIDE'}")
        print(f"Score:      {result.score}/{result.max_score} ({result.confidence:.0%})")
        print(f"ZUGFeRD:    {'✅' if result.zugferd_compatible else '❌'}")
        
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
