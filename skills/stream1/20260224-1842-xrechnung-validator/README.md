# 📄 XRechnung / ZUGFeRD Validator

Validiert deutsche E-Rechnungen nach EN 16931 und XRechnung-Standard für B2G (Business-to-Government) und B2B.

## 🎯 Use Cases

- **Behördenrechnungen**: XRechnung für öffentliche Auftraggeber
- **E-Invoicing**: Automatische Validierung eingehender Rechnungen
- **Compliance**: Prüfung auf GoBD und EN 16931 Konformität
- **ZUGFeRD**: Validierung hybrider PDF/XML-Rechnungen

## 📋 Unterstützte Formate

| Format | Version | Verwendung |
|--------|---------|------------|
| **XRechnung** | 2.3.1 | B2G Deutschland |
| **ZUGFeRD** | 2.1 / 2.2 | B2B Deutschland |
| **EN 16931** | - | EU-Standard |
| **Factur-X** | 1.0 | Frankreich (kompatibel) |

## 📦 Installation

```bash
# Keine externen Dependencies
python3 xrechnung_validator.py validate-xml rechnung.xml
```

## 🚀 Quick Start

### Als Python-Modul

```python
from xrechnung_validator import validate_xrechnung, XRechnungValidator

# XML validieren
with open('rechnung.xml', 'r') as f:
    xml_content = f.read()

result = validate_xrechnung(xml_content)

if result['gueltig']:
    print("✅ Rechnung ist gültig")
else:
    print("❌ Fehler:", result['fehler'])

# Leitweg-ID validieren (für Behörden)
validator = XRechnungValidator()
leitweg_result = validator.validate_leitweg_id("991-12345-67")
```

### CLI Usage

```bash
# XRechnung XML validieren
python xrechnung_validator.py validate-xml rechnung.xml

# Leitweg-ID prüfen
python xrechnung_validator.py validate-leitweg 991-12345-67

# Beispiel-XML anzeigen
python xrechnung_validator.py sample
```

## 📊 Pflichtfelder (EN 16931)

| Feld | Beschreibung | CII | UBL |
|------|-------------|-----|-----|
| `seller_name` | Name Verkäufer | ✅ | ✅ |
| `seller_address` | Adresse Verkäufer | ✅ | ✅ |
| `seller_vat_id` | USt-IdNr Verkäufer | ✅ | ✅ |
| `buyer_name` | Name Käufer | ✅ | ✅ |
| `buyer_address` | Adresse Käufer | ✅ | ✅ |
| `invoice_number` | Rechnungsnummer | ✅ | ✅ |
| `invoice_date` | Rechnungsdatum | ✅ | ✅ |
| `currency` | Währung | ✅ | ✅ |
| `total_net` | Gesamt-Netto | ✅ | ✅ |
| `total_vat` | Gesamt-USt | ✅ | ✅ |
| `total_gross` | Gesamt-Brutto | ✅ | ✅ |
| `vat_rate` | USt-Satz | ✅ | ✅ |
| `vat_category` | USt-Kategorie | ✅ | ✅ |

## 🔢 Leitweg-ID Format

Die Leitweg-ID ist für Rechnungen an deutsche Behörden **pflichtig**:

```
Format: [0-9\-]{6,}

Beispiele:
  - 991-12345-67
  - 20-123456-001
  - 991112233445
```

## 📊 Rückgabewerte

```python
{
    'gueltig': True,              # Gesamt-Validierung
    'profil': 'XRECHNUNG_CII',   # Erkanntes Profil
    'fehler': [],                 # Kritische Fehler
    'warnungen': [],              # Warnungen
    'informationen': [],          # Zusatzinfos
    'pflichtfelder': {            # Einzelprüfung
        'seller_name': True,
        'invoice_number': True,
        ...
    }
}
```

## ⚡ Automation-Ready

### E-Rechnung Workflow

```python
def process_e_invoice(xml_content, pdf_attachment=None):
    validator = XRechnungValidator()
    
    # XML validieren
    result = validator.validate_xrechnung_xml(xml_content)
    
    if not result.gueltig:
        # Fehler-Log
        log_error(result.fehler)
        return {'status': 'REJECTED', 'errors': result.fehler}
    
    # Leitweg-ID prüfen (bei B2G)
    if is_government_invoice(xml_content):
        leitweg = extract_leitweg_id(xml_content)
        lw_result = validator.validate_leitweg_id(leitweg)
        
        if not lw_result['gueltig']:
            return {'status': 'REJECTED', 'reason': 'Invalid Leitweg-ID'}
    
    return {'status': 'ACCEPTED', 'profile': result.profil}
```

### ZUGFeRD PDF-Verarbeitung

```python
# Hinweis: Für PDF-Extraktion PyPDF2 oder pdfminer erforderlich
from PyPDF2 import PdfReader

def extract_zugferd_xml(pdf_path):
    reader = PdfReader(pdf_path)
    # Extrahiere eingebettetes XML aus PDF/A-3
    # ...
    return xml_content
```

## 📝 XRechnung Beispiel (CII)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice
    xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
    xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
    xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
    
    <rsm:ExchangedDocumentContext>
        <ram:GuidelineSpecifiedDocumentContextParameter>
            <ram:ID>urn:cen.eu:en16931:2017</ram:ID>
        </ram:GuidelineSpecifiedDocumentContextParameter>
    </rsm:ExchangedDocumentContext>
    
    <rsm:ExchangedDocument>
        <ram:ID>RE-2025-00001</ram:ID>
        <ram:TypeCode>380</ram:TypeCode>
        <ram:IssueDateTime>
            <udt:DateTimeString format="102">20250224</udt:DateTimeString>
        </ram:IssueDateTime>
    </rsm:ExchangedDocument>
    
    <rsm:SupplyChainTradeTransaction>
        <ram:ApplicableHeaderTradeAgreement>
            <ram:SellerTradeParty>
                <ram:Name>Muster GmbH</ram:Name>
            </ram:SellerTradeParty>
            <ram:BuyerTradeParty>
                <ram:Name>Kunde AG</ram:Name>
            </ram:BuyerTradeParty>
        </ram:ApplicableHeaderTradeAgreement>
    </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>
```

## 🔗 Weiterführende Links

- [XRechnung Standard](https://www.xrechnung.de/)
- [ZUGFeRD / Factur-X](https://www.ferd-net.de/)
- [EN 16931](https://www.unece.org/trade/uncefact/introducing-uncefact/standards/uncefact-standard)
- [Leitweg-ID](https://leitweg-id.de/)
- [KoSIT Validator](https://it-plattform-kosit.de/xrechnung)

## ⚠️ Wichtige Hinweise

- **Leitweg-ID**: Bei Rechnungen an Behörden zwingend erforderlich
- **Format**: XRechnung CII oder UBL (nicht beides gemischt)
- **ZUGFeRD**: PDF/A-3 mit eingebettetem XML
- **Validierung**: Dies ist eine Basis-Validierung - für vollständige Prüfung KoSIT-Validator nutzen
- **B2G ab 2020**: Elektronische Rechnungen an Bund zwingend
