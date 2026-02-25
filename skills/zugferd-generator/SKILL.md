# ZUGFeRD E-Rechnung Generator

**Version:** 1.0.0 | **Preis:** 149 EUR/Monat | **Support:** DE/EN

Vollständiger ZUGFeRD 2.1 / Factur-X Generator für die elektronische Rechnungsstellung (gesetzlich ab 2025 Pflicht für B2B).

## Warum ZUGFeRD?

| Format | Beschreibung | Verwendung |
|--------|-------------|------------|
| **ZUGFeRD** | PDF + XML hybrid | Universal (Deutschland) |
| **XRechnung** | Reines XML | Öffentliche Auftraggeber |
| **Factur-X** | Französischer Standard | Frankreich, kompatibel mit ZUGFeRD |

**Ab 2025:** Alle B2B-Rechnungen in der EU müssen elektronisch sein (EU-Richtlinie 2014/55/EU).

## Features

### Core Features
- ✅ **ZUGFeRD 2.1** - Aktueller Standard (EN 16931 kompatibel)
- ✅ **Factur-X** - Französische Kompatibilität
- ✅ **XRechnung** - Reines XML für Behörden
- ✅ **Hybrid-Format** - PDF (menschlich lesbar) + XML (maschinell)
- ✅ **QR-Code** - XRechnung-QR für mobile Verarbeitung
- ✅ **Validierung** - Schema-Validierung vor Versand
- ✅ **Multi-Tax** - 19%, 7%, 0%, Reverse-Charge
- ✅ **Leitweg-ID** - Für öffentliche Auftraggeber
- ✅ **SEPA** - Zahlungsinformationen integriert

## Schnelle Verwendung

```python
from zugferd_generator import ZUGFeRDGenerator, Invoice

# Rechnung erstellen
invoice = Invoice(
    invoice_number="RE-2025-001",
    invoice_date="2025-02-25",
    due_date="2025-03-25",
    seller={
        "name": "Navii Automation GmbH",
        "street": "Musterstraße 1",
        "zip": "12345",
        "city": "Berlin",
        "country": "DE",
        "vat_id": "DE123456789",
        "tax_number": "1234567890"
    },
    buyer={
        "name": "Max Mustermann GmbH",
        "street": "Beispielweg 5",
        "zip": "54321",
        "city": "München",
        "country": "DE",
        "vat_id": "DE987654321"
    },
    items=[
        {
            "description": "Software-Lizenz",
            "quantity": 1,
            "unit": "C62",  # Stück
            "price": 1000.00,
            "vat_rate": 19
        },
        {
            "description": "Support-Vertrag",
            "quantity": 12,
            "unit": "MON",  # Monat
            "price": 99.00,
            "vat_rate": 19
        }
    ]
)

# ZUGFeRD PDF generieren
generator = ZUGFeRDGenerator()
pdf_bytes = generator.generate_zugferd(invoice)

# Speichern
with open("rechnung_RE-2025-001.pdf", "wb") as f:
    f.write(pdf_bytes)

print("✅ ZUGFeRD-Rechnung erstellt!")
```

## CLI Usage

```bash
# JSON zu ZUGFeRD
python zugferd_generator.py --input rechnung.json --output rechnung.pdf

# Validierung
python zugferd_generator.py --validate rechnung.pdf

# Nur XML extrahieren
python zugferd_generator.py --extract-xml rechnung.pdf --output rechnung.xml

# XRechnung (reines XML)
python zugferd_generator.py --input rechnung.json --output rechnung.xml --format xrechnung
```

## JSON-Input-Format

```json
{
  "invoice_number": "RE-2025-001",
  "invoice_date": "2025-02-25",
  "due_date": "2025-03-25",
  "delivery_date": "2025-02-20",
  "seller": {
    "name": "Navii Automation GmbH",
    "street": "Musterstraße 1",
    "zip": "12345",
    "city": "Berlin",
    "country": "DE",
    "vat_id": "DE123456789",
    "tax_number": "1234567890",
    "contact_email": "rechnung@navii.de",
    "iban": "DE89370400440532013000",
    "bic": "COBADEFFXXX"
  },
  "buyer": {
    "name": "Max Mustermann GmbH",
    "street": "Beispielweg 5",
    "zip": "54321",
    "city": "München",
    "country": "DE",
    "vat_id": "DE987654321",
    "buyer_reference": "MAX-12345"
  },
  "items": [
    {
      "position": 1,
      "description": "Software-Lizenz",
      "quantity": 1,
      "unit": "C62",
      "price": 1000.00,
      "vat_rate": 19
    },
    {
      "position": 2,
      "description": "Support-Vertrag",
      "quantity": 12,
      "unit": "MON",
      "price": 99.00,
      "vat_rate": 19
    }
  ],
  "payment_terms": "Zahlbar innerhalb von 30 Tagen",
  "leitweg_id": "123-456-789-01"
}
```

## Integration

### Mit GoBD-Rechnungsvalidator
```python
from gobd_validator import validate_rechnung
from zugferd_generator import ZUGFeRDGenerator

# Rechnung validieren
result = validate_rechnung("rechnung.pdf")
if result.is_valid:
    # ZUGFeRD generieren
    generator = ZUGFeRDGenerator()
    zugferd_pdf = generator.generate_from_json(result.extracted_data)
```

### Mit DATEV-Export
```python
from datev_export import DATEVExporter
from zugferd_generator import ZUGFeRDGenerator

# ZUGFeRD Rechnung -> DATEV Buchung
zugferd = ZUGFeRDGenerator()
invoice_data = zugferd.extract_from_pdf("rechnung.pdf")

# DATEV Buchung erstellen
exporter = DATEVExporter(kontenrahmen="SKR03")
exporter.add_invoice(invoice_data)
exporter.export("buchungen.csv")
```

## Preisgestaltung

| Plan | Preis | Inklusive |
|------|-------|-----------|
| **Starter** | 49€/Monat | 100 Rechnungen/Monat |
| **Professional** | 149€/Monat | 1.000 Rechnungen/Monat, API-Zugriff |
| **Enterprise** | 499€/Monat | Unlimited, White-Label, Support |

## Changelog

- **v1.0.0** - Initial release mit ZUGFeRD 2.1, Factur-X, XRechnung

## TODO

- [ ] ZUGFeRD 2.2 (neuester Standard)
- [ ] OCR-Erkennung aus bestehenden PDFs
- [ ] Massenverarbeitung (Batch-Upload)
- [ ] E-Mail-Versand direkt aus dem Tool
- [ ] Digitale Signatur (XAdES)
