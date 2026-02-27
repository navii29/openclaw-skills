# German Accounting Suite

**Version:** 1.0.0 | **Preis:** 299 EUR/Monat | **Bundle**

Komplette Accounting-Automation für den deutschen Markt: PDF → E-Rechnung → Buchhaltung → Zahlung

## Enthaltene Skills

| Skill | Version | Funktion |
|-------|---------|----------|
| gobd-rechnungsvalidator | **v2.5.0** | PDF Validierung mit erweitertem OCR |
| zugferd-generator | v1.0.0 | E-Rechnung (ZUGFeRD/XRechnung) |
| datev-csv-export | v2.0.0 | DATEV Export mit Smart-Suggest |
| sepa-xml-generator | v1.0.0 | SEPA Überweisung/Lastschrift |

### v2.5 OCR-Verbesserungen
- ✅ **Bildvorverarbeitung**: DPI-Optimierung, Kontrast, Schärfung, Binarisierung
- ✅ **Mehrsprachige OCR**: DEU, ENG, FRA, ITA, SPA, NLD
- ✅ **Adaptive Presets**: scanned, low_quality, invoice, fast, max_quality
- ✅ **Automatische Spracherkennung**
- ✅ **OCR-Konfidenz-Metriken**

## Workflow

```
PDF Rechnung
    ↓
🔍 GoBD Validierung (OCR falls nötig)
    ↓
🧾 ZUGFeRD E-Rechnung generieren
    ↓
📊 DATEV Buchhaltung exportieren
    ↓
💳 SEPA Zahlung vorbereiten
```

## Schnellstart

### Einzelne Rechnung
```bash
python3 suite_integration.py rechnung.pdf --iban DE89370400440532013000

# Ausgabe:
# 🔍 Schritt 1: PDF validieren...
#    ✅ Valid (8/9 Punkte)
# 🧾 Schritt 2: ZUGFeRD E-Rechnung generieren...
#    ✅ ./output/rechnung.zugferd.zip
# 📊 Schritt 3: DATEV Export...
#    ✅ ./output/rechnung_datev.csv
# 💳 Schritt 4: SEPA Zahlung vorbereiten...
#    ✅ ./output/rechnung_sepa.xml
```

### Batch-Verarbeitung
```bash
python3 suite_integration.py ./rechnungen/ --batch --iban DE89370400440532013000

# Ausgabe:
# 🔄 Batch-Verarbeitung: 50 PDFs
# ==================================================
# [1/50] rechnung_001.pdf
# ...
# 📊 BATCH-ZUSAMMENFASSUNG
# Geprüft:     50
# Valide:      48 ✅
# ZUGFeRD:     45 🧾
# DATEV:       48 📊
```

## Python API

```python
from suite_integration import GermanAccountingSuite

# Suite initialisieren
suite = GermanAccountingSuite(use_ocr=True, smart_suggest=True)

# Einzelne Rechnung
result = suite.process_invoice(
    pdf_path="rechnung.pdf",
    output_dir="./output",
    creditor_iban="DE89370400440532013000"
)

print(result.summary())
# 📄 PDF: rechnung.pdf
#    Valid: ✅
#    ZUGFeRD: ✅ ./output/rechnung.zugferd.zip
#    DATEV: ✅ ./output/rechnung_datev.csv
#    SEPA: ✅ ./output/rechnung_sepa.xml
```

### Batch-Verarbeitung
```python
results = suite.batch_process(
    pdf_folder="./rechnungen/",
    output_dir="./output",
    creditor_iban="DE89370400440532013000"
)

for result in results:
    if result.is_valid:
        print(f"✅ {result.pdf_path}: Erfolg")
    else:
        print(f"❌ {result.pdf_path}: {result.errors}")
```

## Einzelne Skills nutzen

### Nur GoBD Validierung
```python
from gobd_validator_v2 import GoBDValidator

validator = GoBDValidator(use_ocr=True)
result = validator.validate("rechnung.pdf")

print(f"Valide: {result.is_valid}")
print(f"Score: {result.score}/{result.max_score}")
```

### Nur ZUGFeRD generieren
```python
from zugferd_generator import ZUGFeRDGenerator, Invoice, Party

generator = ZUGFeRDGenerator()
invoice = Invoice(...)
zugferd_bytes = generator.generate_zugferd(invoice)
```

### Nur DATEV Export
```python
from datev_export_v2 import DATEVExporter

exporter = DATEVExporter(smart_suggest=True)
exporter.add_rechnung_smart(datum="15.02.2025", brutto=119.00, text="Miete")
exporter.export("datev.csv")
```

### Nur SEPA Zahlung
```python
from sepa_generator import SEPAGenerator, CreditTransfer

sepa = SEPAGenerator()
transfer = CreditTransfer(
    creditor_iban="DE89370400440532013000",
    creditor_name="Muster GmbH",
    amount=100.00
)
sepa.add_credit_transfer(transfer)
sepa.generate_xml("sepa.xml")
```

## Installation

```bash
# Alle Skills installieren
pip install -r gobd-rechnungsvalidator/requirements.txt
pip install -r zugferd-generator/requirements.txt
pip install -r datev-csv-export/requirements.txt
pip install -r sepa-xml-generator/requirements.txt

# OCR Support (optional)
pip install pytesseract pdf2image
brew install tesseract  # macOS
```

## Preisgestaltung

| Plan | Preis | Enthalten |
|------|-------|-----------|
| **Basic** | 99€/Monat | 100 Rechnungen/Monat |
| **Professional** | 299€/Monat | 1.000 Rechnungen, alle Features |
| **Enterprise** | 799€/Monat | Unlimited, API, Support |

## Changelog

### v1.1.0 (2025-02-25) - OCR-Upgrade
- 🆕 **GoBD Validator v2.5** mit erweitertem OCR
  - Bildvorverarbeitung (DPI, Kontrast, Schärfung, Binarisierung)
  - Mehrsprachige Unterstützung (DE, EN, FR, IT, ES, NL)
  - Adaptive OCR-Presets für verschiedene Dokumenttypen
  - Automatische Spracherkennung
  - OCR-Konfidenz-Metriken
- 🆕 Unterstützung für internationale Rechnungsformate
- 🆕 Verbesserte Erkennungsraten bei gescannten Dokumenten

### v1.0.0 (2025-02-25)
- Initiale Suite-Veröffentlichung
- Integration aller 4 Skills
- Batch-Verarbeitung
- CLI Interface

## Roadmap

- [ ] Web-Interface
- [ ] REST API
- [ ] Automatischer Mail-Versand
- [ ] Digitale Signatur
- [ ] DATEV-Online Direktanbindung
