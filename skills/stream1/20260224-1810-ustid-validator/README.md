# 🇩🇪 Deutsche USt-IdNr Validierung

Validiert USt-IdNr gegen das BZSt (Bundeszentralamt für Steuern) - offizieller Webservice für E-Commerce Automation.

## 🎯 Use Cases

- **E-Commerce Shops**: Automatische Validierung bei B2B-Bestellungen
- **Buchhaltung**: Prüfung vor Rechnungsstellung
- **Onboarding**: Validierung neuer Geschäftskunden
- **Compliance**: GoBD-konforme Dokumentation

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### Als Python-Modul

```python
from ustid_validator import validate_ustid, UStIdValidator

# Schnell-Validierung
result = validate_ustid("DE123456789")
print(result)

# Mit eigener USt-IdNr (qualifizierte Prüfung)
result = validate_ustid(
    "DE123456789",
    eigen_ustid="DE987654321",
    firma="Muster GmbH",
    ort="Berlin",
    plz="10115"
)
```

### CLI Usage

```bash
# Format-Check + Online-Validierung
python ustid_validator.py DE123456789

# Mit eigener USt-IdNr
python ustid_validator.py DE123456789 DE987654321
```

## 📊 Rückgabewerte

```python
{
    'valid': True,           # True/False/None
    'ustid': 'DE123456789',  # Formatierter Wert
    'status': 'VALID',       # Status-Code
    'error_code': None,      # BZSt-Fehlercode
    'error_message': None,   # Beschreibung
    'datum': '20260224',     # Prüfdatum
    'uhrzeit': '181005'      # Prüfzeit
}
```

## 🔢 BZSt Status-Codes

| Code | Bedeutung |
|------|-----------|
| 200 | ✅ USt-IdNr ist gültig |
| 201 | ❌ USt-IdNr ist ungültig |
| 202 | ⚠️ Nicht registriert |
| 203/204 | ⚠️ Prüfung nicht möglich |
| 216 | ✅ Gültig (mit Adressabweichung) |
| 217 | ✅ Gültig (ohne Abgleich) |

## 🌍 EU-USt-IdNr Support

EU-USt-IdNr (außer DE) werden formatiert, aber nicht online geprüft (nationale Stellen zuständig):

```python
result = validate_ustid("ATU12345678")
# {'format_check': True, 'online_check': False, 'status': 'EU_FORMAT_VALID'}
```

## ⚡ Automation-Ready

```python
# In deinem E-Commerce Workflow
def process_b2b_order(order):
    if order.get('is_business'):
        result = validate_ustid(order['ustid'])
        if result['valid']:
            order['ust_validated'] = True
            order['ust_validation_date'] = result['datum']
        else:
            raise ValueError(f"Ungültige USt-IdNr: {result.get('error_message')}")
```

## 📝 Lizenz

MIT - Frei für kommerzielle Nutzung

## 🔗 Weiterführende Links

- [BZSt USt-IdNr Prüfung](https://www.bzst.de/DE/Unternehmen/USt_und_Rechnungen/UST_ID_Nr/UST_ID_Nr_Validierung/ust_id_nr_validierung_node.html)
- [GoBD Richtlinien](https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Weitere_Steuerthemen/Abgabenordnung/2022-11-14-Gobd-nichtveranlagung.html)
