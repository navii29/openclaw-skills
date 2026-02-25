#!/usr/bin/env python3
"""
PDF Rechnung zu DATEV CSV
Extract invoice data from PDFs and export to DATEV-compatible format.
"""

import re
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Try to import PyPDF2, fallback to basic regex
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFInvoiceParser:
    """Parse German PDF invoices and export to DATEV format."""
    
    # German date patterns
    DATE_PATTERNS = [
        r'(\d{1,2})[\.\-/](\d{1,2})[\.\-/](\d{2,4})',  # DD.MM.YYYY
        r'(\d{1,2})\.\s*(\w+)\s*(\d{4})',  # DD. Month YYYY (German)
    ]
    
    # German amount patterns
    AMOUNT_PATTERNS = [
        r'(?:Gesamtbetrag|Rechnungsbetrag|Summe|Total|Endbetrag)[\s:]*([\d\.,]+)\s*[€]?',
        r'(?: brutto|Brutto)[\s:]*([\d\.,]+)',
        r'(?:Zu zahlen|Fälliger Betrag)[\s:]*([\d\.,]+)\s*[€]?',
    ]
    
    # Invoice number patterns
    INVOICE_PATTERNS = [
        r'(?:Rechnungsnummer|Rechnung Nr\.|Rechnung-Nr\.|Invoice No\.?)[\s:]*(\S+)',
        r'(?:Rechnung|Invoice)[\s#]*(\d[\w\-/]*)',
    ]
    
    # VAT patterns
    VAT_PATTERNS = [
        r'MwSt\.?\s*(19|7)[\s%]*[\.:]?\s*([\d\.,]+)',
        r'USt\.?\s*(19|7)[\s%].*?([\d\.,]+)',
        r'(?:zzgl\.?|plus|inkl\.)?\s*MwSt\.?\s*(19|7)',
    ]
    
    # Vendor patterns
    VENDOR_PATTERNS = [
        r'(?:Von|From|Lieferant)[:\s]+([A-Za-z][A-Za-z\s\.]+)',
        r'^([A-Z][A-Za-z\s]+GmbH|[A-Z][A-Za-z\s]+AG|[A-Z][A-Za-z\s]+OHG)',
    ]
    
    # Default DATEV chart of accounts for common vendors
    DEFAULT_ACCOUNTS = {
        'amazon': {'konto': '3400', 'gegenkonto': '1200', 'steuer': '19'},
        'telekom': {'konto': '6300', 'gegenkonto': '1200', 'steuer': '19'},
        'vodafone': {'konto': '6300', 'gegenkonto': '1200', 'steuer': '19'},
        'zalando': {'konto': '3400', 'gegenkonto': '1200', 'steuer': '19'},
        'hm': {'konto': '3400', 'gegenkonto': '1200', 'steuer': '19'},
        'bauhaus': {'konto': '6300', 'gegenkonto': '1200', 'steuer': '19'},
        'obi': {'konto': '6300', 'gegenkonto': '1200', 'steuer': '19'},
        'ikea': {'konto': '6300', 'gegenkonto': '1200', 'steuer': '19'},
        'conrad': {'konto': '6300', 'gegenkonto': '1200', 'steuer': '19'},
        'rewe': {'konto': '6400', 'gegenkonto': '1200', 'steuer': '7'},
        'edeka': {'konto': '6400', 'gegenkonto': '1200', 'steuer': '7'},
        'lidl': {'konto': '6400', 'gegenkonto': '1200', 'steuer': '7'},
        'aldi': {'konto': '6400', 'gegenkonto': '1200', 'steuer': '7'},
        'shell': {'konto': '6600', 'gegenkonto': '1200', 'steuer': '19'},
        'aral': {'konto': '6600', 'gegenkonto': '1200', 'steuer': '19'},
        'db': {'konto': '6500', 'gegenkonto': '1200', 'steuer': '19'},
        'bahn': {'konto': '6500', 'gegenkonto': '1200', 'steuer': '19'},
        'lufthansa': {'konto': '6500', 'gegenkonto': '1200', 'steuer': '19'},
        'adobe': {'konto': '4900', 'gegenkonto': '1200', 'steuer': '19'},
        'microsoft': {'konto': '4900', 'gegenkonto': '1200', 'steuer': '19'},
        'google': {'konto': '4900', 'gegenkonto': '1200', 'steuer': '19'},
        'stripe': {'konto': '1200', 'gegenkonto': '8400', 'steuer': '19'},
        'paypal': {'konto': '1210', 'gegenkonto': '8400', 'steuer': '19'},
    }
    
    def __init__(self, pdf_text: str):
        self.text = pdf_text
        self.lines = pdf_text.split('\n')
    
    def _find_pattern(self, patterns: List[str], text: str) -> Optional[str]:
        """Find first matching pattern in text."""
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                return matches[0]
        return None
    
    def extract_invoice_number(self) -> Optional[str]:
        """Extract invoice number from text."""
        result = self._find_pattern(self.INVOICE_PATTERNS, self.text)
        if result:
            # Clean up the result
            if isinstance(result, tuple):
                result = result[0] if result[0] else result[1]
            return result.strip().replace('#', '').replace(':', '')
        return None
    
    def extract_date(self) -> Optional[str]:
        """Extract invoice date from text."""
        # Try first pattern
        match = re.search(self.DATE_PATTERNS[0], self.text)
        if match:
            day, month, year = match.groups()
            # Normalize year
            if len(year) == 2:
                year_int = int(year)
                year = '20' + year if year_int < 50 else '19' + year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return None
    
    def extract_amount(self) -> Optional[float]:
        """Extract total amount from text."""
        result = self._find_pattern(self.AMOUNT_PATTERNS, self.text)
        if result:
            if isinstance(result, tuple):
                result = result[0]
            # Parse German number format (1.234,56)
            amount_str = result.strip()
            amount_str = amount_str.replace('.', '')  # Remove thousand separator
            amount_str = amount_str.replace(',', '.')  # Convert decimal
            try:
                return float(amount_str)
            except ValueError:
                return None
        return None
    
    def extract_vat_rate(self) -> Optional[str]:
        """Extract VAT rate from text."""
        result = self._find_pattern(self.VAT_PATTERNS, self.text)
        if result:
            if isinstance(result, tuple):
                return result[0]
            return result
        return "19"  # Default to 19%
    
    def extract_vendor(self) -> Optional[str]:
        """Extract vendor name from text."""
        # Look for common vendor indicators in first 20 lines
        for line in self.lines[:20]:
            line_clean = line.strip()
            if any(keyword in line_clean.lower() for keyword in ['gmbh', 'ag', 'ohg', 'kg', 'ug']):
                return line_clean
        return None
    
    def detect_account(self, vendor: str) -> Dict:
        """Detect DATEV accounts based on vendor."""
        vendor_lower = vendor.lower() if vendor else ''
        
        for key, account in self.DEFAULT_ACCOUNTS.items():
            if key in vendor_lower:
                return account
        
        # Default accounts
        return {'konto': '6300', 'gegenkonto': '1200', 'steuer': '19'}
    
    def parse(self) -> Dict:
        """Parse all invoice data."""
        vendor = self.extract_vendor()
        account = self.detect_account(vendor) if vendor else {'konto': '6300', 'gegenkonto': '1200', 'steuer': '19'}
        
        return {
            'rechnungsnummer': self.extract_invoice_number(),
            'datum': self.extract_date(),
            'betrag_brutto': self.extract_amount(),
            'mwst_satz': self.extract_vat_rate(),
            'lieferant': vendor,
            'konto': account['konto'],
            'gegenkonto': account['gegenkonto'],
            'raw_text': self.text[:500] + '...' if len(self.text) > 500 else self.text
        }


class DATEVExporter:
    """Export invoice data to DATEV-compatible CSV."""
    
    # DATEV CSV format (Buchungsstapel)
    DATEV_HEADER = [
        'Umsatz (ohne Soll/Haben-Kz)',
        'Soll/Haben-Kennzeichen',
        'WKZ Umsatz',
        'Kurs',
        'Basis-Umsatz',
        'WKZ Basis-Umsatz',
        'Konto',
        'Gegenkonto (ohne BU-Schlüssel)',
        'BU-Schlüssel',
        'Belegdatum',
        'Belegfeld 1',
        'Belegfeld 2',
        'Skonto',
        'Buchungstext',
    ]
    
    def __init__(self, invoices: List[Dict]):
        self.invoices = invoices
    
    def calculate_net_amount(self, brutto: float, mwst_satz: str) -> Tuple[float, float]:
        """Calculate net amount and VAT from gross."""
        try:
            mwst_rate = float(mwst_satz) / 100
            netto = brutto / (1 + mwst_rate)
            mwst = brutto - netto
            return round(netto, 2), round(mwst, 2)
        except:
            return brutto, 0.0
    
    def to_csv(self, output_path: str) -> bool:
        """Export to DATEV CSV format."""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                
                # Write header
                writer.writerow(self.DATEV_HEADER)
                
                # Write data rows
                for inv in self.invoices:
                    if not inv.get('betrag_brutto'):
                        continue
                    
                    netto, mwst = self.calculate_net_amount(
                        inv['betrag_brutto'],
                        inv.get('mwst_satz', '19')
                    )
                    
                    # Format date for DATEV (DDMM)
                    datum = inv.get('datum', '')
                    if datum:
                        try:
                            dt = datetime.strptime(datum, '%Y-%m-%d')
                            belegdatum = dt.strftime('%d%m')
                        except:
                            belegdatum = ''
                    else:
                        belegdatum = ''
                    
                    row = [
                        str(netto).replace('.', ','),  # Umsatz
                        'S',  # Soll
                        'EUR',  # WKZ
                        '',  # Kurs
                        '',  # Basis-Umsatz
                        '',  # WKZ Basis
                        inv.get('konto', '6300'),  # Konto
                        inv.get('gegenkonto', '1200'),  # Gegenkonto
                        '',  # BU-Schlüssel
                        belegdatum,  # Belegdatum
                        inv.get('rechnungsnummer', '')[:12],  # Belegfeld 1
                        '',  # Belegfeld 2
                        '',  # Skonto
                        inv.get('lieferant', 'Rechnung')[:60],  # Buchungstext
                    ]
                    writer.writerow(row)
            
            return True
        except Exception as e:
            logger.error(f"Error writing CSV: {e}")
            return False
    
    def to_json(self, output_path: str) -> bool:
        """Export to JSON for further processing."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.invoices, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error writing JSON: {e}")
            return False


def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """Extract text from PDF file."""
    try:
        # Try PyPDF2 first
        try:
            import PyPDF2
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() or ''
                return text
        except ImportError:
            logger.warning("PyPDF2 not installed, trying pdfplumber")
        
        # Fallback to pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() or ''
                return text
        except ImportError:
            logger.error("No PDF library available. Install: pip install PyPDF2")
            return None
            
    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
        return None


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='PDF Rechnung zu DATEV CSV')
    parser.add_argument('pdf_files', nargs='+', help='PDF Rechnungsdateien')
    parser.add_argument('--output', '-o', default='rechnungen.csv', help='Output CSV Datei')
    parser.add_argument('--json', '-j', help='Optional JSON Output')
    
    args = parser.parse_args()
    
    print("🚀 PDF Rechnung zu DATEV CSV Konverter\n")
    
    invoices = []
    
    for pdf_file in args.pdf_files:
        print(f"📄 Verarbeite: {pdf_file}")
        
        text = extract_text_from_pdf(pdf_file)
        if not text:
            print(f"   ❌ Konnte PDF nicht lesen")
            continue
        
        parser = PDFInvoiceParser(text)
        data = parser.parse()
        
        print(f"   📋 Rechnung: {data.get('rechnungsnummer', 'N/A')}")
        print(f"   📅 Datum: {data.get('datum', 'N/A')}")
        print(f"   💰 Betrag: {data.get('betrag_brutto', 'N/A')} €")
        print(f"   🏢 Lieferant: {data.get('lieferant', 'N/A')[:40]}")
        print(f"   📊 Konto: {data.get('konto')} / {data.get('gegenkonto')}")
        print()
        
        invoices.append(data)
    
    if invoices:
        exporter = DATEVExporter(invoices)
        
        if exporter.to_csv(args.output):
            print(f"✅ CSV exportiert: {args.output}")
        
        if args.json:
            if exporter.to_json(args.json):
                print(f"✅ JSON exportiert: {args.json}")
    else:
        print("❌ Keine Rechnungen verarbeitet")


if __name__ == "__main__":
    main()
