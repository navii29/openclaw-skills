# 💰 German VAT (USt) Calculator

Berechnet Umsatzsteuer für die deutschen Steuersätze (19%, 7%, 0%).

## 🎯 Use Cases

- **E-Commerce**: Preisberechnung im Checkout
- **Rechnungsstellung**: USt-Berechnung für Rechnungen
- **Buchhaltung**: Brutto/Netto-Umrechnung
- **Skonto/Rabatt**: Zahlungskonditionen berechnen

## 📋 Deutsche USt-Sätze

| Satz | Prozent | Anwendung |
|------|---------|-----------|
| **Regelsatz** | 19% | Standard (Produkte, Dienstleistungen) |
| **Ermäßigt** | 7% | Lebensmittel, Bücher, Kultur |
| **Nullsatz** | 0% | Export, innergemeinschaftlich |

## 📦 Installation

```bash
# Keine externen Dependencies
python3 ust_calculator.py netto-zu-brutto 100
```

## 🚀 Quick Start

### Als Python-Modul

```python
from ust_calculator import UStCalculator, calculate_vat

# Calculator erstellen
calc = UStCalculator()

# Netto zu Brutto
result = calc.netto_zu_brutto(100.0, 19.0)
print(result.brutto)      # 119.0
print(result.ust_betrag)  # 19.0

# Brutto zu Netto
result = calc.brutto_zu_netto(119.0, 19.0)
print(result.netto)       # 100.0

# Schnell-Berechnung
result = calculate_vat(net_amount=100, vat_rate=19)
print(result['brutto'])   # 119
```

### CLI Usage

```bash
# Netto zu Brutto (19%)
python ust_calculator.py netto-zu-brutto 100

# Netto zu Brutto (7%)
python ust_calculator.py netto-zu-brutto 100 7

# Brutto zu Netto
python ust_calculator.py brutto-zu-netto 119

# Skonto berechnen (2% Skonto auf 119€)
python ust_calculator.py skonto 119 2

# Rabatt berechnen (10% Rabatt)
python ust_calculator.py rabatt 100 10

# Rechnungsposition
python ust_calculator.py position 5 19.99
```

## 📊 Berechnungsbeispiele

### Netto → Brutto
```
Netto:      100,00 €
+ 19% USt:   19,00 €
────────────────────
Brutto:     119,00 €
```

### Brutto → Netto
```
Brutto:     119,00 €
- 19% USt:   19,00 €
────────────────────
Netto:      100,00 €
```

### Skonto-Berechnung
```
Bruttobetrag:     119,00 €
- 2% Skonto:       -2,38 €
──────────────────────────
Zahlungsbetrag:   116,62 €
```

### Rabatt (B2B)
```
Original Netto:      100,00 €
- 10% Rabatt:        -10,00 €
─────────────────────────────
Netto nach Rabatt:    90,00 €
+ 19% USt:            17,10 €
─────────────────────────────
Brutto:              107,10 €
```

## 📊 Rückgabewerte

```python
UStBerechnung(
    netto=100.0,
    steuersatz=19.0,
    ust_betrag=19.0,
    brutto=119.0,
    steuerkategorie='Regelsatz'
)
```

## ⚡ Automation-Ready

### E-Commerce Checkout

```python
def calculate_cart_total(items):
    calc = UStCalculator()
    
    total_net = 0
    total_vat = 0
    
    for item in items:
        vat_rate = calc.get_steuer_satz_fuer_produkt(item.category)
        result = calc.netto_zu_brutto(item.price_net, vat_rate)
        
        total_net += result.netto * item.quantity
        total_vat += result.ust_betrag * item.quantity
    
    return {
        'net': round(total_net, 2),
        'vat': round(total_vat, 2),
        'gross': round(total_net + total_vat, 2)
    }
```

### Rechnung erstellen

```python
def create_invoice_line(quantity, unit_price_net, category='standard'):
    calc = UStCalculator()
    
    vat_rate = calc.get_steuer_satz_fuer_produkt(category)
    result = calc.rechnungsposition(quantity, unit_price_net, vat_rate)
    
    return {
        'quantity': result['menge'],
        'unit_price': result['einzelpreis_netto'],
        'net_total': result['gesamt_netto'],
        'vat_rate': result['steuersatz'],
        'vat_amount': result['ust_betrag'],
        'gross_total': result['gesamt_brutto']
    }
```

### Skonto-Workflow

```python
def apply_payment_terms(invoice_gross, skonto_percent=2.0):
    calc = UStCalculator()
    
    result = calc.skonto_berechnen(invoice_gross, skonto_percent)
    
    return {
        'original_amount': result['brutto'],
        'discount_percent': result['skonto_prozent'],
        'discount_amount': result['skonto_betrag'],
        'payment_amount': result['zahlungsbetrag'],
        'due_date': calculate_due_date(days=14)
    }
```

## 📝 Produktkategorien

| Kategorie | Steuersatz |
|-----------|------------|
| `standard` | 19% |
| `lebensmittel` | 7% |
| `buecher` | 7% |
| `zeitungen` | 7% |
| `kultur` | 7% |
| `medizin` | 7% |
| `steuerfrei` | 0% |
| `export` | 0% |

## 🔗 Weiterführende Links

- [UStG §12 Steuersätze](https://www.gesetze-im-internet.de/ustg_1980/__12.html)
- [BMF USt](https://www.bundesfinanzministerium.de/Content/DE/Standardartikel/Themen/Steuern/Steuerarten/Umsatzsteuer.html)
- [DATEV USt](https://www.datev.de/web/de/mam/top-themen/umsatzsteuer/)

## ⚠️ Wichtige Hinweise

- **Rundung**: Standardmäßig 2 Nachkommastellen
- **Brutto→Netto**: Division durch (1 + Satz/100)
- **Skonto**: Wird auf Brutto berechnet
- **Rabatt**: Wird auf Netto berechnet (B2B-Standard)
- **Steuersatz-Änderungen**: Prüfen Sie aktuelle Sätze
