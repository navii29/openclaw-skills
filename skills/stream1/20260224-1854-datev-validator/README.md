# 📊 DATEV-Format Validator

Validiert DATEV-kompatible CSV/TXT Dateien für Buchhaltungsexporte.

## 🎯 Use Cases

- **Buchhaltung**: Validierung vor DATEV-Import
- **E-Commerce**: Automatische DATEV-Export-Prüfung
- **Steuerberater**: Fehlererkennung in Buchungsstapeln
- **Datenmigration**: Qualitätsprüfung bei Übernahmen

## 📋 Unterstützte Formate

| Format | Beschreibung | Verwendung |
|--------|--------------|------------|
| **BUCHUNGSSTAPEL** | Standardbuchungen | Tägliche Buchungen |
| **DEBITOREN** | Debitoren-Stammdaten | Kundenverwaltung |
| **KREDITOREN** | Kreditoren-Stammdaten | Lieferantenverwaltung |

## 📦 Installation

```bash
# Keine externen Dependencies
python3 datev_validator.py validate buchungen.csv
```

## 🚀 Quick Start

### Als Python-Modul

```python
from datev_validator import validate_datev, DATEVValidator

# CSV validieren
with open('export.csv', 'r') as f:
    result = validate_datev(f.read())

print(result['gueltig'])  # True/False
print(result['format'])   # BUCHUNGSSTAPEL
print(result['fehler'])   # Liste der Fehler

# Einzelnes Konto validieren
validator = DATEVValidator()
konto_result = validator.validate_konto("8400")
print(konto_result['gueltig'])
print(konto_result.get('hinweis'))  # Erfolgskonto, Bestandskonto, etc.
```

### CLI Usage

```bash
# CSV-Datei validieren
python datev_validator.py validate buchungen.csv

# Einzelnes Konto prüfen
python datev_validator.py validate-konto 8400

# Beispiel-CSV generieren
python datev_validator.py sample
```

## 📋 Buchungsstapel-Header

```csv
Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;WKZ Umsatz;Kurs;Basisumsatz;WKZ Basisumsatz;Konto;Gegenkonto (ohne BU-Schlüssel);BU-Schlüssel;Belegdatum;Belegfeld 1;Belegfeld 2;Skonto;Buchungstext;Postensperre;Diverse Adressnummer;Geschäftspartnerbank;Sachverhalt;Zinssperre;Beleglink
```

## 📊 Rückgabewerte

```python
{
    'gueltig': True,
    'format': 'BUCHUNGSSTAPEL',
    'zeilen_gesamt': 150,
    'zeilen_fehlerhaft': 2,
    'fehler': [
        {'zeile': 5, 'feld': 'Belegdatum', 'fehler': 'Ungültiges Datumsformat'},
        {'zeile': 12, 'feld': 'Konto', 'fehler': 'Konto ungültig'}
    ],
    'warnungen': []
}
```

## 🔢 Validierungsregeln

### Pflichtfelder
- `Umsatz (ohne Soll/Haben-Kz)`
- `Soll/Haben-Kennzeichen` (S oder H)
- `Konto` (max. 9 Stellen)
- `Gegenkonto (ohne BU-Schlüssel)` (max. 9 Stellen)
- `Belegdatum` (Format: TTMMJJJJ)

### Soll/Haben-Kennzeichen
| Wert | Bedeutung |
|------|-----------|
| `S` | Soll |
| `H` | Haben |

### Datumsformat
```
TTMMJJJJ (8 Ziffern)

Beispiele:
- 24022025 = 24.02.2025
- 31122025 = 31.12.2025
```

### Kontenstruktur (SKR03/SKR04)
| Bereich | Kontenart |
|---------|-----------|
| 1000-6999 | Bestandskonten (Aktiv/Passiv) |
| 8000-8999 | Erfolgskonten (Aufwand/Ertrag) |
| 9000-9999 | Abschlusskonten |

## ⚡ Automation-Ready

### E-Commerce Export

```python
def generate_datev_export(orders):
    validator = DATEVValidator()
    
    # Erstelle CSV
    csv_lines = [header]
    for order in orders:
        csv_lines.append(format_order_as_datev(order))
    
    csv_content = '\n'.join(csv_lines)
    
    # Validiere vor Export
    result = validator.validate_csv(csv_content)
    
    if not result.gueltig:
        notify_accountant(result.fehler)
        return {'status': 'ERROR', 'fehler': result.fehler}
    
    return {'status': 'OK', 'csv': csv_content}
```

### DATEV-Import-Workflow

```python
def import_datev_file(filepath):
    validator = DATEVValidator()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        csv_content = f.read()
    
    result = validator.validate_csv(csv_content)
    
    if result.zeilen_fehlerhaft > 0:
        return {
            'status': 'PARTIAL',
            'gueltige_zeilen': result.zeilen_gesamt - result.zeilen_fehlerhaft,
            'fehlerhafte_zeilen': result.zeilen_fehlerhaft,
            'fehler': result.fehler
        }
    
    # Import durchführen
    import_to_accounting(csv_content)
    return {'status': 'OK'}
```

### Buchhaltungsprüfung

```python
def validate_booking_entry(entry):
    validator = DATEVValidator()
    
    # Konto validieren
    konto_check = validator.validate_konto(entry['konto'])
    if not konto_check['gueltig']:
        return {'valid': False, 'error': konto_check['fehler']}
    
    # Gegenkonto validieren
    gegenkonto_check = validator.validate_konto(entry['gegenkonto'])
    if not gegenkonto_check['gueltig']:
        return {'valid': False, 'error': gegenkonto_check['fehler']}
    
    return {'valid': True}
```

## 📝 Beispiel-Buchung

```csv
Umsatz (ohne Soll/Haben-Kz);Soll/Haben-Kennzeichen;WKZ Umsatz;Kurs;Basisumsatz;WKZ Basisumsatz;Konto;Gegenkonto (ohne BU-Schlüssel);BU-Schlüssel;Belegdatum;Belegfeld 1;Belegfeld 2;Skonto;Buchungstext;Postensperre;Diverse Adressnummer;Geschäftspartnerbank;Sachverhalt;Zinssperre;Beleglink
1000,00;S;EUR;;;;8400;1200;;24022025;RE-2025-001;;;Erlöse aus Lieferungen;;;;;;;
```

**Bedeutung:**
- 1000,00 € Soll an Konto 8400 (Erlöse)
- gegen 1200 (Forderungen)
- Belegdatum: 24.02.2025
- Beleg-Nr: RE-2025-001

## 🔗 Weiterführende Links

- [DATEV-Homepage](https://www.datev.de/)
- [DATEV-Formatbeschreibung](https://developer.datev.de/)
- [SKR03 Kontenrahmen](https://de.wikipedia.org/wiki/SKR03)
- [SKR04 Kontenrahmen](https://de.wikipedia.org/wiki/SKR04)

## ⚠️ Wichtige Hinweise

- **Trennzeichen**: Meist Semikolon (`;`)
- **Encoding**: UTF-8 oder Windows-1252
- **Dezimaltrenner**: Komma (`,`) für Umsätze
- **Datum**: Keine Punkte (TTMMJJJJ statt TT.MM.JJJJ)
- **Konten**: Maximal 9 Stellen
- **BU-Schlüssel**: Optional, für automatische Steuerbuchungen
