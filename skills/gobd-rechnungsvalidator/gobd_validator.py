#!/usr/bin/env python3
"""
GoBD-Rechnungsvalidator
Automatische Validierung von Rechnungs-PDFs auf GoBD-Konformität

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
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None


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
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class GoBDValidator:
    """Validiert Rechnungs-PDFs auf GoBD-Konformität"""
    
    # Deutsche Datums-Patterns
    DATE_PATTERNS = [
        r'\b(\d{1,2})[.](\d{1,2})[.](\d{2,4})\b',  # 15.02.2024
        r'\b(\d{1,2})[/](\d{1,2})[/](\d{2,4})\b',  # 15/02/2024
        r'\b(\d{4})-(\d{2})-(\d{2})\b',            # 2024-02-15
    ]
    
    # Steuernummern-Patterns (verschiedene Bundesländer)
    STEUERNR_PATTERNS = [
        r'S(?:t\.?|teuer)?-?Nr\.?[:\s]*([\d\s/\-]+)',
        r'Steuernummer[:\s]*([\d\s/\-]+)',
        r'Finanzamt[:\s]*.*?([\d]{2,3}[\s/\-][\d]{3}[\s/\-][\d]{4})',
    ]
    
    # USt-IdNr Pattern (EU-weit)
    USTID_PATTERN = r'(DE\d{9}|ATU\d{8}|CH\d{9}(?:MWST|TVA|IVA)?|FR[A-Z0-9]{2}\s?\d{9})'
    
    # Rechnungsnummer-Patterns
    RECHNUNGNR_PATTERNS = [
        r'Rechnungs?(?:nummer|nr| Nr|\.Nr)[:\s.]*([A-Z0-9\-\/_]+)',
        r'Rechnung[:\s.]*(?:Nr\.?|Nummer)?[:\s.]*([A-Z0-9\-\/_]+)',
        r'Invoice[:\s.]*(?:No\.?|Number)?[:\s.]*([A-Z0-9\-\/_]+)',
    ]
    
    # Betrags-Patterns
    BETRAG_PATTERNS = [
        r'Gesamtbetrag(?: netto)?[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Endbetrag[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Zu zahlen[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Total[:\s]*([\d.,]+\s*[€EUR]?)',
        r'Summe[:\s]*([\d.,]+\s*[€EUR]?)',
        r'([\d]{1,3}(?:[.,][\d]{3})*[.,][\d]{2})\s*[€EUR]',
    ]
    
    # USt-Satz Patterns
    UST_SATZ_PATTERNS = [
        r'(\d{1,2})\s*%\s*(?:USt|MwSt|VAT)',
        r'(?:USt|MwSt|VAT)[:\s]*(\d{1,2})\s*%',
        r'steuerfrei',
        r'0\s*%',
    ]
    
    def __init__(self):
        self.warnings: List[str] = []
    
    def extract_text(self, pdf_path: str) -> str:
        """Extrahiert Text aus PDF"""
        text_parts = []
        
        # Versuche pdfplumber (bessere Tabellen-Extraktion)
        if pdfplumber:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
            except Exception as e:
                self.warnings.append(f"pdfplumber Fehler: {e}")
        
        # Fallback zu PyPDF2
        if not text_parts and PdfReader:
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    text_parts.append(page.extract_text() or "")
            except Exception as e:
                self.warnings.append(f"PyPDF2 Fehler: {e}")
        
        full_text = "\n".join(text_parts)
        return full_text if full_text else ""
    
    def find_lieferant(self, text: str) -> Dict[str, Optional[str]]:
        """Findet Lieferant (Name und Anschrift)"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Suche nach Firmenbezeichnungen
        firma = None
        anschrift = None
        
        for i, line in enumerate(lines[:20]):  # Nur erste 20 Zeilen
            # GmbH, UG, AG, etc.
            if re.search(r'\b(GmbH|UG|AG|OHG|KG|Gbr|e\.K\.?|e\.Kfr\.|Einzelunternehmen)\b', line, re.I):
                firma = line.strip()
                # Anschrift in nächsten 3 Zeilen
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j]
                    if re.search(r'\d{5}\s+\w+', next_line) or re.search(r'St\.|Strasse|straße|Platz|weg\b', next_line, re.I):
                        anschrift = next_line.strip()
                        # Vollständige Anschrift (PLZ + Ort)
                        if re.search(r'\d{5}', anschrift):
                            break
                break
        
        # Fallback: Erste nicht-leere Zeile als Firma
        if not firma and lines:
            firma = lines[0]
        
        return {
            'name': firma,
            'anschrift': anschrift
        }
    
    def find_empfaenger(self, text: str) -> Dict[str, Optional[str]]:
        """Findet Empfänger (Name und Anschrift)"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Suche nach "Rechnung an:" oder ähnlichem
        for i, line in enumerate(lines):
            if re.search(r'\b(Rechnung an|Lieferadresse|Kunde|Kundennr)[:\s]', line, re.I):
                # Nächste 2-3 Zeilen = Empfänger
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
        
        # Suche nach explizitem Hinweis
        match = re.search(r'USt-?IdNr?\.?[:\s]*([A-Z]{2}\d{8,12})', text, re.I)
        if match:
            return match.group(1)
        
        return None
    
    def find_rechnungsdatum(self, text: str) -> Optional[str]:
        """Findet Rechnungsdatum"""
        # Suche nach explizitem Hinweis
        date_patterns = [
            r'(?:Rechnungsdatum|Datum|Date)[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
            r'(?:vom|from)[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1)
        
        # Suche allgemein nach Datumsformaten
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                # Nimm das erste gefundene Datum
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
        # Suche nach Tabellen-Strukturen oder Mengenangaben
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
                if len(result) < 50:  # Keine riesigen Texte
                    return result
        
        return None
    
    def find_gesamtbetrag(self, text: str) -> Optional[str]:
        """Findet Gesamtbetrag"""
        for pattern in self.BETRAG_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        
        # Suche nach größtem Betrag im Dokument
        amounts = re.findall(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})\s*[€EUR]?', text)
        if amounts:
            # Konvertiere und finde Maximum
            max_amount = 0
            max_str = None
            for amount in amounts:
                try:
                    # Normalisiere: 1.234,56 -> 1234.56
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
        
        # Text extrahieren
        text = self.extract_text(pdf_path)
        
        if not text:
            return ValidationResult(
                filename=Path(pdf_path).name,
                is_valid=False,
                score=0,
                max_score=11,
                confidence=0.0,
                missing_fields=['alle'],
                extracted_data={},
                warnings=['Kein Text extrahierbar - gescanntes PDF?']
            )
        
        # Daten extrahieren
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
        
        # GoBD-Pflichtfelder prüfen
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
        
        missing = [name for name, found in checks if not found]
        score = sum(1 for _, found in checks if found)
        max_score = len(checks)
        
        # Confidence berechnen (wie sicher sind wir?)
        confidence = score / max_score
        
        # Warnung wenn nur Steuernummer gefunden (nicht USt-IdNr)
        if extracted['steuernummer'] and not extracted['ust_id']:
            self.warnings.append('USt-IdNr nicht gefunden - Steuernummer verwendet')
        
        return ValidationResult(
            filename=Path(pdf_path).name,
            is_valid=score >= 7,  # Mindestens 7 von 9 für "gültig"
            score=score,
            max_score=max_score,
            confidence=round(confidence, 2),
            missing_fields=missing,
            extracted_data=extracted,
            warnings=self.warnings
        )


def validate_rechnung(pdf_path: str) -> ValidationResult:
    """Hilfsfunktion für einfache Validierung"""
    validator = GoBDValidator()
    return validator.validate(pdf_path)


def main():
    parser = argparse.ArgumentParser(
        description='GoBD-Rechnungsvalidator - Prüft Rechnungs-PDFs auf Konformität'
    )
    parser.add_argument('path', help='Pfad zur PDF-Rechnung oder Ordner')
    parser.add_argument('--batch', '-b', action='store_true', help='Batch-Verarbeitung für Ordner')
    parser.add_argument('--output', '-o', help='Ausgabedatei für JSON-Report')
    parser.add_argument('--quiet', '-q', action='store_true', help='Nur Ergebnis ausgeben')
    
    args = parser.parse_args()
    
    validator = GoBDValidator()
    path = Path(args.path)
    
    results = []
    
    if args.batch and path.is_dir():
        pdf_files = list(path.glob('*.pdf'))
        if not args.quiet:
            print(f"🔍 Verarbeite {len(pdf_files)} PDFs...\n")
        
        for pdf_file in pdf_files:
            result = validator.validate(str(pdf_file))
            results.append(result)
            
            if not args.quiet:
                status = "✅" if result.is_valid else "❌"
                print(f"{status} {result.filename}: {result.score}/{result.max_score} ({result.confidence*100:.0f}%)")
        
        if not args.quiet:
            print(f"\n📊 Zusammenfassung:")
            valid_count = sum(1 for r in results if r.is_valid)
            print(f"   Gültig: {valid_count}/{len(results)}")
            print(f"   Ungültig: {len(results) - valid_count}/{len(results)}")
    
    else:
        result = validator.validate(str(path))
        results.append(result)
        
        if args.quiet:
            print('valid' if result.is_valid else 'invalid')
        else:
            print(result.to_json())
    
    if args.output:
        output_data = [r.to_dict() for r in results]
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        if not args.quiet:
            print(f"\n💾 Report gespeichert: {args.output}")


if __name__ == '__main__':
    main()
