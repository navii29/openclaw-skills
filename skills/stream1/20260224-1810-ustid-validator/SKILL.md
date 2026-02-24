# USt-IdNr Validator

Deutsche USt-IdNr Validierung gegen das BZSt (Bundeszentralamt für Steuern). Offizieller Webservice für E-Commerce Automation.

**Version:** 1.0.0 | **Preis:** 49 EUR | **Quelle:** BZSt-offiziell

## Features

- ✅ **BZSt-Validierung** - Offizielle Prüfung gegen Bundeszentralamt für Steuern
- ✅ **Format-Check** - DE + EU USt-IdNr Format-Validierung
- ✅ **Qualifizierte Prüfung** - Mit eigener USt-IdNr, Firmenname, Ort, PLZ
- ✅ **GoBD-konform** - Dokumentationspflichtige Prüfungen
- ✅ **EU-Support** - Alle EU-USt-IdNr Formate (DE nur online)
- ✅ **CLI + Python API** - Flexibel einsetzbar

## Quick Start

```python
from ustid_validator import validate_ustid

# Schnell-Validierung
result = validate_ustid("DE123456789")
print(result['valid'])  # True/False

# Qualifizierte Prüfung (mit Bestätigung)
result = validate_ustid(
    "DE123456789",
    eigen_ustid="DE987654321",
    firma="Muster GmbH",
    ort="Berlin",
    plz="10115"
)
```

## CLI Usage

```bash
# Einfache Validierung
python ustid_validator.py DE123456789

# Mit eigener USt-IdNr
python ustid_validator.py DE123456789 DE987654321
```

## Rückgabewerte

| Feld | Beschreibung |
|------|--------------|
| `valid` | True/False/None |
| `ustid` | Formatierter Wert |
| `status` | Status-Code (200=OK) |
| `error_code` | BZSt-Fehlercode |
| `error_message` | Beschreibung |
| `datum` | Prüfdatum |
| `uhrzeit` | Prüfzeit |

## BZSt Status-Codes

| Code | Bedeutung |
|------|-----------|
| 200 | ✅ USt-IdNr ist gültig |
| 201 | ❌ USt-IdNr ist ungültig |
| 202 | ⚠️ Nicht registriert |
| 203/204 | ⚠️ Prüfung nicht möglich |
| 216 | ✅ Gültig (mit Abweichung) |
| 217 | ✅ Gültig (ohne Abgleich) |

## Use Cases

### 1. E-Commerce B2B-Validierung
Automatische Prüfung bei Geschäftskunden-Bestellungen für steuerfreie Lieferungen.

### 2. Buchhaltungs-Integration
Validierung vor Rechnungsstellung an Unternehmenskunden.

### 3. Kunden-Onboarding
Überprüfung neuer Geschäftskunden im CRM-System.

## Installation

```bash
pip install -r requirements.txt
```

## Lizenz

MIT - Frei für kommerzielle Nutzung

## Weiterführende Links

- [BZSt USt-IdNr Prüfung](https://www.bzst.de/DE/Unternehmen/USt_und_Rechnungen/UST_ID_Nr/UST_ID_Nr_Validierung/ust_id_nr_validierung_node.html)
