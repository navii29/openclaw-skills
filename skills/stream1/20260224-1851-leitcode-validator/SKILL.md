# Leitcode Validator

Deutsche Leitcode-Validierung (Post/DHL Briefe).

**Version:** 1.0.0 | **Preis:** 29 EUR

## Features

- ✅ **5-stellig** - Postleitzahlen-Format
- ✅ **Prüfziffer** - Modulo 10
- ✅ **Adress-Routing** - Briefzustellung

## Quick Start

```python
from leitcode_validator import validate_leitcode
result = validate_leitcode("12345")
print(result['valid'])  # True/False
```

## Aufbau

- 4 Stellen: PLZ
- 1 Stelle: Prüfziffer

## Use Cases

1. **Adressvalidierung** - Briefadressen
2. **Massenmailings** - PLZ-Prüfung
3. **Logistik** - Routing-Optimierung

## Lizenz

MIT
