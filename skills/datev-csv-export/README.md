# 📊 DATEV-CSV-Export

> Erzeugt DATEV-konforme CSV-Dateien für den direkten Import in DATEV Unternehmen Online

## ⚡ Schnellstart

```bash
# Installation
pip install -r requirements.txt

# Beispiel generieren
python datev_export.py --example --output beispiel.csv --stats

# CSV validieren
python datev_export.py --validate datev.csv
```

## 🎯 Features

- ✅ **Kontenrahmen SKR03 & SKR04**
- ✅ **Automatische USt-Berechnung** (19%, 7%)
- ✅ **Datum-Format-Konvertierung** (DD.MM.YYYY → TTMMJJ)
- ✅ **CSV-Validierung** vor Import
- ✅ **JSON API** für Integration

## 📋 DATEV-Format

```csv
Datum;Konto;Gegenkonto;BU-Schlüssel;Umsatz;S/H;Währung;Buchungstext;Beleg
150224;8400;1400;;1000,00;H;EUR;Verkauf;RE-001
```

## 🐍 Python API

```python
from datev_export import DATEVExporter, Buchungssatz

exporter = DATEVExporter(kontenrahmen="SKR03")

# Einfache Buchung
exporter.add_buchung(Buchungssatz(
    datum="15.02.2024",
    konto=8400,
    gegenkonto=1400,
    umsatz=1000.00,
    soll_haben="H"
))

# Automatische Rechnung mit USt
exporter.add_rechnung(
    datum="20.02.2024",
    brutto=119.00,
    ust_satz=19,
    konto=7020,
    gegenkonto=1600,
    ist_eingangsrechnung=True
)

exporter.export("buchungen.csv")
```

## 🔧 Kontenrahmen

### SKR03 (Standard)
- `1200` Bank
- `1400` Forderungen (Kunden)
- `1600` Verbindlichkeiten (Kreditoren)
- `8400` Erlöse 19% USt
- `1576` Vorsteuer 19%

### SKR04
- `1800` Bank
- `1200` Forderungen
- `1600` Verbindlichkeiten
- `4400` Erlöse 19% USt
- `1401` Vorsteuer 19%

## 💡 Use-Cases

1. **Buchhaltungsbüro:** Automatischer Export aus eigener Software
2. **E-Commerce:** Shopify/WooCommerce → DATEV
3. **GoBD-Validator + DATEV:** Rechnung validieren → Buchung erzeugen → DATEV-Import

## 🚀 Integration

```python
# Kombination mit GoBD-Validator
from gobd_validator import validate_rechnung
from datev_export import DATEVExporter

result = validate_rechnung("rechnung.pdf")
if result.is_valid:
    exporter = DATEVExporter("SKR03")
    exporter.add_rechnung(
        datum=result.extracted_data['rechnungsdatum'],
        brutto=float(result.extracted_data['gesamtbetrag'].replace('.', '').replace(',', '.')),
        ust_satz=int(result.extracted_data['ust_satz'].replace('%', '')),
        konto=8400,
        gegenkonto=1400,
        text=f"Rechnung {result.extracted_data['rechnungsnummer']}"
    )
    exporter.export("datev_import.csv")
```

## 📊 Validierung

```bash
python datev_export.py --validate meine_buchungen.csv
```

Prüft:
- Datumsformat (TTMMJJ)
- Konten im gültigen Bereich
- Konto ≠ Gegenkonto
- Soll/Haben = S oder H
- Währung = EUR

## 💰 Preisgestaltung (SaaS)

| Plan | Preis | Features |
|------|-------|----------|
| Free | 0€ | 100 Buchungen/Monat |
| Pro | 19€/Monat | 10.000 Buchungen, API |
| Kanzlei | 49€/Monat | Unlimited, Multi-Mandant |

## 📦 Output

```json
{
  "anzahl": 3,
  "summe_soll": 1119.00,
  "summe_haben": 1119.00,
  "differenz": 0.00,
  "kontenrahmen": "SKR03"
}
```

## 🔗 Related

- **Skill #1:** GoBD-Rechnungsvalidator (Rechnungen prüfen)
- **Skill #2:** DATEV-CSV-Export (Buchungen erzeugen)

## 📝 Lizenz

MIT License
