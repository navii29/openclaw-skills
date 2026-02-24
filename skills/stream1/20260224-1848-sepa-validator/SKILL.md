# SEPA Validator

IBAN/BIC Validierung und SEPA-Daten-Prüfung.

**Version:** 1.0.0 | **Preis:** 49 EUR

## Features

- ✅ **IBAN-Check** - 77 Länder
- ✅ **BIC-Validierung** - SWIFT-Codes
- ✅ **Prüfziffer** - BBAN Berechnung
- ✅ **Länder-Info** - Bankdaten

## Quick Start

```python
from sepa_validator import validate_iban
result = validate_iban("DE89370400440532013000")
print(result['valid'])  # True/False
```

## Unterstützte Länder

- DE, AT, CH, NL, FR, IT, ES, BE, LU, etc. (77 Länder)

## Use Cases

1. **Zahlungsverkehr** - Überweisungen prüfen
2. **Onboarding** - Bankdaten validieren
3. **SEPA-Lastschrift** - Mandate prüfen

## Lizenz

MIT
