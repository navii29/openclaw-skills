# Rechnungs-Matching

Automatisches Matching von Zahlungen zu offenen Rechnungen für DATEV.

## Features

✅ **Exaktes Matching** (Rechnungsnummer + Betrag)  
✅ **Fuzzy Matching** (Betrags-Toleranz)  
✅ **Teilzahlungen** erkennen  
✅ **Doppelte Zahlungen** erkennen  
✅ **DATEV-Export**  
✅ **31 Unit Tests**  

## Schnellstart

```python
from invoice_matching import InvoiceMatcher

matcher = InvoiceMatcher(toleranz_prozent=1.0)

# Rechnungen laden
matcher.lade_rechnungen([
    {'nr': 'RE-001', 'kunde_id': 'K001', 'betrag': 1190.00, 'datum': '2024-01-01'},
])

# Zahlungen laden
matcher.lade_zahlungen([
    {'datum': '2024-01-15', 'betrag': 1190.00, 'zweck': 'Rechnung RE-001'},
])

# Matching
ergebnis = matcher.match()
print(f"{ergebnis['stats']['match_rate']*100:.0f}% gematcht")
```

## Tests

```bash
pytest tests/test_invoice_matching.py -v
```

## Demo

```bash
python3 demo.py
```

## Lizenz

MIT
