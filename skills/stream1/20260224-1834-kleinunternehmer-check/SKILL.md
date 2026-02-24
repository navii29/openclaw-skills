# Kleinunternehmer Check

Prüft automatisch Kleinunternehmer-Status nach §19 UStG.

**Version:** 1.0.0 | **Preis:** 39 EUR

## Features

- ✅ **Umsatzgrenzen-Check** - 22.000€ / 50.000€ Grenzen
- ✅ **Steuerbefreiung** - §19 UStG Anwendung
- ✅ **Prognose** - Nächstes Jahr Vorab-Prüfung
- ✅ **Rechnungshinweis** - Pflicht-Text generieren

## Quick Start

```python
from kleinunternehmer_check import check_kleinunternehmer
result = check_kleinunternehmer(
    umsatz_vorjahr=21000,
    umsatz_aktuelles_jahr=15000
)
print(result['status'])  # KLEINUNTERNEHMER
```

## Status

- KLEINUNTERNEHMER - Befreit
- GRENZFAELLIG - Vorsicht
- REGULÄR - USt pflichtig

## Use Cases

1. **Jahresabschluss**: Status prüfen
2. **Rechnungsstellung**: Hinweis-Text
3. **Steuerberatung**: Grenzwert-Überwachung

## Lizenz

MIT
