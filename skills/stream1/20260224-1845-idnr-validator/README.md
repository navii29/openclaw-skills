# 🆔 Steuer-Identifikationsnummer (IdNr) Validator

Validiert die 11-stellige deutsche Steuer-ID mit Format- und Prüfziffer-Prüfung.

## 🎯 Use Cases

- **ELSTER**: Validierung vor Online-Steuererklärung
- **Personalwesen**: Überprüfung von Mitarbeiter-Steuer-IDs
- **Lohnabrechnung**: Automatische Plausibilitätsprüfung
- **Kunden-Onboarding**: Validierung in Formularen

## 📋 IdNr Format

| Eigenschaft | Beschreibung |
|-------------|--------------|
| **Länge** | Genau 11 Ziffern |
| **Erste Ziffer** | 1-9 (keine 0) |
| **Besonderheit** | Keine doppelten aufeinanderfolgenden Ziffern |
| **Prüfziffer** | Letzte Stelle (Modulo 11) |
| **Format** | ZZZ ZZZ ZZZ ZZ |

## 📦 Installation

```bash
# Keine externen Dependencies
python3 idnr_validator.py 12345678901
```

## 🚀 Quick Start

### Als Python-Modul

```python
from idnr_validator import validate_idnr, IdNrValidator

# Schnell-Validierung
result = validate_idnr("12345678901")
print(result['gueltig'])  # True/False
print(result['pruefziffer_korrekt'])  # True/False/None

# Mit Validator-Objekt
validator = IdNrValidator()
result = validator.validate("12345678901")

# Nur Format prüfen (ohne Prüfziffer)
result = validator.validate("12345678901", strict=False)

# Maskieren für Logs
masked = validator.mask_idnr("12345678901")
print(masked)  # "12345*****1"
```

### CLI Usage

```bash
# Vollständige Validierung (mit Prüfziffer)
python idnr_validator.py 12345678901

# Mit Leerzeichen
python idnr_validator.py "12 345 678 901"

# Nur Format prüfen
python idnr_validator.py 12345678901 --lenient
```

## 📊 Rückgabewerte

```python
{
    'gueltig': True,              # Gesamtergebnis
    'idnr': '12345678901',        # Formatierter Wert
    'format_korrekt': True,       # Format-Check
    'pruefziffer_korrekt': True,  # Prüfziffer-Check
    'fehler': []                  # Fehlerliste
}
```

## 🔢 Prüfziffer-Algorithmus

```
Beispiel: 12345678901

1. Multiplikation mit Position:
   1×1 + 2×2 + 3×3 + ... + 0×10
   = 1 + 4 + 9 + 16 + 25 + 36 + 49 + 64 + 81 + 0
   = 285

2. Modulo 11:
   285 % 11 = 10

3. Prüfziffer:
   10 → 0 (Sonderfall)
   
   Prüfziffer = 0 ✓
```

## ⚡ Automation-Ready

### ELSTER-Integration

```python
def submit_tax_form(steuer_id, data):
    validator = IdNrValidator()
    result = validator.validate(steuer_id)
    
    if not result.gueltig:
        raise ValueError(f"Ungültige Steuer-ID: {result.fehler}")
    
    # ELSTER-API Call
    elster.submit(
        steuer_id=result.idnr,
        ...
    )
```

### HR-Onboarding

```python
def onboard_employee(employee_data):
    validator = IdNrValidator()
    
    # IdNr validieren
    result = validator.validate(employee_data['tax_id'])
    if not result.gueltig:
        return {
            'status': 'ERROR',
            'field': 'tax_id',
            'errors': result.fehler
        }
    
    # Maskiert speichern (für Logs)
    employee_data['tax_id_masked'] = validator.mask_idnr(result.idnr)
    
    return {'status': 'OK'}
```

### Formular-Validierung

```python
# JavaScript-ähnliche Frontend-Validierung
def validate_tax_id_input(input_value):
    validator = IdNrValidator()
    
    # Format-Check (schnell, kein Backend nötig)
    format_ok, formatted, errors = validator.validate_format(input_value)
    
    return {
        'valid': format_ok,
        'formatted': formatted,
        'errors': errors
    }
```

## 📝 Beispiele

| Eingabe | Format | Prüfziffer | Ergebnis |
|---------|--------|------------|----------|
| 12 345 678 901 | ✅ | Prüfung | Abhängig |
| 12345678901 | ✅ | Prüfung | Abhängig |
| 02345678901 | ❌ | - | Erste Ziffer = 0 |
| 11234567890 | ❌ | - | Doppelte 1 |
| 1234567890 | ❌ | - | Zu kurz (10) |
| 123456789012 | ❌ | - | Zu lang (12) |

## 🔒 Datenschutz

### Maskierung

```python
validator = IdNrValidator()

# Vollständige IdNr (nur intern verwenden!)
full_id = "12345678901"

# Maskiert für Logs, Anzeigen, etc.
masked = validator.mask_idnr(full_id)
print(masked)  # "12345*****1"
```

### Best Practices

- IdNr **niemals** unverschlüsselt speichern
- In Logs immer maskieren
- SSL/TLS für Übertragung verwenden
- DSGVO-konforme Verarbeitung dokumentieren

## 🔗 Weiterführende Links

- [Bundeszentralamt für Steuern - IdNr](https://www.bzst.de/DE/Steuern_National/Steuerliche_Identifikationsnummer/steuerliche_identifikationsnummer_node.html)
- [Wikipedia - Steueridentifikationsnummer](https://de.wikipedia.org/wiki/Steueridentifikationsnummer)
- [ELSTER](https://www.elster.de/)

## ⚠️ Wichtige Hinweise

- Jeder Bürger hat **genau eine** IdNr (lebenslang)
- IdNr wird bei Geburt oder Erstveranlagung vergeben
- Ersatz bei Verlust nicht möglich
- IdNr **≠** Steuernummer (die ist vom Finanzamt!)
- Prüfziffer-Algorithmus ist öffentlich bekannt
