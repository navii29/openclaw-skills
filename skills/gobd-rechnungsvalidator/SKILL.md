# GoBD-Rechnungsvalidator v2.5

**Version:** 2.5.0 | **Preis:** 149 EUR/Monat | **Support:** DE/EN/FR/IT/ES

Automatische Validierung von Rechnungs-PDFs auf GoBD-Konformität mit **erweitertem OCR-Preprocessing**, **mehrsprachiger Unterstützung** und **ZUGFeRD-Export**.

## Neue Features in v2.5 🆕

- ✅ **Erweitertes OCR-Preprocessing** - DPI-Optimierung, Kontrast, Schärfung, Binarisierung
- ✅ **Mehrsprachige Texterkennung** - DEU, ENG, FRA, ITA, SPA, NLD und mehr
- ✅ **Adaptive OCR-Strategien** - Presets für verschiedene Dokumenttypen
- ✅ **Automatische Spracherkennung** - Erkennt Dokumentsprache automatisch
- ✅ **Bildvorverarbeitung** - Deskewing, Rauschunterdrückung, Auto-Kontrast
- ✅ **Erweiterte Pattern-Erkennung** - Internationale Rechnungsformate

## Features aus v2.0

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
python3 gobd_validator_v25.py rechnung.pdf
```

### Mit spezifischem OCR-Preset
```bash
# Für gescannte Dokumente
python3 gobd_validator_v25.py gescannt.pdf --preset scanned

# Für schlechte Scan-Qualität
python3 gobd_validator_v25.py schlecht.pdf --preset low_quality

# Für mehrsprachige Rechnungen
python3 gobd_validator_v25.py international.pdf --preset invoice --lang deu eng fra
```

### ZUGFeRD-E-Rechnung generieren
```bash
python3 gobd_validator_v25.py rechnung.pdf --zugferd --output rechnung.zugferd.zip
```

### Batch-Verarbeitung (ganzer Ordner)
```bash
python3 gobd_validator_v25.py ./rechnungen/ --batch --preset invoice --lang deu eng
```

## OCR-Presets

| Preset | DPI | Beschreibung | Anwendungsfall |
|--------|-----|--------------|----------------|
| `scanned` | 300 | Optimal für gescannte Dokumente | Standard-Scanner |
| `low_quality` | 400 | Für schlechte Scan-Qualität | Alte/schechte Scans |
| `invoice` | 300 | Für mehrsprachige Rechnungen | **Standard** |
| `fast` | 150 | Schnelle Verarbeitung | Große Mengen |
| `max_quality` | 400 | Maximale Qualität | Kritische Dokumente |

## Python API

### Basis-Validierung
```python
from gobd_validator_v25 import EnhancedGoBDValidator

validator = EnhancedGoBDValidator(
    use_ocr=True,
    ocr_preset='invoice',
    ocr_languages=['deu', 'eng', 'fra']
)

result = validator.validate("rechnung.pdf")

print(f"Valide: {result.is_valid}")
print(f"Score: {result.score}/{result.max_score}")
print(f"ZUGFeRD-kompatibel: {result.zugferd_compatible}")
print(f"OCR verwendet: {result.ocr_used}")
print(f"Sprache: {result.ocr_language}")
print(f"OCR-Konfidenz: {result.ocr_confidence:.1%}")
```

### Mit erweiterten OCR-Optionen
```python
from gobd_validator_v25 import EnhancedGoBDValidator
from ocr_preprocessor import OCRConfig

# Eigene OCR-Konfiguration
validator = EnhancedGoBDValidator(
    use_ocr=True,
    ocr_preset='max_quality',
    ocr_languages=['deu', 'eng', 'fra', 'ita'],
    dpi=400
)

result = validator.validate("international.pdf")

# Preprocessing-Details
print(f"Preprocessing: {result.preprocessing_applied}")
```

### Direkte OCR-Nutzung
```python
from ocr_preprocessor import MultilingualOCR, OCRPresets

# OCR-Engine erstellen
ocr = MultilingualOCR(OCRPresets.invoice_multilingual())

# Text aus PDF extrahieren
results = ocr.extract_from_pdf("rechnung.pdf")

for result in results:
    print(f"Seite {result.page_num}:")
    print(f"  Sprache: {result.language}")
    print(f"  Konfidenz: {result.confidence:.1%}")
    print(f"  Preprocessing: {result.preprocessing_applied}")
    print(f"  Text: {result.text[:200]}...")
```

### Mit ZUGFeRD-Export
```python
from gobd_validator_v25 import EnhancedGoBDValidator

validator = EnhancedGoBDValidator()

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
from gobd_validator_v25 import batch_validate

stats = batch_validate(
    folder_path="./rechnungen/",
    output_json="ergebnisse.json",
    ocr_preset='invoice',
    languages=['deu', 'eng', 'fra']
)

print(f"Geprüft: {stats['total']}")
print(f"Valide: {stats['valid']}")
print(f"ZUGFeRD-fähig: {stats['zugferd_compatible']}")
print(f"OCR genutzt: {stats['ocr_used']}")
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
  "ocr_used": true,
  "ocr_confidence": 0.95,
  "ocr_language": "deu",
  "preprocessing_applied": ["resize_to_300dpi", "contrast", "sharpen", "denoise", "binarize"],
  "missing_fields": ["lieferdatum"],
  "extracted_data": {
    "lieferant_name": "Muster GmbH",
    "lieferant_anschrift": "Musterstraße 1, 12345 Berlin",
    "steuernummer": "1234567890",
    "ust_id": "DE123456789",
    "rechnungsdatum": "15.02.2025",
    "rechnungsnummer": "RE-2025-001",
    "gesamtbetrag": "1.190,00 €",
    "ust_satz": "19%",
    "erkannte_sprache": "deu"
  },
  "warnings": ["✅ OCR abgeschlossen (Konfidenz: 95%, Sprache: deu)"]
}
```

## Installation

### Basis-Installation
```bash
pip install pdfplumber pypdf Pillow
```

### Mit erweitertem OCR
```bash
pip install pytesseract pdf2image Pillow

# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Sprachpakete installieren
brew install tesseract-lang  # macOS
sudo apt-get install tesseract-ocr-deu tesseract-ocr-eng tesseract-ocr-fra
```

### Python-Abhängigkeiten
```bash
pip install -r requirements.txt
```

## Dateistruktur

```
gobd-rechnungsvalidator/
├── SKILL.md                      # Diese Dokumentation
├── gobd_validator_v25.py         # Haupt-Script (v2.5)
├── ocr_preprocessor.py           # OCR-Preprocessing-Modul
├── gobd_validator_v2.py          # Legacy v2.0
├── test_ocr_preprocessor.py      # Test-Suite
├── requirements.txt              # Python-Abhängigkeiten
└── tests/
    └── test_v2.py
```

## Integration

### Mit ZUGFeRD-Generator
```python
# PDF → Validierung → E-Rechnung
validator = EnhancedGoBDValidator()
result = validator.validate("rechnung.pdf")

if result.zugferd_compatible:
    zugferd_path = validator.generate_zugferd("rechnung.pdf")
    # ZUGFeRD-Datei kann direkt an Kunden gesendet werden
```

### Mit DATEV-Export
```python
from gobd_validator_v25 import EnhancedGoBDValidator
from datev_export import DATEVExporter

validator = EnhancedGoBDValidator()
exporter = DATEVExporter(kontenrahmen="SKR03")

# Rechnung validieren und Buchung erstellen
result = validator.validate("rechnung.pdf")
if result.is_valid:
    exporter.add_buchung_from_gobd(result.extracted_data)
    exporter.export("datev.csv")
```

## Unterstützte Sprachen

| Sprache | Code | Status |
|---------|------|--------|
| Deutsch | deu | ✅ Voll unterstützt |
| Englisch | eng | ✅ Voll unterstützt |
| Französisch | fra | ✅ Voll unterstützt |
| Italienisch | ita | ✅ Voll unterstützt |
| Spanisch | spa | ✅ Voll unterstützt |
| Niederländisch | nld | ✅ Unterstützt |
| Polnisch | pol | ✅ Unterstützt |
| Tschechisch | ces | ✅ Unterstützt |

## Preisgestaltung

| Plan | Preis | Features |
|------|-------|----------|
| **Basic** | 49€/Monat | 100 Rechnungen/Monat |
| **Professional** | 149€/Monat | 1.000 Rechnungen, erweitertes OCR, ZUGFeRD |
| **Enterprise** | 499€/Monat | Unlimited, API, Batch-Processing, alle Sprachen |

## Changelog

### v2.5.0 (2025-02-25)
- 🆕 **Erweitertes OCR-Preprocessing** - DPI, Kontrast, Schärfung, Binarisierung
- 🆕 **Mehrsprachige Unterstützung** - DEU, ENG, FRA, ITA, SPA, NLD
- 🆕 **OCR-Presets** - scanned, low_quality, invoice, fast, max_quality
- 🆕 **Automatische Spracherkennung**
- 🆕 **Bildvorverarbeitung** - Deskewing, Rauschunterdrückung
- 🆕 **Erweiterte Pattern-Erkennung** - Internationale Rechnungen
- 🆕 **OCR-Konfidenz-Metriken**

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
- [ ] GPU-beschleunigtes OCR
- [ ] Cloud-OCR-Integration (AWS Textract, Google Vision)

## Support

Bei Fragen oder Problemen:
- 📧 support@navii-automation.de
- 📱 +49 123 456789

---

**Made with ❤️ by Navii Automation**
