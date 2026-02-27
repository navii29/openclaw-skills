# GoBD Compliance Checker

**Version:** 1.0.0  
**Domain:** German Tax Law / GoBD / Rechnungsprüfung  
**Status:** Production Ready

---

## Übersicht

Prüft Rechnungen und Buchungsdaten auf Einhaltung der GoBD (Grundsätze zur ordnungsmäßigen Führung und Aufbewahrung von Büchern, Aufzeichnungen und Unterlagen in elektronischer Form sowie zum Datenzugriff).

### Die 11 GoBD-Pflichtangaben

| Nr | Pflichtangabe | Prüfung |
|----|--------------|---------|
| 1 | Name und Anschrift des leistenden Unternehmers | ✅ |
| 2 | Name und Anschrift des Leistungsempfängers | ✅ |
| 3 | Steuernummer oder USt-IdNr des leistenden Unternehmers | ✅ |
| 4 | Ausstellungsdatum | ✅ |
| 5 | Rechnungsnummer (fortlaufend, eindeutig) | ✅ |
| 6 | Menge und Bezeichnung der gelieferten Gegenstände/Dienstleistungen | ✅ |
| 7 | Zeitpunkt der Lieferung/Leistung | ✅ |
| 8 | Entgelt (netto) | ✅ |
| 9 | Steuersatz oder Steuerbefreiung | ✅ |
| 10 | Umsatzsteuerbetrag | ✅ |
| 11 | Unveränderbarkeit (Hash/Signatur) | ✅ |

### Zusätzliche Prüfungen

| Prüfung | Beschreibung |
|---------|-------------|
| **Chronologie** | Rechnungsnummern müssen fortlaufend sein |
| **Eindeutigkeit** | Keine doppelten Rechnungsnummern |
| **Hash-Verifikation** | SHA-256 Hash zur Unveränderbarkeit |
| **Zeitraum** | Lieferdatum im gültigen Zeitraum |

---

## Use Cases

### UC1: Rechnung auf GoBD-Konformität prüfen
**Als** Buchhalter  
**möchte ich** eine Rechnung auf alle GoBD-Pflichtangaben prüfen  
**damit** sie steuerlich anerkannt wird.

---

### UC2: Chronologische Rechnungsnummern prüfen
**Als** Prüfer  
**möchte ich** prüfen ob Rechnungsnummern fortlaufend sind  
**damit** Lücken oder Dopplungen erkannt werden.

---

### UC3: Unveränderbarkeit sicherstellen
**Als** Steuerpflichtiger  
**möchte ich** Rechnungen mit einem Hash versehen  
**damit** spätere Änderungen nachweisbar sind.

---

### UC4: Batch-Prüfung aller Rechnungen
**Als** Buchhalter  
**möchte ich** alle Rechnungen eines Zeitraums prüfen  
**damit** ich einen GoBD-Konformitätsbericht erstellen kann.

---

## API

```python
from gobd_checker import GoBDChecker, Rechnung

# Checker initialisieren
checker = GoBDChecker()

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
        {'bezeichnung': 'Beratung', 'menge': 10, 'preis': 100.00, 'steuersatz': 19},
    ]
)

# Prüfen
ergebnis = checker.pruefe_rechnung(rechnung)

if ergebnis.ist_konform:
    print("✅ GoBD-konform")
else:
    for mangel in ergebnis.mangel:
        print(f"❌ {mangel}")

# Hash für Unveränderbarkeit
hash_wert = checker.berechne_hash(rechnung)
```

---

## Prüfergebnis

```python
{
    'ist_konform': True/False,
    'pflichtangaben': {
        'steller_name': True,
        'steller_anschrift': True,
        'steller_steuerid': True,
        'empfaenger_name': True,
        'empfaenger_anschrift': True,
        'ausstellungsdatum': True,
        'rechnungsnr': True,
        'lieferdatum': True,
        'positionen': True,
        'steuersatz': True,
        'steuerbetrag': True,
    },
    'mangel': [],  # Liste fehlender Angaben
    'hash': 'sha256:abc123...',
    'empfohlene_aktionen': []
}
```

---

## Chronologie-Prüfung

```python
from gobd_checker import ChronologiePruefer

pruefer = ChronologiePruefer()

rechnungsnr_liste = ['RE-001', 'RE-002', 'RE-004']  # RE-003 fehlt!
ergebnis = pruefer.pruefe_fortlaufend(rechnungsnr_liste)

# Ergebnis:
# {
#     'ist_fortlaufend': False,
#     'luecken': ['RE-003'],
#     'doppelte': [],
#     'warnungen': ['Lücke zwischen RE-002 und RE-004']
# }
```

---

## Installation

```bash
pip install hashlib
```

---

## DATEV-Referenz

- **GoBD:** BMF-Schreiben vom 28.11.2019 (IV A 4 - S 0316/19/10004)
- **§ 14 UStG:** Rechnungspflichten
- **§ 238 HGB:** Ordentliche Buchführung

---

## Lizenz

MIT - Für den professionellen Einsatz in der deutschen Buchhaltung.
