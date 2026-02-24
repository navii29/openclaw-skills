# 💶 SEPA IBAN/BIC Validator + Generator

Validiert und generiert IBAN/BIC für SEPA-Zahlungen in Europa.

## 🎯 Use Cases

- **E-Commerce**: Zahlungsvalidierung im Checkout
- **Buchhaltung**: IBAN-Prüfung vor Überweisungen
- **Onboarding**: Bankdaten-Validierung bei Kundenregistrierung
- **Migration**: Alte Kontonummern zu IBAN konvertieren

## 📋 Unterstützte Länder

| Land | Code | IBAN-Länge | Format |
|------|------|------------|--------|
| 🇩🇪 Deutschland | DE | 22 | DE00 1234 5678 9012 3456 78 |
| 🇦🇹 Österreich | AT | 20 | AT00 12345 01234567890 |
| 🇨🇭 Schweiz | CH | 21 | CH00 12345 6789012345678 |
| 🇳🇱 Niederlande | NL | 18 | NL00 BANK 0123 4567 89 |
| 🇫🇷 Frankreich | FR | 27 | FR00 12345 67890... |
| ... | ... | ... | ... |

**Insgesamt 32 europäische Länder**

## 📦 Installation

```bash
# Keine externen Dependencies
python3 sepa_validator.py validate-iban DE89370400440532013000
```

## 🚀 Quick Start

### Als Python-Modul

```python
from sepa_validator import validate_iban, validate_bic, create_german_iban

# IBAN validieren
result = validate_iban("DE89370400440532013000")
print(result['gueltig'])  # True/False
print(result['land'])     # Deutschland

# BIC validieren
result = validate_bic("COBADEFFXXX")
print(result['gueltig'])  # True/False
print(result['bankcode']) # COBA

# Deutsche IBAN aus BLZ/Konto erstellen
result = create_german_iban("37040044", "532013000")
print(result['iban'])      # DE89...
print(result['formatted']) # DE89 3704 0044 0532 0130 00
```

### CLI Usage

```bash
# IBAN validieren
python sepa_validator.py validate-iban DE89370400440532013000

# BIC validieren
python sepa_validator.py validate-bic COBADEFFXXX

# Deutsche IBAN erstellen
python sepa_validator.py create-iban 37040044 532013000

# IBAN formatieren
python sepa_validator.py format DE89370400440532013000
```

## 🔢 IBAN-Prüfziffer (Modulo 97-10)

```
Beispiel: DE89 3704 0044 0532 0130 00

1. Verschiebe erstes 4 Zeichen ans Ende:
   370400440532013000 DE89

2. Buchstaben → Zahlen (A=10, B=11, ...):
   370400440532013000 131489

3. Modulo 97:
   370400440532013000131489 % 97 = 1
   
   → Gültig wenn Rest = 1 ✅
```

## 📊 Rückgabewerte

### IBAN-Validierung
```python
{
    'gueltig': True,
    'iban': 'DE89370400440532013000',
    'land': 'Deutschland',
    'bankleitzahl': '37040044',
    'kontonummer': '0532013000',
    'sepa_faehig': True,
    'fehler': []
}
```

### BIC-Validierung
```python
{
    'gueltig': True,
    'bic': 'COBADEFFXXX',
    'bankcode': 'COBA',
    'laendercode': 'DE',
    'filiale': 'XXX',
    'fehler': []
}
```

## ⚡ Automation-Ready

### E-Commerce Checkout

```python
def process_payment(iban, bic=None):
    validator = SEPAValidator()
    
    # IBAN validieren
    result = validator.validate_iban(iban)
    if not result.gueltig:
        return {
            'status': 'ERROR',
            'field': 'iban',
            'errors': result.fehler
        }
    
    # BIC validieren (optional)
    if bic:
        bic_result = validator.validate_bic(bic)
        if not bic_result['gueltig']:
            return {
                'status': 'ERROR',
                'field': 'bic',
                'errors': bic_result['fehler']
            }
    
    # SEPA-Lastschrift erstellen
    return {
        'status': 'OK',
        'iban': result.iban,
        'formatted': validator.format_iban_readable(result.iban),
        'land': result.land
    }
```

### Bankdaten-Migration

```python
def migrate_to_iban(customers):
    validator = SEPAValidator()
    
    for customer in customers:
        if customer.get('blz') and customer.get('konto'):
            result = validator.german_to_iban(
                customer['blz'],
                customer['konto']
            )
            if result['gueltig']:
                customer['iban'] = result['iban']
                customer['iban_formatted'] = result['formatted']
```

### Formular-Validierung

```python
# Frontend-ähnliche Validierung
def validate_bank_input(iban_input):
    validator = SEPAValidator()
    
    # Format prüfen
    formatted = validator.format_iban(iban_input)
    
    # Ländervorwahl prüfen
    if len(formatted) >= 2:
        land = formatted[:2]
        if not validator.is_sepa_country(land):
            return {'valid': False, 'error': 'Land nicht im SEPA-Raum'}
    
    return {'valid': True, 'formatted': formatted}
```

## 📝 BIC Format

```
BKKLDEFFXXX
││││││└┴┴── Filiale (XXX = Hauptstelle)
││││└┴────── Ortscode (alphanumerisch)
││└┴──────── Ländercode (ISO 3166-1)
└┴────────── Bankcode (4 Buchstaben)

Beispiele:
- COBADEFFXXX: Commerzbank, Deutschland
- DEUTDEFFXXX: Deutsche Bank, Deutschland
- SOLADESTXXX: Sparkasse, Deutschland
```

## 🔗 Weiterführende Links

- [IBAN Registry (SWIFT)](https://www.swift.com/standards/data-standards/iban)
- [SEPA - ECB](https://www.ecb.europa.eu/paym/integration/retail/sepa/html/index.en.html)
- [Bundesbank BLZ-Suche](https://www.bundesbank.de/de/aufgaben/unbarer-zahlungsverkehr/serviceangebot/bankleitzahlen)
- [SEPA-Überweisung](https://www.bundesbank.de/de/aufgaben/unbarer-zahlungsverkehr/sepa-uberweisung)

## ⚠️ Wichtige Hinweise

- **IBAN allein reicht** für SEPA-Überweisungen (BIC optional seit 2016)
- **Prüfziffer** schützt vor Tippfehlern, nicht vor fiktiven Konten
- **Echte Konten** können trotz gültiger Prüfziffer nicht existieren
- **Test-IBANs**: Verwenden Sie echte Test-IBANs für Entwicklung
- **IBAN-Diskriminierung**: In EU ist reine IBAN-Angabe ausreichend
