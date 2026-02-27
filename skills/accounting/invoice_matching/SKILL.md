# Rechnungs-Matching

**Version:** 1.0.0  
**Domain:** German Accounting / Offene Posten / Zahlungszuordnung  
**Status:** Production Ready

---

## Übersicht

Automatisches Matching von Zahlungen zu offenen Rechnungen. Optimiert für DATEV-Export und deutsche Buchhaltungsstandards.

### Unterstützte Matching-Methoden

| Methode | Beschreibung | Genauigkeit |
|---------|-------------|-------------|
| **Exakt** | Betrag + Referenz | 100% |
| **Fuzzy** | Betrag ± Toleranz | ~95% |
| **Teilzahlung** | Teilbetrag auf Rechnung | Manuell |
| **Mehrfach** | Zahlung auf mehrere Rechnungen | Manuell |

---

## Use Cases

### UC1: Automatisches Matching aus Bankdaten
**Als** Buchhalter  
**möchte ich** CSV-Bankdaten automatisch zu Rechnungen matchen  
**damit** ich Zeit bei der Zuordnung spare.

**Input:**
- Offene Rechnungen (CSV/JSON)
- Bankumsätze (CSV)

**Output:**
- Gematchte Paare
- Unmatched Items
- DATEV-CSV Export

---

### UC2: Teilzahlungen erkennen
**Als** Buchhalter  
**möchte ich** Teilzahlungen auf Rechnungen erkennen  
**damit** ich den Zahlungsstand verfolgen kann.

---

### UC3: Doppelte Zahlungen verhindern
**Als** Prüfer  
**möchte ich** doppelte Zahlungen erkennen  
**damit** keine Fehlbuchungen entstehen.

---

### UC4: DATEV-konformer Export
**Als** Steuerberater  
**möchte ich** DATEV-konforme CSV-Dateien exportieren  
**damit** die Daten direkt ins Kanzlei-System importiert werden können.

---

## API

```python
from invoice_matching import InvoiceMatcher, DATEVExporter

# Matcher initialisieren
matcher = InvoiceMatcher(
    toleranz_prozent=1.0,  # 1% Toleranz
    toleranz_absolut=5.0   # ±5 EUR
)

# Rechnungen laden
matcher.lade_rechnungen([
    {'nr': 'RE-001', 'betrag': 1190.00, 'kunde': 'K001'},
    {'nr': 'RE-002', 'betrag': 595.00, 'kunde': 'K002'},
])

# Zahlungen laden
matcher.lade_zahlungen([
    {'datum': '2024-01-15', 'betrag': 1190.00, 'referenz': 'RE-001'},
    {'datum': '2024-01-20', 'betrag': 595.00, 'referenz': 'RE-002'},
])

# Matching durchführen
ergebnis = matcher.match()

# Exportieren
exporter = DATEVExporter()
exporter.export_csv(ergebnis, 'buchungen.csv')
```

---

## CSV-Formate

### Offene Posten (Input)
```csv
Rechnungsnr;Kundennummer;Betrag;Datum;Faellig;Waehrung
RE-001;K001;1190.00;2024-01-01;2024-01-31;EUR
RE-002;K002;595.00;2024-01-05;2024-02-05;EUR
```

### Bankumsätze (Input)
```csv
Datum;Betrag;Zweck;Referenz
2024-01-15;1190.00;Rechnung RE-001;K001-20240115
2024-01-20;595.00;Zahlung fuer RE-002;K002-20240120
```

### DATEV Export (Output)
```csv
Datum;Konto;Gegenkonto;Buchungstext;Umsatz;Belegnr
15.01.2024;1200;8400;RE-001 K001;1190,00;RE-001
```

---

## Fehlerbehandlung

| Exception | Auslöser |
|-----------|----------|
| `MatchingError` | Allgemeiner Matching-Fehler |
| `DuplicatePaymentError` | Doppelte Zahlung erkannt |
| `InvalidFormatError` | Ungültiges CSV-Format |
| `ToleranzUeberschrittenError` | Betrag außerhalb Toleranz |

---

## Installation

```bash
pip install pandas
```

---

## DATEV-Referenz

- **Kontenrahmen:** SKR03 / SKR04
- **Buchungsschlüssel:** Standard für Automatikkonten
- **CSV-Format:** DATEV Standard Format

---

## Lizenz

MIT - Für den professionellen Einsatz in der deutschen Buchhaltung.
