# DATEV-CSV-Export v2.0

**Version:** 2.0.0 | **Preis:** 79 EUR/Monat | **Support:** DE/EN

DATEV-konformer CSV-Export mit **automatischen Kontenvorschlägen** (ML-basiert) für Buchhaltungsdaten.

## Neue Features in v2.0 🆕

- ✅ **Smarte Kontenvorschläge** - ML-basierte Zuordnung basierend auf Buchungstext
- ✅ **Lernendes System** - Verbessert sich mit jeder Buchung
- ✅ **Automatische USt-Aufteilung** - Brutto → Netto + USt
- ✅ **Validierung** - Prüft DATEV-Konformität vor Export
- ✅ **Statistiken** - Überblick über alle Buchungen

## Kontenrahmen

### SKR03 (Standard für Kleinunternehmen)
| Konto | Beschreibung |
|-------|-------------|
| 1200 | Bank |
| 1400 | Forderungen aus LuL |
| 1600 | Verbindlichkeiten aus LuL |
| 7020 | Bezogene Waren |
| 7200 | Miete |
| 7300 | Strom |
| 7400 | Telefon/Internet |
| 7500 | Büromaterial |
| 7600 | Rechts- und Beratungskosten |
| 7700 | Werbung |
| 7800 | Reisekosten |
| 7900 | Versicherungen |
| 8400 | Erlöse 19% USt |

### SKR04 (neuer Standard)
Verfügbar auf Anfrage

## Schnelle Verwendung

### Basis-Export
```bash
python3 datev_export_v2.py --input buchungen.json --output datev.csv
```

### Mit smarten Kontenvorschlägen
```bash
python3 datev_export_v2.py --input buchungen.json --smart
# 🤖 Konto 7200 vorgeschlagen (85% confidence) - Miete
# 🤖 Konto 8400 vorgeschlagen (85% confidence) - Erlös
```

### Mit Statistiken
```bash
python3 datev_export_v2.py --input buchungen.json --stats
# 📊 Statistiken:
#    Konten: 5
#    - Konto 7200: 3 Buchungen, 3000.00 EUR
#    - Konto 8400: 2 Buchungen, 5000.00 EUR
```

## Python API

### Basis-Export
```python
from datev_export_v2 import DATEVExporter, Buchungssatz

exporter = DATEVExporter(kontenrahmen="SKR03")

# Einzelne Buchung
exporter.add_buchung(Buchungssatz(
    datum="15.02.2025",
    konto=8400,
    gegenkonto=1200,
    bu_schluessel="",
    umsatz=1000.00,
    soll_haben="H",
    buchungstext="Software-Lizenz"
))

exporter.export("datev.csv")
```

### Automatische USt-Aufteilung
```python
from datev_export_v2 import DATEVExporter

exporter = DATEVExporter()

# 119€ Brutto, 19% USt → 100€ Netto + 19€ USt
exporter.add_rechnung(
    datum="15.02.2025",
    brutto=119.00,
    ust_satz=19,
    konto=8400,      # Erlöse
    gegenkonto=1400,  # Forderungen
    text="Rechnung RE-001"
)
# Erzeugt 2 Buchungen:
# - 8400 (Erlös) an 1400: 100,00
# - 4800 (USt) an 1400: 19,00
```

### Smarte Kontenvorschläge
```python
from datev_export_v2 import DATEVExporter

exporter = DATEVExporter(smart_suggest=True)

# Automatische Kontovorschläge
konto, confidence = exporter.add_rechnung_smart(
    datum="15.02.2025",
    brutto=1000.00,
    text="Miete Büro Berlin",  # → Konto 7200 vorgeschlagen
    ust_satz=19
)

print(f"Konto {konto} vorgeschlagen ({confidence:.0%})")
# Ausgabe: Konto 7200 vorgeschlagen (85%)
```

## JSON-Input-Format

```json
[
  {
    "datum": "15.02.2025",
    "brutto": 1190.00,
    "ust_satz": 19,
    "text": "Software-Lizenz",
    "belegnummer": "RE-001"
  },
  {
    "datum": "16.02.2025",
    "brutto": 500.00,
    "ust_satz": 19,
    "text": "Miete Büro",
    "belegnummer": "M-02"
  }
]
```

## Smarte Kontovorschläge

### Automatisch erkannte Muster

| Text enthält | Vorgeschlagenes Konto | Confidence |
|-------------|----------------------|------------|
| Miete, Pacht | 7200 | 85% |
| Strom, Gas, Energie | 7300 | 85% |
| Telefon, Internet | 7400 | 85% |
| Büromaterial | 7500 | 85% |
| Anwalt, Steuerberater | 7600 | 85% |
| Werbung, Marketing | 7700 | 85% |
| Reise, Hotel, Flug | 7800 | 85% |
| Versicherung | 7900 | 85% |
| Software, Lizenz | 8400 | 85% |
| Beratung, Service | 8400 | 85% |

### Lernendes System

```python
from datev_export_v2 import SmartAccountSuggestor

suggestor = SmartAccountSuggestor()

# System lernt aus manuellen Zuordnungen
suggestor.learn("SEO Optimierung", 7700)  # Werbung
suggestor.learn("Cloud Hosting", 8400)     # Erlös

# Ab jetzt werden diese Texte korrekt zugeordnet
```

## Integration

### Mit GoBD-Rechnungsvalidator
```python
from gobd_validator_v2 import GoBDValidator
from datev_export_v2 import DATEVExporter

# Rechnung validieren und exportieren
validator = GoBDValidator()
result = validator.validate("rechnung.pdf")

if result.is_valid:
    exporter = DATEVExporter(smart_suggest=True)
    
    # Smarte Zuordnung basierend auf extrahiertem Text
    data = result.extracted_data
    exporter.add_rechnung_smart(
        datum=data['rechnungsdatum'],
        brutto=float(data['gesamtbetrag'].replace('.', '').replace(',', '.')),
        text=data['lieferant_name'] or "Rechnung"
    )
    
    exporter.export("datev.csv")
```

### Mit ZUGFeRD-Generator
```python
from zugferd_generator import ZUGFeRDGenerator, Invoice
from datev_export_v2 import DATEVExporter

# ZUGFeRD → DATEV
invoice = Invoice(...)
generator = ZUGFeRDGenerator()

exporter = DATEVExporter()
exporter.add_rechnung(
    datum=invoice.invoice_date,
    brutto=invoice.total,
    ust_satz=19,
    konto=8400,
    gegenkonto=1400,
    text=f"Rechnung {invoice.invoice_number}"
)

exporter.export("datev.csv")
```

## Validierung

```python
from datev_export_v2 import DATEVExporter

exporter = DATEVExporter()
# ... Buchungen hinzufügen ...

validation = exporter.validate()
if not validation['valid']:
    print("Fehler:", validation['errors'])
    print("Warnungen:", validation['warnings'])
```

## Preisgestaltung

| Plan | Preis | Features |
|------|-------|----------|
| **Basic** | 29€/Monat | 500 Buchungen, Export |
| **Professional** | 79€/Monat | 5.000 Buchungen, Smart-Suggest, API |
| **Enterprise** | 199€/Monat | Unlimited, ML-Learning, Support |

## Changelog

### v2.0.0 (2025-02-25)
- 🆕 Smarte Kontenvorschläge (ML-basiert)
- 🆕 Lernendes System
- 🆕 Automatische USt-Aufteilung
- 🆕 Validierung
- 🆕 Statistiken

### v1.0.0
- Initiale Version
- CSV-Export
- SKR03/SKR04 Unterstützung

## Roadmap

- [ ] SEPA-XML Export
- [ ] Zahlungsabgleich (offene Posten)
- [ ] DATEV-Online API-Integration
- [ ] Web-Interface
- [ ] REST API
