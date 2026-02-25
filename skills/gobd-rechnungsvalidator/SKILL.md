# GoBD-Rechnungsvalidator v2.0

**Version:** 2.0.0 | **Preis:** 149 EUR/Monat | **Support:** DE/EN

Automatische Validierung von Rechnungs-PDFs auf GoBD-Konformität mit **ZUGFeRD-Export** und **OCR-Unterstützung**.

## Neue Features in v2.0 🆕

- ✅ **ZUGFeRD-Export** - PDF validieren → E-Rechnung generieren
- ✅ **OCR-Unterstützung** - Gescannte Rechnungen erkennen (Tesseract)
- ✅ **Batch-Verarbeitung** - Ganze Ordner auf einmal prüfen
- ✅ **ZUGFeRD-Kompatibilitäts-Check** - Vorab prüfen ob E-Rechnung möglich

## GoBD-Pflichtangaben (§14 UStG)

1. ✅ Name und Anschrift des leistenden Unternehmers
2. ✅ Name und Anschrift des Leistungsempfängers
3. ✅ Steuernummer oder USt-IdNr des Lieferanten
4. ✅ Ausstellungsdatum
5. ✅ Fortlaufende Rechnungsnummer
6. ✅ Menge und Handelsbezeichnung der Leistungen
7. ✅ Zeitpunkt der Lieferung/Leistung
8. ✅ Entgelt und Steuerbeträge
9. ✅ Steuersatz oder Steuerbefreiung
10. ⚠️ Hinweis §13b UStG (optional)
11. ⚠️ Mängelhinweis §14c UStG (optional)

## Schnelle Verwendung

### Einzelne Rechnung prüfen
```bash
python3 gobd_validator_v2.py rechnung.pdf
```

### ZUGFeRD-E-Rechnung generieren
```bash
python3 gobd_validator_v2.py rechnung.pdf --zugferd --output rechnung.zugferd.zip
```

### Batch-Verarbeitung (ganzer Ordner)
```bash
python3 gobd_validator_v2.py ./rechnungen/ --batch --output results.json
```

### Mit OCR (für gescannte PDFs)
```bash
python3 gobd_validator_v2.py gescannt.pdf
# OCR wird automatisch verwendet wenn kein Text gefunden wird
```

## Python API

### Basis-Validierung
```python
from gobd_validator_v2 import GoBDValidator

validator = GoBDValidator(use_ocr=True)
result = validator.validate("rechnung.pdf")

print(f"Valide: {result.is_valid}")
print(f"Score: {result.score}/{result.max_score}")
print(f"ZUGFeRD-kompatibel: {result.zugferd_compatible}")
```

### Mit ZUGFeRD-Export
```python
from gobd_validator_v2 import GoBDValidator

validator = GoBDValidator()

# Validieren + ZUGFeRD generieren
zugferd_path = validator.generate_zugferd(
    pdf_path="rechnung.pdf",
    output_path="rechnung.zugferd.zip"
)

if zugferd_path:
    print(f"✅ E-Rechnung erstellt: {zugferd_path}")
else:
    print("❌ Nicht ZUGFeRD-kompatibel")
```

### Batch-Verarbeitung
```python
from gobd_validator_v2 import batch_validate

stats = batch_validate(
    folder_path="./rechnungen/",
    output_json="ergebnisse.json"
)

print(f"Geprüft: {stats['total']}")
print(f"Valide: {stats['valid']}")
print(f"ZUGFeRD-fähig: {stats['zugferd_compatible']}")
```

## Ausgabe-Format

```json
{
  "filename": "rechnung_001.pdf",
  "is_valid": true,
  "score": 8,
  "max_score": 9,
  "confidence": 0.89,
  "zugferd_compatible": true,
  "missing_fields": ["lieferdatum"],
  "extracted_data": {
    "lieferant_name": "Muster GmbH",
    "lieferant_anschrift": "Musterstraße 1, 12345 Berlin",
    "steuernummer": "1234567890",
    "ust_id": "DE123456789",
    "rechnungsdatum": "15.02.2025",
    "rechnungsnummer": "RE-2025-001",
    "gesamtbetrag": "1.190,00 €",
    "ust_satz": "19%"
  },
  "warnings": ["✅ OCR wurde verwendet"]
}
```

## Installation

```bash
pip install pdfplumber pypdf

# Für OCR-Unterstützung (optional):
pip install pytesseract pdf2image
brew install tesseract  # macOS
```

## Integration

### Mit ZUGFeRD-Generator
```python
# PDF → Validierung → E-Rechnung
validator = GoBDValidator()
result = validator.validate("rechnung.pdf")

if result.zugferd_compatible:
    zugferd_path = validator.generate_zugferd("rechnung.pdf")
    # ZUGFeRD-Datei kann direkt an Kunden gesendet werden
```

### Mit DATEV-Export
```python
from gobd_validator_v2 import GoBDValidator
from datev_export import DATEVExporter

validator = GoBDValidator()
exporter = DATEVExporter(kontenrahmen="SKR03")

# Rechnung validieren und Buchung erstellen
result = validator.validate("rechnung.pdf")
if result.is_valid:
    exporter.add_buchung_from_gobd(result.extracted_data)
    exporter.export("datev.csv")
```

## Preisgestaltung

| Plan | Preis | Features |
|------|-------|----------|
| **Basic** | 49€/Monat | 100 Rechnungen/Monat |
| **Professional** | 149€/Monat | 1.000 Rechnungen, OCR, ZUGFeRD |
| **Enterprise** | 499€/Monat | Unlimited, API, Batch-Processing |

## Changelog

### v2.0.0 (2025-02-25)
- 🆕 ZUGFeRD-Export Integration
- 🆕 OCR-Unterstützung (Tesseract)
- 🆕 Batch-Verarbeitung
- 🆕 ZUGFeRD-Kompatibilitäts-Check

### v1.0.0
- Initiale Version
- GoBD-Pflichtfelder-Validierung
- PDF-Text-Extraktion

## TODO / Roadmap

- [ ] QR-Code/ERechnung-Unterstützung
- [ ] Automatische Kontenzuordnung (ML)
- [ ] Direkter DATEV-Export
- [ ] REST API
- [ ] Web-Interface
