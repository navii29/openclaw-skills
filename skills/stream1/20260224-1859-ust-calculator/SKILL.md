# USt Calculator

Deutsche Umsatzsteuer-Berechnung (19%, 7%, 0%).

**Version:** 1.0.0 | **Preis:** 29 EUR

## Features

- ✅ **Sätze** - 19%, 7%, 0%
- ✅ **Brutto/Netto** - Beide Richtungen
- ✅ **Rundung** - 2 Dezimalstellen
- ✅ **Mehrwert** - Differenzberechnung

## Quick Start

```python
from ust_calculator import calculate_ust
result = calculate_ust(netto=100, satz=19)
print(result['brutto'])  # 119.00
print(result['ust'])     # 19.00
```

## Steuersätze

- 19% - Regelsatz
- 7% - Ermäßigt
- 0% - Steuerfrei

## Use Cases

1. **Rechnungen** - USt-Berechnung
2. **Preislisten** - Brutto/Netto-Umrechnung
3. **Buchhaltung** - Steuer-Aufteilung

## Lizenz

MIT
