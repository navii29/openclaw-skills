# XRechnung Validator

Validiert XRechnung XML gegen EN 16931 Standard (ZUGFeRD/Factur-X).

**Version:** 1.0.0 | **Preis:** 79 EUR

## Features

- ✅ **EN 16931** - EU-Norm konform
- ✅ **ZUGFeRD** - 2.1 + 2.2 Support
- ✅ **Factur-X** - Französischer Standard
- ✅ **B2G** - Behörden-Rechnungen

## Quick Start

```python
from xrechnung_validator import validate_xrechnung
result = validate_xrechnung("rechnung.xml")
print(result['valid'])  # True/False
```

## Standards

- XRechnung (CIUS)
- ZUGFeRD 2.1/2.2
- Factur-X
- EN 16931

## Use Cases

1. **B2G-Rechnungen** - Behörden
2. **E-Invoicing** - Großunternehmen
3. **Compliance** - Standard-Check

## Lizenz

MIT
