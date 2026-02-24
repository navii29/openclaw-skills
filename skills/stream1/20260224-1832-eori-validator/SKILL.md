# EORI Validator

EORI-Nummer Validierung für Zoll und Import/Export. Unterstützt EU-Länder + GB.

**Version:** 1.0.0 | **Preis:** 49 EUR

## Features

- ✅ **Format-Validierung** - Alle EU-EORI-Formate
- ✅ **Prüfziffer-Check** - Für deutsche EORI
- ✅ **Online-Validierung** - EU-Webservices
- ✅ **GB-Support** - Brexit-EORI

## Quick Start

```python
from eori_validator import validate_eori
result = validate_eori("DE123456789")
print(result['valid'])  # True/False
```

## CLI

```bash
python eori_validator.py DE123456789 --online
```

## Use Cases

1. **Import/Export**: Zollanmeldungen validieren
2. **E-Commerce**: Brexit-Geschäfte (GB-EORI)
3. **Supplier Onboarding**: Zoll-Nummern prüfen

## Status-Codes

| Code | Bedeutung |
|------|-----------|
| VALID | ✅ Gültig |
| INVALID_FORMAT | ❌ Format ungültig |
| INVALID_CHECK | ❌ Prüfziffer falsch |

## Lizenz

MIT
