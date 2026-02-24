# DATEV Validator

DATEV-Format Prüfung für Buchhaltungs-Daten.

**Version:** 1.0.0 | **Preis:** 59 EUR

## Features

- ✅ **Buchungsstapel** - Format-Validierung
- ✅ **Kontenrahmen** - SKR03/SKR04
- ✅ **Belegdaten** - Pflichtfelder
- ✅ **CSV/TXT** - DATEV-Standard

## Quick Start

```python
from datev_validator import validate_datev
result = validate_datev("buchungen.csv")
print(result['valid'])  # True/False
```

## Unterstützte Formate

- Buchungsstapel (CSV)
- Debitoren/Kreditoren
- Kontenbeschriftungen

## Use Cases

1. **Buchhaltung** - Daten-Export prüfen
2. **Steuerberater** - DATEV-Schnittstelle
3. **Migration** - Format-Konvertierung

## Lizenz

MIT
