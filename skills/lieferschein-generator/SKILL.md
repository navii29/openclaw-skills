# Lieferschein-Generator (Delivery Note Generator)

**Version:** 1.0.0 | **Preis:** 49 EUR/Monat | **GoBD-konform** 🇩🇪

Erstelle GoBD-konforme Lieferscheine mit QR-Code Tracking, Seriennummern-Erfassung und elektronischer Unterschriftsfunktion.

## Warum dieser Skill?

- 📦 **Pflicht für jeden Versand** - Lieferscheine sind gesetzlich vorgeschrieben
- 🔍 **Tracking-QR-Code** - Kunden können Lieferung online verfolgen
- 📝 **Seriennummern-Tracking** - Wichtig für Garantie und Rückverfolgbarkeit
- ✍️ **Digitale Unterschrift** - Empfangsbestätigung direkt auf dem Lieferschein
- 📊 **GoBD-konform** - Revisionssichere Archivierung garantiert

## Schnellstart

### Einzelnen Lieferschein erstellen

```python
from lieferschein_generator import LieferscheinGenerator, LieferscheinPosition

gen = LieferscheinGenerator()

# Absender (deine Firma)
gen.set_absender(
    name="Muster GmbH",
    strasse="Musterstraße 1",
    plz_ort="10115 Berlin",
    steuernr="DE123456789"
)

# Empfänger
gen.set_empfaenger(
    name="Kunde AG",
    strasse="Kundenweg 5",
    plz_ort="20095 Hamburg"
)

# Positionen hinzufügen
gen.add_position(LieferscheinPosition(
    artikelnr="ART-001",
    bezeichnung="Premium Laptop",
    menge=2,
    einheit="Stk",
    seriennummern=["SN123456", "SN123457"]
))

# QR-Code für Tracking
gen.set_tracking(
    tracking_url="https://tracking.de/LS-2025-001",
    tracking_nummer="LS-2025-001"
)

# PDF generieren
gen.generate("lieferschein_001.pdf")
```

### CLI Nutzung

```bash
# Aus JSON generieren
python lieferschein_generator.py --input lieferschein.json --output lieferschein.pdf

# Mit Tracking-QR
python lieferschein_generator.py --input lieferschein.json --tracking-url "https://track.de/123"

# Unterschriften-Feld hinzufügen
python lieferschein_generator.py --input lieferschein.json --signature
```

## JSON Input-Format

```json
{
  "lieferschein_nummer": "LS-2025-001",
  "lieferschein_datum": "26.02.2025",
  "lieferdatum": "28.02.2025",
  "auftragsnummer": "A-2025-042",
  "kundennummer": "K-1234",
  "absender": {
    "name": "Muster GmbH",
    "zusatz": "Abteilung Vertrieb",
    "strasse": "Musterstraße 1",
    "plz_ort": "10115 Berlin",
    "telefon": "030 123456",
    "email": "info@muster-gmbh.de",
    "steuernr": "DE123456789",
    "ustid": "DE123456789"
  },
  "empfaenger": {
    "name": "Kunde AG",
    "zusatz": "Einkauf",
    "strasse": "Kundenweg 5",
    "plz_ort": "20095 Hamburg",
    "land": "Deutschland"
  },
  "lieferadresse": {
    "name": "Kunde AG Lager",
    "strasse": "Lagerstraße 10",
    "plz_ort": "20095 Hamburg"
  },
  "positionen": [
    {
      "pos": 1,
      "artikelnr": "ART-001",
      "bezeichnung": "Premium Laptop",
      "menge": 2,
      "einheit": "Stk",
      "seriennummern": ["SN123456", "SN123457"],
      "charge": "CHG-2025-A",
      "gewicht_kg": 2.5
    }
  ],
  "tracking": {
    "nummer": "LS-2025-001",
    "url": "https://tracking.muster-gmbh.de/LS-2025-001",
    "dienstleister": "DHL"
  },
  "hinweise": "Bitte bei Schäden sofort melden",
  "unterschrift_erforderlich": true
}
```

## Features

### 1. QR-Code Tracking

Jeder Lieferschein enthält einen QR-Code mit:
- Tracking-URL für Kunden
- Interne Lieferschein-Nummer
- Versanddienstleister-Link

```python
gen.set_tracking(
    tracking_url="https://meine-firma.de/track/LS-001",
    tracking_nummer="LS-001",
    dienstleister="DHL"
)
```

### 2. Seriennummern-Tracking

Erfasse Seriennummern für Garantie und Rückverfolgbarkeit:

```python
gen.add_position(LieferscheinPosition(
    artikelnr="SERVER-001",
    bezeichnung="Enterprise Server",
    menge=3,
    seriennummern=["SN001", "SN002", "SN003"]
))
```

### 3. Digitale Unterschrift

Füge ein Unterschriftenfeld hinzu:

```python
gen.enable_unterschrift_feld(
    datum_feld=True,
    name_feld=True,
    stempel_feld=True
)
```

### 4. Versandetikett-Export

Generiere zusätzlich ein Versandetikett:

```python
gen.generate_versandetikett("etikett.pdf", format="DIN_A6")
```

## GoBD-Konformität

Dieser Generator erfüllt alle GoBD-Anforderungen:

| Anforderung | Umsetzung |
|-------------|-----------|
| **Vollständigkeit** | Alle Pflichtfelder enthalten |
| **Richtigkeit** | Validierung vor Export |
| **Nachvollziehbarkeit** | Zeitstempel + Referenznummern |
| **Unveränderbarkeit** | PDF/A-1b Standard |
| **Aufbewahrung** | Archivierbar digital |

## API Reference

### LieferscheinGenerator

```python
LieferscheinGenerator(
    template: str = "standard",  # "standard", "minimal", "detailed"
    gobd_compliant: bool = True
)

Methods:
- set_absender(**kwargs) -> None
- set_empfaenger(**kwargs) -> None
- set_lieferadresse(**kwargs) -> None
- add_position(LieferscheinPosition) -> None
- set_tracking(url, nummer, dienstleister) -> None
- enable_unterschrift_feld(**kwargs) -> None
- generate(output_path) -> bool
- validate() -> dict
```

### LieferscheinPosition

```python
LieferscheinPosition(
    artikelnr: str = "",
    bezeichnung: str,
    menge: float,
    einheit: str = "Stk",
    seriennummern: List[str] = None,
    charge: str = "",
    mhd: str = "",           # Mindesthaltbarkeitsdatum
    gewicht_kg: float = 0.0
)
```

## Integration

### Mit ZUGFeRD-Rechnung

```python
from zugferd_generator import ZUGFeRDGenerator
from lieferschein_generator import LieferscheinGenerator

# Rechnung und Lieferschein zusammen
rechnung = ZUGFeRDGenerator()
lieferschein = LieferscheinGenerator()

# Gleiche Daten verwenden
lieferschein.import_from_rechnung(rechnung)
lieferschein.generate("lieferschein.pdf")
```

### Mit DATEV-Export

```python
from datev_export_v2 import DATEVExporter
from lieferschein_generator import LieferscheinGenerator

# Lieferschein-Nummer in DATEV erfassen
exporter = DATEVExporter()
exporter.add_buchung(Buchungssatz(
    datum="26.02.2025",
    konto=1200,
    gegenkonto=1400,
    buchungstext="Lieferschein LS-2025-001"
))
```

## Preisgestaltung

| Plan | Preis | Features |
|------|-------|----------|
| **Starter** | 19€/Monat | 50 Lieferscheine/Monat, Basis-Template |
| **Business** | 49€/Monat | Unlimited, alle Templates, QR-Tracking |
| **Enterprise** | 99€/Monat | API-Zugriff, White-Label, Support |

## Changelog

### v1.0.0 (2025-02-26)
- 🆕 Initiale Version
- 🆕 GoBD-konforme PDF-Generierung
- 🆕 QR-Code Tracking
- 🆕 Seriennummern-Erfassung
- 🆕 Unterschriften-Feld
- 🆕 JSON-Import/Export

## Roadmap

- [ ] Excel-Import
- [ ] E-Mail-Versand direkt aus Generator
- [ ] Status-Tracking (geliefert, retourniert)
- [ ] Multi-Package Support
- [ ] REST API
