# ELSTER USt-Voranmeldung Helper

**Version:** 1.0.0  
**Domain:** German Tax / ELSTER / USt-Voranmeldung  
**Status:** Production Ready

---

## Übersicht

Generiert konforme XML-Dateien für die elektronische Umsatzsteuer-Voranmeldung (USt-VA) an das deutsche Finanzamt via ELSTER.

### Unterstützte Kennzahlen (Kz)

| Kz | Beschreibung | XML-Tag |
|----|-------------|---------|
| 81 | Umsatzsteuer aus Lieferungen/Leistungen (19%) | `Umsatzsteuer` |
| 86 | Umsatzsteuer aus Lieferungen/Leistungen (7%) | `Umsatzsteuer_7` |
| 66 | Vorsteuer aus Rechnungen anderer Unternehmer | `Vorsteuer` |
| 63 | Berichtigung Vorsteuer (z.B. nicht abzugsfähig) | `Berichtigung_Vorsteuer` |

---

## Use Cases

### UC1: Monatliche USt-Voranmeldung erstellen
**Als** Buchhalter  
**möchte ich** eine USt-Voranmeldung für einen Monat erstellen  
**damit** ich sie an das Finanzamt übermitteln kann.

**Input:**
- Steuernummer (13-stellig)
- Zeitraum (Monat/Jahr)
- Beträge für Kz 81, 86, 66, 63

**Output:** Validierbare XML-Datei

---

### UC2: Steuernummer validieren
**Als** Anwender  
**möchte ich** die Gültigkeit einer deutschen Steuernummer prüfen  
**damit** keine ungültigen Übermittlungen erfolgen.

**Prüfungen:**
- 11-stellige USt-IdNr (EU-weit)
- 13-stellige nationale Steuernummer
- Prüfziffernberechnung

---

### UC3: Batch-Verarbeitung mehrerer Perioden
**Als** Buchhalter  
**möchte ich** mehrere Monate auf einmal verarbeiten  
**damit** ich Quartals- oder Jahresdaten effizient erstelle.

---

### UC4: XML-Validierung vor ELSTER-Upload
**Als** Prüfer  
**möchte ich** das XML vor dem Upload validieren  
**damit** Ablehnungen durch das Finanzamt vermieden werden.

---

## API

```python
from elster_ustva import UStVAGenerator, SteuernummerValidator

# Generator initialisieren
gen = UStVAGenerator(
    steuernummer="1234567890123",
    finanzamt="2166",
    name="Muster GmbH"
)

# Voranmeldung erstellen
xml_content = gen.create_voranmeldung(
    jahr=2024,
    monat=1,
    kz81=19000,  # €19.000 USt 19%
    kz86=7000,   # €7.000 USt 7%
    kz66=5000,   # €5.000 Vorsteuer
    kz63=0
)

# Validieren
validator = SteuernummerValidator()
valid = validator.validate_national("1234567890123")
```

---

## Fehlerbehandlung

| Exception | Auslöser |
|-----------|----------|
| `InvalidSteuernummerError` | Ungültige Steuernummer |
| `InvalidZeitraumError` | Ungültiger Monat/Jahr |
| `InvalidBetragError` | Negative Beträge, über Limit |
| `XMLGenerationError` | XML-Validierung fehlgeschlagen |

---

## Installation

```bash
pip install lxml
```

---

## DATEV-Referenz

- **Dokument:** USt-Voranmeldung (Formular)
- **ELSTER-Verfahren:** "elektronische Übermittlung der USt-Voranmeldung"
- **Schema:** XFinFormular (amtliche ELSTER-Schemas)

---

## Lizenz

MIT - Für den professionellen Einsatz in der deutschen Buchhaltung.
