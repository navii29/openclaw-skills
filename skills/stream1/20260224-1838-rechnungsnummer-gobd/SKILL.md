# Rechnungsnummer GoBD

GoBD-konforme Rechnungsnummern-Generierung und Prüfung.

**Version:** 1.0.0 | **Preis:** 39 EUR

## Features

- ✅ **Lückenlos** - Fortlaufende Nummern
- ✅ **Eindeutig** - Keine Dopplungen
- ✅ **GoBD-konform** - BMF Anforderungen
- ✅ **Persistenz** - JSON-Speicherung

## Quick Start

```python
from rechnungsnummer_gobd import generate_number
nummer = generate_number(prefix="RE-2024-")
print(nummer)  # RE-2024-000042
```

## GoBD Anforderungen

- Fortlaufend ✓
- Lückenlos ✓
- Eindeutig ✓
- Chronologisch ✓

## Use Cases

1. **Rechnungsstellung**: Automatische Nummern
2. **Buchhaltung**: GoBD-Konformität
3. **Steuerprüfung**: Nachweisbarkeit

## Lizenz

MIT
