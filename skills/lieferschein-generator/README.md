# 🚚 Lieferschein-Generator

**GoBD-konforme Delivery Notes mit QR-Code Tracking**

[![Tests](https://img.shields.io/badge/tests-5%2F5%20passing-green)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![License](https://img.shields.io/badge/license-Commercial-orange)]()

## Schnellstart

```bash
# Installation
pip install -r requirements.txt

# Beispiel-Lieferschein erstellen
python lieferschein_generator.py \
  --input example_lieferschein.json \
  --output lieferschein.pdf \
  --signature
```

## Features

- ✅ **GoBD-konform** - Revisionssichere Archivierung
- 📱 **QR-Code Tracking** - Kunden können Lieferung verfolgen
- 📝 **Seriennummern-Tracking** - Für Garantie & Rückverfolgbarkeit  
- ✍️ **Digitale Unterschrift** - Empfangsbestätigung auf dem Lieferschein
- 🐍 **Python API + CLI** - Flexibel integrierbar

## Verwendung

### Als Python-Bibliothek

```python
from lieferschein_generator import LieferscheinGenerator, LieferscheinPosition

gen = LieferscheinGenerator()

gen.set_absender(
    name="Deine Firma GmbH",
    strasse="Musterstraße 1",
    plz_ort="10115 Berlin",
    steuernr="DE123456789"
)

gen.set_empfaenger(
    name="Kunde AG",
    strasse="Kundenweg 5",
    plz_ort="20095 Hamburg"
)

gen.add_position(LieferscheinPosition(
    artikelnr="ART-001",
    bezeichnung="Premium Laptop",
    menge=2,
    seriennummern=["SN123456", "SN123457"]
))

gen.set_tracking(
    tracking_url="https://tracking.de/LS-001",
    tracking_nummer="LS-001"
)

gen.generate("lieferschein.pdf")
```

### CLI

```bash
# Basis-Generierung
python lieferschein_generator.py -i input.json -o output.pdf

# Mit Tracking-QR
python lieferschein_generator.py -i input.json -o output.pdf \
  --tracking-url "https://track.de/123"

# Mit Unterschriftenfeld
python lieferschein_generator.py -i input.json -o output.pdf --signature
```

## Dateien

| Datei | Beschreibung |
|-------|-------------|
| `lieferschein_generator.py` | Haupt-Implementierung |
| `example_lieferschein.json` | Beispiel-Input |
| `test_generator.py` | Testsuite |
| `requirements.txt` | Python-Abhängigkeiten |
| `SKILL.md` | Detaillierte Dokumentation |

## Tests ausführen

```bash
python test_generator.py
```

Ausgabe:
```
✅ PASS: Basis-Generation
✅ PASS: JSON-Import
✅ PASS: Unterschrift
✅ PASS: Validierung
✅ PASS: CLI-Modus

Ergebnis: 5/5 Tests bestanden
🎉 Alle Tests erfolgreich!
```

## Lizenz

Commercial - NAVII Automation

## Support

Bei Fragen: kontakt@navii-automation.de
