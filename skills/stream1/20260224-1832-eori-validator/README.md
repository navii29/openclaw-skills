# 🛃 EORI-Nummer Validierung

Validiert EORI-Nummern (Economic Operators Registration and Identification) für E-Commerce Import/Export und Zoll-Automation.

## 🎯 Use Cases

- **Import/Export**: Validierung bei Zollanmeldungen
- **E-Commerce**: Prüfung Brexit-Geschäfte (GB-EORI)
- **Supplier Onboarding**: Zoll-Nummern-Validierung
- **Compliance**: Zollrechtliche Anforderungen

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### Als Python-Modul

```python
from eori_validator import validate_eori, EORIValidator

# Format-Validierung
result = validate_eori("DE123456789")
print(result)
# {'valid': True, 'eori': 'DE123456789', 'land': 'Deutschland'}

# Mit Online-Check (sofern verfügbar)
result = validate_eori("DE123456789", online=True)
```

### CLI Usage

```bash
# Format-Check
python eori_validator.py DE123456789

# Mit Online-Validierung
python eori_validator.py DE123456789 --online
```

## 🌍 Unterstützte Länderformate

| Land | Format | Beispiel |
|------|--------|----------|
| 🇩🇪 DE | DE + 9 Ziffern | DE123456789 |
| 🇦🇹 AT | ATU + 8 Ziffern | ATU12345678 |
| 🇧🇪 BE | BE0 + 9 Ziffern | BE0123456789 |
| 🇫🇷 FR | FR + 11 alphanumerisch | FR12345678901 |
| 🇮🇹 IT | IT + 11 Ziffern | IT12345678901 |
| 🇳🇱 NL | NL + 12 alphanumerisch | NL123456789B01 |
| 🇪🇸 ES | ES + Buchstabe + 8 Ziffern | ESA12345678 |
| 🇬🇧 GB | GB + 12-15 alphanumerisch | GB123456789000 |

## 🔢 Deutsche EORI-Validierung

Deutsche EORI-Nummern enthalten eine **Prüfziffer** (berechnet mit Modulo 11):

```python
validator = EORIValidator()
result = validator.validate_online("DE123456789")
# Prüft Format + Prüfziffer
```

### Prüfziffer-Berechnung

```
Zollnummer: D E 1 2 3 4 5 6 7 [8]
Gewichtung:   - - 3 1 2 1 2 1 2  1
Berechnung:   1*3 + 2*1 + 3*2 + 4*1 + 5*2 + 6*1 + 7*2 + 8*1 = 53
Prüfziffer:   53 % 11 = 9 (Rest)
```

## 📊 Rückgabewerte

```python
{
    'valid': True,              # True/False/None
    'eori': 'DE123456789',      # Formatierter Wert
    'status': 'VALID',          # Status-Code
    'land': 'Deutschland',      # Land
    'zollnummer': '123456789',  # Nur DE
    'pruefziffer_ok': True      # Nur DE
}
```

## ⚡ Automation-Ready

```python
def process_import_order(order):
    if order.get('eori'):
        result = validate_eori(order['eori'])
        if not result['valid']:
            raise ValueError(f"Ungültige EORI: {result.get('error')}")
        
        order['eori_validated'] = True
        order['eori_land'] = result['land']
```

## 📝 Hinweise

- Deutsche EORI-Nummern können auf [Zoll.de](https://www.zoll.de) beantragt werden
- GB-EORI nach Brexit separat erforderlich
- Online-Validierung nutzt EU-Webservices (Rate-Limits beachten)

## 🔗 Weiterführende Links

- [EU EORI-System](https://ec.europa.eu/taxation_customs/business/customs-procedures/import-export/registration-identification-eori_de)
- [BZSt EORI](https://www.bzst.de/DE/Unternehmen/Aussenwirtschaft/Zoll/EORI/eori_node.html)
- [Zoll EORI-Service](https://www.zoll.de/DE/Fachthemen/EORI/eori_node.html)
