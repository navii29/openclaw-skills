# 🧾 GoBD-konforme Rechnungsnummern

Lückenlose, fortlaufende Rechnungsnummer-Generierung nach GoBD (Grundsätze zur ordnungsmäßigen Führung und Aufbewahrung von Büchern).

## 🎯 Use Cases

- **E-Commerce**: Automatische Rechnungsnummern bei Bestellungen
- **Buchhaltung**: GoBD-konforme Nummernvergabe
- **DATEV-Export**: Kompatibel mit DATEV-Formaten
- **Steuerprüfung**: Lückenlose Nachweiskette

## 📋 GoBD-Anforderungen

| Anforderung | Umsetzung |
|-------------|-----------|
| **Fortlaufend** | ✅ Automatische Inkrementierung |
| **Eindeutig** | ✅ Keine Doppelvergabe möglich |
| **Chronologisch** | ✅ Mit Zeitstempel |
| **Nicht manipulierbar** | ✅ Persistente Speicherung |
| **Lückenlos** | ✅ Prüffunktion für Lücken |

## 📦 Installation

```bash
# Keine externen Dependencies
python3 rechnungsnummer_gobd.py generate RE
```

## 🚀 Quick Start

### Als Python-Modul

```python
from rechnungsnummer_gobd import GoBDRechnungsnummer, RechnungsnummerConfig

# Standard-Schema: RE-2025-00001
config = RechnungsnummerConfig(prefix="RE", jahr_format="YYYY", ziffern=5)
generator = GoBDRechnungsnummer(config)

nummer = generator.generiere()
print(nummer)  # RE-2025-00001
nummer = generator.generiere()
print(nummer)  # RE-2025-00002
```

### CLI Usage

```bash
# Neue Rechnungsnummer generieren
python rechnungsnummer_gobd.py generate RE
# Ausgabe: RE-2025-00001

# Rechnungsnummer validieren
python rechnungsnummer_gobd.py validate RE-2025-00001

# Statistiken anzeigen
python rechnungsnummer_gobd.py stats

# Auf Lücken prüfen
python rechnungsnummer_gobd.py check
```

## 📊 Nummern-Schemata

### Schema 1: Mit Jahr (Standard)
```python
config = RechnungsnummerConfig(
    prefix="RE",
    jahr_format="YYYY",  # oder "YY"
    trennzeichen="-",
    ziffern=5
)
# Ergebnis: RE-2025-00001, RE-2025-00002, ...
```

### Schema 2: Ohne Jahr
```python
config = RechnungsnummerConfig(
    prefix="INV",
    jahr_format="",
    ziffern=6
)
# Ergebnis: INV-000001, INV-000002, ...
```

### Schema 3: Kundenspezifisch
```python
config = RechnungsnummerConfig(
    prefix="K2025",
    jahr_format="",
    trennzeichen=".",
    ziffern=4
)
# Ergebnis: K2025.0001, K2025.0002, ...
```

## ⚡ Automation-Ready

### E-Commerce Integration

```python
def create_invoice(order):
    generator = GoBDRechnungsnummer(config)
    
    # Rechnungsnummer generieren
    rechnungsnummer = generator.generiere()
    
    # Rechnung erstellen
    invoice = {
        'nummer': rechnungsnummer,
        'datum': datetime.now(),
        'kunde': order.customer,
        'betrag': order.total
    }
    
    return invoice
```

### Lücken-Prüfung (für Steuerprüfung)

```python
generator = GoBDRechnungsnummer()
luecken = generator.pruefe_luecken()

if luecken:
    alert_accountant(f"Lücken in Rechnungsnummern: {luecken}")
```

### GoBD-Export

```python
# Export für Steuerprüfer
generator.export_vergabe_liste("rechnungsnummern_2025.csv")
# Erstellt: Rechnungsnummer;Datum;Timestamp
```

## 📊 Speicherung

```json
{
  "schema": {
    "prefix": "RE",
    "jahr_format": "YYYY",
    "trennzeichen": "-",
    "ziffern": 5,
    "start_nummer": 1
  },
  "jahr": 2025,
  "letzte_nummer": 42,
  "ausgegebene_nummern": [
    {
      "nummer": "RE-2025-00001",
      "datum": "2025-02-24T10:30:00",
      "timestamp": "2025-02-24T10:30:05.123456"
    }
  ]
}
```

## 🔒 GoBD-Compliance

### Nachweiskette
- ✅ Zeitstempel bei jeder Nummernvergabe
- ✅ Persistente JSON-Speicherung
- ✅ Exportfunktion für Prüfer
- ✅ Lückenprüfung

### Empfohlene Praxis
```python
# 1. Nummer generieren
nummer = generator.generiere()

# 2. Sofort Rechnung erstellen (nicht speichern ohne Rechnung!)
rechnung = create_invoice(nummer, ...)

# 3. Rechnung versenden
send_invoice(rechnung)

# 4. Periodisch Lücken prüfen
luecken = generator.pruefe_luecken()
```

## 🔗 Weiterführende Links

- [GoBD (BMF)](https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Weitere_Steuerthemen/Abgabenordnung/2022-11-14-Gobd-nichtveranlagung.html)
- [§14 UStG (Rechnungsmerkmale)](https://www.gesetze-im-internet.de/ustg_1980/__14.html)
- [DATEV-Format](https://www.datev.de/web/de/datev-shop/materialien/rechnungsmerkmale/)

## ⚠️ Wichtige Hinweise

- Rechnungsnummern dürfen **nicht gelöscht** werden
- **Stornorechnungen** mit eigenem Schema (z.B. ST-2025-00001)
- **Jahreswechsel**: Optional Counter zurücksetzen
- **Backup** der Counter-Datei empfohlen
