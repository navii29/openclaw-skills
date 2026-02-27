# GoBD Compliance Checker

Prüft Rechnungen auf Einhaltung der GoBD (Grundsätze zur ordnungsmäßigen Führung und Aufbewahrung von Büchern).

## Features

✅ **11 Pflichtangaben** nach § 14 UStG prüfen  
✅ **Chronologie-Prüfung** (fortlaufende Rechnungsnummern)  
✅ **Unveränderbarkeit** (SHA-256 Hash)  
✅ **Batch-Prüfung**  
✅ **33 Unit Tests**  

## Die 11 GoBD-Pflichtangaben

1. Name und Anschrift des leistenden Unternehmers
2. Name und Anschrift des Leistungsempfängers
3. Steuernummer oder USt-IdNr des leistenden Unternehmers
4. Ausstellungsdatum
5. Rechnungsnummer (fortlaufend, eindeutig)
6. Menge und Bezeichnung der gelieferten Gegenstände/Dienstleistungen
7. Zeitpunkt der Lieferung/Leistung
8. Entgelt (netto)
9. Steuersatz oder Steuerbefreiung
10. Umsatzsteuerbetrag
11. Unveränderbarkeit (Hash/Signatur)

## Schnellstart

```python
from gobd_checker import Rechnung, Rechnungsposition, GoBDChecker

# Rechnung erstellen
rechnung = Rechnung(
    rechnungsnr="RE-2024-001",
    ausstellungsdatum="2024-01-15",
    lieferdatum="2024-01-10",
    steller_name="Muster GmbH",
    steller_anschrift="Musterstraße 1, 20095 Hamburg",
    steller_ustid="DE123456789",
    empfaenger_name="Kunde AG",
    empfaenger_anschrift="Kundenweg 42, 10115 Berlin",
    positionen=[
        Rechnungsposition("Beratung", 10, 100.00, 19),
    ]
)

# Prüfen
checker = GoBDChecker()
ergebnis = checker.pruefe_rechnung(rechnung)

if ergebnis.ist_konform:
    print("✅ GoBD-konform")
else:
    for mangel in ergebnis.mangel:
        print(f"❌ {mangel}")
```

## Tests

```bash
pytest tests/test_gobd_checker.py -v
```

## Demo

```bash
python3 demo.py
```

## Lizenz

MIT
