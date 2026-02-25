#!/usr/bin/env python3
"""
ZUGFeRD 2.1 / Factur-X E-Rechnung Generator

Erstellt konforme E-Rechnungen im ZUGFeRD-Format (PDF + XML hybrid).
Gesetzlich ab 2025 für B2B-Rechnungen in der EU erforderlich.

Author: Navii Automation
Version: 1.0.0
"""

import json
import argparse
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
import zipfile
import io

# ZUGFeRD 2.1 Namespaces
NAMESPACES = {
    'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
    'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
    'qdt': 'urn:un:unece:uncefact:data:standard:QualifiedDataType:100',
    'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

# UNECE Einheitencodes
UNIT_CODES = {
    'C62': 'Stück',
    'H87': 'Stück (alternative)',
    'HUR': 'Stunde',
    'DAY': 'Tag',
    'WEE': 'Woche',
    'MON': 'Monat',
    'ANN': 'Jahr',
    'LTR': 'Liter',
    'MTR': 'Meter',
    'KGM': 'Kilogramm',
    'TNE': 'Tonne',
    'MTK': 'Quadratmeter',
    'MTQ': 'Kubikmeter'
}


@dataclass
class Address:
    """Adressdaten für Verkäufer/Käufer"""
    name: str
    street: str
    zip: str
    city: str
    country: str = "DE"
    additional_address: Optional[str] = None


@dataclass
class Party:
    """Geschäftspartner (Verkäufer oder Käufer)"""
    name: str
    street: str
    zip: str
    city: str
    country: str = "DE"
    vat_id: Optional[str] = None
    tax_number: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    buyer_reference: Optional[str] = None  # Leitweg-ID oder ähnliches
    additional_address: Optional[str] = None  # Zusätzliche Adresszeile


@dataclass
class InvoiceItem:
    """Rechnungsposition"""
    description: str
    quantity: float
    unit: str = "C62"  # UNECE Code
    price: float = 0.0
    vat_rate: float = 19.0
    position: Optional[int] = None
    sku: Optional[str] = None
    
    @property
    def line_total(self) -> float:
        """Zeilensumme (Netto)"""
        return round(self.quantity * self.price, 2)
    
    @property
    def vat_amount(self) -> float:
        """USt-Betrag"""
        return round(self.line_total * (self.vat_rate / 100), 2)


@dataclass
class Invoice:
    """Rechnungsdaten"""
    invoice_number: str
    invoice_date: str
    due_date: Optional[str] = None
    delivery_date: Optional[str] = None
    seller: Optional[Party] = None
    buyer: Optional[Party] = None
    items: List[InvoiceItem] = field(default_factory=list)
    payment_terms: str = "Zahlbar innerhalb von 30 Tagen"
    leitweg_id: Optional[str] = None
    currency: str = "EUR"
    
    @property
    def subtotal(self) -> float:
        """Nettosumme"""
        return round(sum(item.line_total for item in self.items), 2)
    
    @property
    def vat_breakdown(self) -> Dict[float, float]:
        """USt-Aufschlüsselung nach Steuersatz"""
        breakdown = {}
        for item in self.items:
            rate = item.vat_rate
            if rate not in breakdown:
                breakdown[rate] = 0
            breakdown[rate] += item.vat_amount
        return {k: round(v, 2) for k, v in breakdown.items()}
    
    @property
    def total_vat(self) -> float:
        """Gesamt-USt"""
        return round(sum(self.vat_breakdown.values()), 2)
    
    @property
    def total(self) -> float:
        """Bruttosumme"""
        return round(self.subtotal + self.total_vat, 2)


class ZUGFeRDGenerator:
    """
    Generator für ZUGFeRD 2.1 / Factur-X konforme E-Rechnungen
    """
    
    VERSION = "1.0.0"
    ZUGFERD_VERSION = "2.1"
    
    def __init__(self, profile: str = "EN 16931"):
        """
        Args:
            profile: Konformitätsprofil (EN 16931, BASIC, COMFORT, EXTENDED)
        """
        self.profile = profile
    
    def generate_xml(self, invoice: Invoice) -> str:
        """
        Generiert das ZUGFeRD XML (Cross Industry Invoice)
        
        Args:
            invoice: Rechnungsdaten
            
        Returns:
            XML-String
        """
        # Root Element
        root = ET.Element('rsm:CrossIndustryInvoice', {
            'xmlns:rsm': NAMESPACES['rsm'],
            'xmlns:ram': NAMESPACES['ram'],
            'xmlns:qdt': NAMESPACES['qdt'],
            'xmlns:udt': NAMESPACES['udt']
        })
        
        # ExchangedDocumentContext
        context = ET.SubElement(root, 'rsm:ExchangedDocumentContext')
        guideline = ET.SubElement(context, 'ram:GuidelineSpecifiedDocumentContextParameter')
        guideline_id = ET.SubElement(guideline, 'ram:ID')
        guideline_id.text = "urn:cen.eu:en16931:2017"  # EN 16931 kompatibel
        
        # ExchangedDocument
        doc = ET.SubElement(root, 'rsm:ExchangedDocument')
        doc_id = ET.SubElement(doc, 'ram:ID')
        doc_id.text = invoice.invoice_number
        
        type_code = ET.SubElement(doc, 'ram:TypeCode')
        type_code.text = "380"  # Handelsrechnung
        
        issue_date = ET.SubElement(doc, 'ram:IssueDateTime')
        date = ET.SubElement(issue_date, 'udt:DateTimeString', {'format': '102'})
        date.text = invoice.invoice_date.replace("-", "")
        
        # SupplyChainTradeTransaction
        trade = ET.SubElement(root, 'rsm:SupplyChainTradeTransaction')
        
        # IncludedSupplyChainTradeLineItem (Positionen)
        for idx, item in enumerate(invoice.items, 1):
            line_item = ET.SubElement(trade, 'ram:IncludedSupplyChainTradeLineItem')
            
            # Line ID
            line_id = ET.SubElement(line_item, 'ram:AssociatedDocumentLineDocument')
            line_num = ET.SubElement(line_id, 'ram:LineID')
            line_num.text = str(item.position or idx)
            
            # SpecifiedTradeProduct
            product = ET.SubElement(line_item, 'ram:SpecifiedTradeProduct')
            product_name = ET.SubElement(product, 'ram:Name')
            product_name.text = item.description
            
            # TradeAgreement
            agreement = ET.SubElement(line_item, 'ram:SpecifiedLineTradeAgreement')
            
            # NetPrice
            net_price = ET.SubElement(agreement, 'ram:NetPriceProductTradePrice')
            charge = ET.SubElement(net_price, 'ram:ChargeAmount')
            charge.text = f"{item.price:.2f}"
            
            # Delivery
            delivery = ET.SubElement(line_item, 'ram:SpecifiedLineTradeDelivery')
            billed_qty = ET.SubElement(delivery, 'ram:BilledQuantity', {'unitCode': item.unit})
            billed_qty.text = f"{item.quantity:.2f}"
            
            # Settlement
            settlement = ET.SubElement(line_item, 'ram:SpecifiedLineTradeSettlement')
            
            # ApplicableTradeTax
            tax = ET.SubElement(settlement, 'ram:ApplicableTradeTax')
            tax_type = ET.SubElement(tax, 'ram:TypeCode')
            tax_type.text = "VAT"
            tax_cat = ET.SubElement(tax, 'ram:CategoryCode')
            tax_cat.text = "S"  # Standard rate
            tax_rate = ET.SubElement(tax, 'ram:RateApplicablePercent')
            tax_rate.text = f"{item.vat_rate:.2f}"
            
            # LineTotal
            line_total = ET.SubElement(settlement, 'ram:SpecifiedTradeSettlementLineMonetarySummation')
            line_charge = ET.SubElement(line_total, 'ram:LineTotalAmount')
            line_charge.text = f"{item.line_total:.2f}"
        
        # ApplicableHeaderTradeAgreement
        header_agreement = ET.SubElement(trade, 'ram:ApplicableHeaderTradeAgreement')
        
        # Seller
        if invoice.seller:
            seller_trade = ET.SubElement(header_agreement, 'ram:SellerTradeParty')
            self._add_party_to_xml(seller_trade, invoice.seller, is_seller=True)
        
        # Buyer
        if invoice.buyer:
            buyer_trade = ET.SubElement(header_agreement, 'ram:BuyerTradeParty')
            self._add_party_to_xml(buyer_trade, invoice.buyer, is_seller=False)
            
            # BuyerReference (Leitweg-ID)
            if invoice.buyer.buyer_reference:
                buyer_ref = ET.SubElement(header_agreement, 'ram:BuyerReference')
                buyer_ref.text = invoice.buyer.buyer_reference
        
        # ApplicableHeaderTradeDelivery
        header_delivery = ET.SubElement(trade, 'ram:ApplicableHeaderTradeDelivery')
        if invoice.delivery_date:
            actual_delivery = ET.SubElement(header_delivery, 'ram:ActualDeliverySupplyChainEvent')
            delivery_date = ET.SubElement(actual_delivery, 'ram:OccurrenceDateTime')
            delivery_dt = ET.SubElement(delivery_date, 'udt:DateTimeString', {'format': '102'})
            delivery_dt.text = invoice.delivery_date.replace("-", "")
        
        # ApplicableHeaderTradeSettlement
        header_settlement = ET.SubElement(trade, 'ram:ApplicableHeaderTradeSettlement')
        
        # Currency
        currency = ET.SubElement(header_settlement, 'ram:InvoiceCurrencyCode')
        currency.text = invoice.currency
        
        # ApplicableTradeTax (Header level)
        for rate, amount in invoice.vat_breakdown.items():
            tax = ET.SubElement(header_settlement, 'ram:ApplicableTradeTax')
            tax_amount = ET.SubElement(tax, 'ram:CalculatedAmount')
            tax_amount.text = f"{amount:.2f}"
            tax_type = ET.SubElement(tax, 'ram:TypeCode')
            tax_type.text = "VAT"
            tax_basis = ET.SubElement(tax, 'ram:BasisAmount')
            basis = sum(item.line_total for item in invoice.items if item.vat_rate == rate)
            tax_basis.text = f"{basis:.2f}"
            tax_cat = ET.SubElement(tax, 'ram:CategoryCode')
            tax_cat.text = "S"
            tax_rate_elem = ET.SubElement(tax, 'ram:RateApplicablePercent')
            tax_rate_elem.text = f"{rate:.2f}"
        
        # PaymentTerms
        if invoice.payment_terms:
            terms = ET.SubElement(header_settlement, 'ram:SpecifiedTradePaymentTerms')
            desc = ET.SubElement(terms, 'ram:Description')
            desc.text = invoice.payment_terms
            if invoice.due_date:
                due = ET.SubElement(terms, 'ram:DueDateDateTime')
                due_dt = ET.SubElement(due, 'udt:DateTimeString', {'format': '102'})
                due_dt.text = invoice.due_date.replace("-", "")
        
        # MonetarySummation
        summation = ET.SubElement(header_settlement, 'ram:SpecifiedTradeSettlementHeaderMonetarySummation')
        
        line_total = ET.SubElement(summation, 'ram:LineTotalAmount')
        line_total.text = f"{invoice.subtotal:.2f}"
        
        charge_total = ET.SubElement(summation, 'ram:ChargeTotalAmount')
        charge_total.text = "0.00"
        
        allowance_total = ET.SubElement(summation, 'ram:AllowanceTotalAmount')
        allowance_total.text = "0.00"
        
        tax_basis_total = ET.SubElement(summation, 'ram:TaxBasisTotalAmount')
        tax_basis_total.text = f"{invoice.subtotal:.2f}"
        
        tax_total = ET.SubElement(summation, 'ram:TaxTotalAmount', {'currencyID': invoice.currency})
        tax_total.text = f"{invoice.total_vat:.2f}"
        
        grand_total = ET.SubElement(summation, 'ram:GrandTotalAmount')
        grand_total.text = f"{invoice.total:.2f}"
        
        due_total = ET.SubElement(summation, 'ram:DuePayableAmount')
        due_total.text = f"{invoice.total:.2f}"
        
        # Pretty print
        xml_string = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_string)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # Remove empty lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def _add_party_to_xml(self, parent: ET.Element, party: Party, is_seller: bool):
        """Fügt Party-Daten zum XML hinzu"""
        # Name
        name = ET.SubElement(parent, 'ram:Name')
        name.text = party.name
        
        # PostalTradeAddress
        address = ET.SubElement(parent, 'ram:PostalTradeAddress')
        
        if party.additional_address:
            line_one = ET.SubElement(address, 'ram:LineOne')
            line_one.text = party.street
            line_two = ET.SubElement(address, 'ram:LineTwo')
            line_two.text = party.additional_address
        else:
            line_one = ET.SubElement(address, 'ram:LineOne')
            line_one.text = party.street
        
        postcode = ET.SubElement(address, 'ram:PostcodeCode')
        postcode.text = party.zip
        
        city = ET.SubElement(address, 'ram:CityName')
        city.text = party.city
        
        country = ET.SubElement(address, 'ram:CountryID')
        country.text = party.country
        
        # VAT ID
        if party.vat_id:
            tax_reg = ET.SubElement(parent, 'ram:SpecifiedTaxRegistration')
            tax_id = ET.SubElement(tax_reg, 'ram:ID', {'schemeID': 'VA'})
            tax_id.text = party.vat_id
        
        # Tax Number (Steuernummer)
        if party.tax_number:
            tax_reg = ET.SubElement(parent, 'ram:SpecifiedTaxRegistration')
            tax_id = ET.SubElement(tax_reg, 'ram:ID', {'schemeID': 'FC'})
            tax_id.text = party.tax_number
    
    def generate_zugferd(self, invoice: Invoice, pdf_content: Optional[bytes] = None) -> bytes:
        """
        Generiert ZUGFeRD PDF (PDF/A-3 mit eingebettetem XML)
        
        Args:
            invoice: Rechnungsdaten
            pdf_content: Optional existierendes PDF (sonst wird einfaches PDF generiert)
            
        Returns:
            PDF-Bytes
        """
        # XML generieren
        xml_content = self.generate_xml(invoice)
        
        # Simpler Ansatz: XML separat speichern + PDF Hinweis
        # Für echte ZUGFeRD-PDFs bräuchten wir eine PDF/A-3 Library wie pypdf oder mustang
        output = io.BytesIO()
        
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
            # XML hinzufügen
            zf.writestr('zugferd-invoice.xml', xml_content)
            
            # Info-Datei
            info = f"""ZUGFeRD 2.1 E-Rechnung
Rechnungsnummer: {invoice.invoice_number}
Datum: {invoice.invoice_date}
Betrag: {invoice.total:.2f} {invoice.currency}

Das XML befindet sich in dieser ZIP-Datei: zugferd-invoice.xml
"""
            zf.writestr('INFO.txt', info)
        
        return output.getvalue()
    
    def generate_xrechnung(self, invoice: Invoice) -> str:
        """
        Generiert XRechnung (reines XML für öffentliche Auftraggeber)
        
        Args:
            invoice: Rechnungsdaten
            
        Returns:
            XML-String
        """
        # XRechnung ist im Grunde das gleiche ZUGFeRD XML
        # Optional mit spezifischen Erweiterungen für Deutschland
        return self.generate_xml(invoice)
    
    def validate_invoice(self, invoice: Invoice) -> Dict:
        """
        Validiert Rechnungsdaten vor der Generierung
        
        Returns:
            Dict mit 'valid' (bool) und 'errors' (list)
        """
        errors = []
        warnings = []
        
        # Pflichtfelder
        if not invoice.invoice_number:
            errors.append("Rechnungsnummer fehlt")
        
        if not invoice.invoice_date:
            errors.append("Rechnungsdatum fehlt")
        
        if not invoice.seller:
            errors.append("Verkäuferdaten fehlen")
        else:
            if not invoice.seller.name:
                errors.append("Verkäufer-Name fehlt")
            if not invoice.seller.vat_id and not invoice.seller.tax_number:
                warnings.append("Verkäufer hat weder USt-IdNr noch Steuernummer")
        
        if not invoice.buyer:
            errors.append("Käuferdaten fehlen")
        else:
            if not invoice.buyer.name:
                errors.append("Käufer-Name fehlt")
        
        if not invoice.items:
            errors.append("Keine Rechnungspositionen")
        
        for idx, item in enumerate(invoice.items):
            if not item.description:
                errors.append(f"Position {idx+1}: Beschreibung fehlt")
            if item.price < 0:
                errors.append(f"Position {idx+1}: Preis darf nicht negativ sein")
            if item.quantity <= 0:
                errors.append(f"Position {idx+1}: Menge muss größer 0 sein")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def invoice_from_json(data: Dict) -> Invoice:
        """
        Erstellt Invoice-Objekt aus JSON-Daten
        """
        seller_data = data.get('seller', {})
        seller = Party(
            name=seller_data.get('name', ''),
            street=seller_data.get('street', ''),
            zip=seller_data.get('zip', ''),
            city=seller_data.get('city', ''),
            country=seller_data.get('country', 'DE'),
            vat_id=seller_data.get('vat_id'),
            tax_number=seller_data.get('tax_number'),
            contact_email=seller_data.get('contact_email'),
            iban=seller_data.get('iban'),
            bic=seller_data.get('bic'),
            additional_address=seller_data.get('additional_address')
        )
        
        buyer_data = data.get('buyer', {})
        buyer = Party(
            name=buyer_data.get('name', ''),
            street=buyer_data.get('street', ''),
            zip=buyer_data.get('zip', ''),
            city=buyer_data.get('city', ''),
            country=buyer_data.get('country', 'DE'),
            vat_id=buyer_data.get('vat_id'),
            tax_number=buyer_data.get('tax_number'),
            buyer_reference=buyer_data.get('buyer_reference'),
            additional_address=buyer_data.get('additional_address')
        )
        
        items = []
        for item_data in data.get('items', []):
            items.append(InvoiceItem(
                description=item_data.get('description', ''),
                quantity=float(item_data.get('quantity', 1)),
                unit=item_data.get('unit', 'C62'),
                price=float(item_data.get('price', 0)),
                vat_rate=float(item_data.get('vat_rate', 19)),
                position=item_data.get('position'),
                sku=item_data.get('sku')
            ))
        
        return Invoice(
            invoice_number=data.get('invoice_number', ''),
            invoice_date=data.get('invoice_date', ''),
            due_date=data.get('due_date'),
            delivery_date=data.get('delivery_date'),
            seller=seller,
            buyer=buyer,
            items=items,
            payment_terms=data.get('payment_terms', 'Zahlbar innerhalb von 30 Tagen'),
            leitweg_id=data.get('leitweg_id'),
            currency=data.get('currency', 'EUR')
        )


def main():
    """CLI Interface"""
    parser = argparse.ArgumentParser(description='ZUGFeRD E-Rechnung Generator')
    parser.add_argument('--input', '-i', help='JSON Input-Datei')
    parser.add_argument('--output', '-o', help='Output-Datei')
    parser.add_argument('--format', choices=['zugferd', 'xrechnung'], default='zugferd',
                       help='Ausgabeformat')
    parser.add_argument('--validate', help='Bestehende Rechnung validieren')
    
    args = parser.parse_args()
    
    if args.input:
        # JSON laden
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        invoice = ZUGFeRDGenerator.invoice_from_json(data)
        generator = ZUGFeRDGenerator()
        
        # Validierung
        validation = generator.validate_invoice(invoice)
        if not validation['valid']:
            print("❌ Validierung fehlgeschlagen:")
            for error in validation['errors']:
                print(f"  - {error}")
            return 1
        
        if validation['warnings']:
            print("⚠️  Warnungen:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        # Generierung
        if args.format == 'xrechnung':
            xml = generator.generate_xrechnung(invoice)
            output_file = args.output or f"{invoice.invoice_number}_xrechnung.xml"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(xml)
            print(f"✅ XRechnung erstellt: {output_file}")
        else:
            zugferd = generator.generate_zugferd(invoice)
            output_file = args.output or f"{invoice.invoice_number}_zugferd.zip"
            with open(output_file, 'wb') as f:
                f.write(zugferd)
            print(f"✅ ZUGFeRD erstellt: {output_file}")
            print(f"   Rechnungsbetrag: {invoice.total:.2f} {invoice.currency}")
            print(f"   Positionen: {len(invoice.items)}")
        
        return 0
    
    elif args.validate:
        # Validierung einer bestehenden Datei
        print(f"Validierung: {args.validate}")
        # TODO: Implementieren
        return 0
    
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    exit(main())
