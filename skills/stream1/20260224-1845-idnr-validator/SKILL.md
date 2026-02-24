# IdNr Validator

Steuer-IdNr (Identifikationsnummer) Validierung für Deutschland.

**Version:** 1.0.0 | **Preis:** 39 EUR

## Features

- ✅ **Format-Check** - 11 Stellen, Ziffern
- ✅ **Prüfziffer** - Modulo 11 Berechnung
- ✅ **Sonderfälle** - Test-IdNr erkennen

## Quick Start

```python
from idnr_validator import validate_idnr
result = validate_idnr("12345678901")
print(result['valid'])  # True/False
```

## Aufbau

- 11 Ziffern
- Ziffer 1: Nie 0
- Ziffer 2-10: Prüfziffer-Berechnung
- Ziffer 11: Prüfziffer

## Use Cases

1. **Onboarding** - Kunden-Validierung
2. **Lohnabrechnung** - Mitarbeiter-Check
3. **Steuererklärung** - Formular-Validierung

## Lizenz

MIT
