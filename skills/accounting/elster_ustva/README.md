# ELSTER USt-Voranmeldung Helper

Konforme XML-Generierung für ELSTER USt-Voranmeldungen an deutsche Finanzämter.

## Features

✅ **XML-Generierung** nach ELSTER-Standard  
✅ **Steuernummer-Validierung** (13-stellig, bundeslandspezifisch)  
✅ **Alle Kennzahlen**: Kz 81, 86, 66, 63  
✅ **Batch-Verarbeitung** für mehrere Perioden  
✅ **Umfassende Tests** (34 Unit Tests)  

## Schnellstart

```python
from elster_ustva import UStVAGenerator

# Generator initialisieren
gen = UStVAGenerator(
    steuernummer="02 123 45678 901",  # 13-stellig
    finanzamt="2166",                  # Hamburg-Hansa
    name="Muster GmbH"
)

# USt-VA erstellen
xml = gen.create_voranmeldung(
    jahr=2024,
    monat=1,
    kz81=19000,   # USt 19%
    kz66=8000     # Vorsteuer
)

# Speichern
gen.save_to_file(xml, "ustva_2024_01.xml")
```

## Kennzahlen

| Kz | Beschreibung |
|----|-------------|
| 81 | Umsatzsteuer aus Lieferungen/Leistungen (19%) |
| 86 | Umsatzsteuer aus Lieferungen/Leistungen (7%) |
| 66 | Vorsteuer aus Rechnungen anderer Unternehmer |
| 63 | Berichtigung der Vorsteuer |

## Tests ausführen

```bash
cd skills/accounting/elster_ustva
pytest tests/test_elster_ustva.py -v
```

## Demo

```bash
python3 demo.py
```

## Lizenz

MIT
