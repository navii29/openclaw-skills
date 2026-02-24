"""
XRechnung / ZUGFeRD Validator
Validiert deutsche E-Rechnungen nach EN 16931 und XRechnung-Standard

Fokus: German E-Invoicing, B2G, Tax Compliance
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json


@dataclass
class XRechnungValidationResult:
    """Ergebnis einer XRechnung-Validierung"""
    gueltig: bool
    profil: str
    fehler: List[str]
    warnungen: List[str]
    informationen: List[str]
    pflichtfelder_ok: Dict[str, bool]


class XRechnungValidator:
    """
    Validator für XRechnung und ZUGFeRD
    
    Unterstützte Profile:
    - XRechnung 2.3.1 (CII/XML)
    - ZUGFeRD 2.1/2.2 (Factur-X)
    - EN 16931 (Core Invoice)
    """
    
    # Pflichtfelder nach EN 16931 / XRechnung
    PFLICHTFELDER = {
        # Absender (Seller)
        'seller_name': 'Name Verkäufer',
        'seller_address': 'Adresse Verkäufer',
        'seller_vat_id': 'USt-IdNr Verkäufer',
        
        # Empfänger (Buyer)
        'buyer_name': 'Name Käufer',
        'buyer_address': 'Adresse Käufer',
        
        # Rechnung
        'invoice_number': 'Rechnungsnummer',
        'invoice_date': 'Rechnungsdatum',
        'currency': 'Währung',
        
        # Beträge
        'total_net': 'Gesamt-Netto',
        'total_vat': 'Gesamt-USt',
        'total_gross': 'Gesamt-Brutto',
        
        # Steuerinformationen
        'vat_rate': 'USt-Satz',
        'vat_category': 'USt-Kategorie',
    }
    
    # Gültige Währungscodes (ISO 4217)
    GUELTIGE_WAEHRUNGEN = ['EUR', 'USD', 'GBP', 'CHF']
    
    # Gültige USt-Sätze Deutschland
    GUELTIGE_UST_SAETZE = [0, 7, 19]
    
    # Leitweg-ID Format (XRechnung B2G)
    LEITWEGID_PATTERN = r'^[0-9\-]{6,}$'
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
    
    def validate_xrechnung_xml(self, xml_content: str) -> XRechnungValidationResult:
        """
        Validiert XRechnung-XML (CII oder UBL)
        
        Args:
            xml_content: XML-String der Rechnung
        
        Returns:
            XRechnungValidationResult
        """
        self.errors = []
        self.warnings = []
        self.info = []
        
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            return XRechnungValidationResult(
                gueltig=False,
                profil="UNKNOWN",
                fehler=[f"XML Parse-Fehler: {e}"],
                warnungen=[],
                informationen=[],
                pflichtfelder_ok={}
            )
        
        # Erkenne Profil
        profil = self._detect_profile(root)
        self.info.append(f"Erkanntes Profil: {profil}")
        
        # Validiere je nach Profil
        if profil == "XRECHNUNG_CII":
            pflichtfelder = self._validate_cii(root)
        elif profil == "XRECHNUNG_UBL":
            pflichtfelder = self._validate_ubl(root)
        else:
            pflichtfelder = self._validate_generic(root)
        
        # Allgemeine Validierungen
        self._validate_business_rules(xml_content)
        
        return XRechnungValidationResult(
            gueltig=len(self.errors) == 0,
            profil=profil,
            fehler=self.errors,
            warnungen=self.warnings,
            informationen=self.info,
            pflichtfelder_ok=pflichtfelder
        )
    
    def validate_zugferd(self, pdf_path: str) -> XRechnungValidationResult:
        """
        Validiert ZUGFeRD/Factur-X PDF
        
        Hinweis: Extrahiert eingebettetes XML aus PDF/A-3
        """
        self.errors = []
        self.warnings = []
        self.info = []
        
        # Hinweis: Echte PDF/A-Extraktion benötigt PyPDF2 oder pdfminer
        # Dies ist eine vereinfachte Implementierung
        
        self.info.append("ZUGFeRD-Validierung: Extraktion des eingebetteten XML erforderlich")
        
        return XRechnungValidationResult(
            gueltig=None,
            profil="ZUGFERD",
            fehler=["PDF-Extraktion nicht implementiert"],
            warnungen=["Verwenden Sie validate_xrechnung_xml() mit extrahiertem XML"],
            informationen=self.info,
            pflichtfelder_ok={}
        )
    
    def validate_leitweg_id(self, leitweg_id: str) -> Dict:
        """
        Validiert Leitweg-ID (für XRechnung an Behörden)
        
        Args:
            leitweg_id: Die zu prüfende Leitweg-ID
        
        Returns:
            Dict mit Validierungsergebnis
        """
        if not leitweg_id:
            return {
                'gueltig': False,
                'fehler': ['Leitweg-ID ist leer'],
                'format': None
            }
        
        # Format-Prüfung
        if re.match(self.LEITWEGID_PATTERN, leitweg_id):
            return {
                'gueltig': True,
                'format': 'korrekt',
                'laenge': len(leitweg_id),
                'hinweis': 'Format gültig (Prüfziffer-Validierung nicht möglich)'
            }
        else:
            return {
                'gueltig': False,
                'fehler': ['Ungültiges Format (nur Zahlen und Bindestriche erlaubt)'],
                'format': 'ungültig'
            }
    
    def _detect_profile(self, root: ET.Element) -> str:
        """Erkennt das Rechnungsprofil aus XML"""
        # CII Erkennung
        if 'CrossIndustryInvoice' in root.tag or 'rsm:CrossIndustryInvoice' in root.tag:
            return "XRECHNUNG_CII"
        
        # UBL Erkennung
        if 'Invoice' in root.tag and 'urn:oasis:names:specification:ubl' in str(root.attrib.values()):
            return "XRECHNUNG_UBL"
        
        # ZUGFeRD/Factur-X
        if 'FACTUR' in root.tag.upper() or 'ZUGFERD' in root.tag.upper():
            return "ZUGFERD"
        
        return "UNKNOWN"
    
    def _validate_cii(self, root: ET.Element) -> Dict[str, bool]:
        """Validiert CII (Cross Industry Invoice) Format"""
        pflichtfelder = {}
        
        # Namespace-Mapping
        ns = {
            'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
            'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
            'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100'
        }
        
        # Seller Trade Party
        seller = root.find('.//ram:SellerTradeParty', ns)
        pflichtfelder['seller_name'] = seller is not None and seller.find('.//ram:Name', ns) is not None
        
        # Buyer Trade Party
        buyer = root.find('.//ram:BuyerTradeParty', ns)
        pflichtfelder['buyer_name'] = buyer is not None and buyer.find('.//ram:Name', ns) is not None
        
        # Rechnungsnummer
        invoice_id = root.find('.//ram:ID', ns)
        pflichtfelder['invoice_number'] = invoice_id is not None and invoice_id.text is not None
        
        # Beträge
        grand_total = root.find('.//ram:GrandTotalAmount', ns)
        pflichtfelder['total_gross'] = grand_total is not None
        
        # Fehler sammeln
        for feld, ok in pflichtfelder.items():
            if not ok:
                self.errors.append(f"Pflichtfeld fehlt: {self.PFLICHTFELDER.get(feld, feld)}")
        
        return pflichtfelder
    
    def _validate_ubl(self, root: ET.Element) -> Dict[str, bool]:
        """Validiert UBL (Universal Business Language) Format"""
        pflichtfelder = {}
        
        ns = {
            'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        }
        
        # AccountingSupplierParty
        supplier = root.find('.//cac:AccountingSupplierParty', ns)
        pflichtfelder['seller_name'] = supplier is not None
        
        # AccountingCustomerParty
        customer = root.find('.//cac:AccountingCustomerParty', ns)
        pflichtfelder['buyer_name'] = customer is not None
        
        # Rechnungsnummer
        invoice_id = root.find('.//cbc:ID', ns)
        pflichtfelder['invoice_number'] = invoice_id is not None and invoice_id.text is not None
        
        # Fehler sammeln
        for feld, ok in pflichtfelder.items():
            if not ok:
                self.errors.append(f"Pflichtfeld fehlt: {self.PFLICHTFELDER.get(feld, feld)}")
        
        return pflichtfelder
    
    def _validate_generic(self, root: ET.Element) -> Dict[str, bool]:
        """Generische Validierung wenn Profil unbekannt"""
        self.warnings.append("Unbekanntes Profil - generische Validierung")
        return {}
    
    def _validate_business_rules(self, xml_content: str):
        """Validiert Geschäftsregeln"""
        # Rechnungsnummer-Format
        if 'RE-' in xml_content or 'INV' in xml_content:
            self.info.append("Rechnungsnummer mit Präfix erkannt")
        
        # Währung prüfen
        if 'EUR' in xml_content:
            self.info.append("Währung: EUR")
        
        # Hinweis auf Elektronische Rechnung
        if 'XRechnung' in xml_content or 'xrechnung' in xml_content.lower():
            self.info.append("XRechnung-Kennzeichnung erkannt")


def validate_xrechnung(xml_content: str) -> Dict:
    """
    Schnell-Validierung einer XRechnung
    
    Usage:
        result = validate_xrechnung(xml_string)
        print(result['gueltig'])
        print(result['fehler'])
    """
    validator = XRechnungValidator()
    result = validator.validate_xrechnung_xml(xml_content)
    
    return {
        'gueltig': result.gueltig,
        'profil': result.profil,
        'fehler': result.fehler,
        'warnungen': result.warnungen,
        'informationen': result.informationen,
        'pflichtfelder': result.pflichtfelder_ok
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python xrechnung_validator.py <command> [args]")
        print("\nCommands:")
        print("  validate-xml <file.xml>  - XML-Datei validieren")
        print("  validate-leitweg <id>    - Leitweg-ID validieren")
        print("  sample                  - Beispiel-XML anzeigen")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "validate-xml":
        if len(sys.argv) < 3:
            print("❌ Fehler: XML-Datei angeben")
            sys.exit(1)
        
        filepath = sys.argv[2]
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            result = validate_xrechnung(xml_content)
            
            print(f"🔍 XRechnung-Validierung")
            print("-" * 50)
            print(f"Profil: {result['profil']}")
            print(f"Gültig: {'✅ Ja' if result['gueltig'] else '❌ Nein'}")
            
            if result['fehler']:
                print(f"\n❌ Fehler ({len(result['fehler'])}):")
                for fehler in result['fehler']:
                    print(f"   - {fehler}")
            
            if result['warnungen']:
                print(f"\n⚠️  Warnungen ({len(result['warnungen'])}):")
                for warn in result['warnungen']:
                    print(f"   - {warn}")
            
            if result['informationen']:
                print(f"\nℹ️  Informationen:")
                for info in result['informationen']:
                    print(f"   - {info}")
                    
        except FileNotFoundError:
            print(f"❌ Datei nicht gefunden: {filepath}")
    
    elif command == "validate-leitweg":
        if len(sys.argv) < 3:
            print("❌ Fehler: Leitweg-ID angeben")
            sys.exit(1)
        
        leitweg_id = sys.argv[2]
        validator = XRechnungValidator()
        result = validator.validate_leitweg_id(leitweg_id)
        
        print(f"🔍 Leitweg-ID: {leitweg_id}")
        print("-" * 50)
        print(f"Gültig: {'✅ Ja' if result['gueltig'] else '❌ Nein'}")
        
        if result.get('fehler'):
            for fehler in result['fehler']:
                print(f"   - {fehler}")
    
    elif command == "sample":
        sample = """<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100">
  <rsm:ExchangedDocument>
    <ram:ID>RE-2025-00001</ram:ID>
    <ram:TypeCode>380</ram:TypeCode>
    <ram:IssueDateTime>
      <udt:DateTimeString format="102">20250224</udt:DateTimeString>
    </ram:IssueDateTime>
  </rsm:ExchangedDocument>
</rsm:CrossIndustryInvoice>"""
        print("Beispiel XRechnung (CII):")
        print(sample)
    
    else:
        print(f"❌ Unbekannter Befehl: {command}")
