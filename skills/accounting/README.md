# Skill Factory: Buchhaltung & Compliance (German Market)

Übersicht über alle entwickelten Skills für die deutsche Buchhaltung.

---

## 📊 Skills Übersicht

| Skill | Status | Tests | Beschreibung |
|-------|--------|-------|--------------|
| **ELSTER USt-Voranmeldung** | ✅ Fertig | 34 | XML-Generator für Finanzamt |
| **Rechnungs-Matching** | ✅ Fertig | 31 | Zahlungen zuordnen |
| **GoBD Compliance Checker** | ✅ Fertig | 33 | Alle 11 Pflichtangaben prüfen |

**Gesamt: 98 Unit Tests**

---

## 📁 Verzeichnisstruktur

```
skills/accounting/
├── elster_ustva/
│   ├── SKILL.md              # Dokumentation
│   ├── README.md             # Kurzübersicht
│   ├── requirements.txt      # Abhängigkeiten
│   ├── demo.py               # Demonstration
│   ├── src/
│   │   └── elster_ustva.py   # Hauptmodul (~400 Zeilen)
│   ├── tests/
│   │   └── test_elster_ustva.py  # 34 Unit Tests
│   └── data/
│       └── beispieldaten.json    # Testdaten
│
├── invoice_matching/
│   ├── SKILL.md              # Dokumentation
│   ├── README.md             # Kurzübersicht
│   ├── demo.py               # Demonstration
│   ├── src/
│   │   └── invoice_matching.py   # Hauptmodul (~550 Zeilen)
│   ├── tests/
│   │   └── test_invoice_matching.py  # 31 Unit Tests
│   └── data/
│       └── beispieldaten.json    # Testdaten
│
└── gobd_compliance/
    ├── SKILL.md              # Dokumentation
    ├── README.md             # Kurzübersicht
    ├── demo.py               # Demonstration
    ├── src/
    │   └── gobd_checker.py   # Hauptmodul (~600 Zeilen)
    ├── tests/
    │   └── test_gobd_checker.py    # 33 Unit Tests
    └── data/
        └── beispieldaten.json    # Testdaten
```

---

## 🔧 Schnellstart

### Alle Tests ausführen

```bash
cd skills/accounting

# ELSTER
cd elster_ustva && pytest tests/ -v

# Invoice Matching
cd ../invoice_matching && pytest tests/ -v

# GoBD
cd ../gobd_compliance && pytest tests/ -v
```

### Alle Demos ausführen

```bash
cd skills/accounting

python3 elster_ustva/demo.py
python3 invoice_matching/demo.py
python3 gobd_compliance/demo.py
```

---

## 📋 Skill Details

### 1. ELSTER USt-Voranmeldung Helper

**Features:**
- XML-Generierung nach amtlicher ELSTER-Vorlage
- Unterstützt Kz 81, 86, 66, 63
- Steuernummer-Validierung (13-stellig)
- Batch-Verarbeitung
- DATEV-kompatibel

**Verwendung:**
```python
from elster_ustva import UStVAGenerator

gen = UStVAGenerator(
    steuernummer="0212345678901",
    finanzamt="2166",
    name="Muster GmbH"
)

xml = gen.create_voranmeldung(
    jahr=2024, monat=1,
    kz81=19000, kz66=8000
)
```

---

### 2. Rechnungs-Matching

**Features:**
- Exaktes Matching (Rechnungsnummer + Betrag)
- Fuzzy Matching (Betrags-Toleranz)
- Teilzahlungen erkennen
- Doppelte Zahlungen erkennen
- DATEV-CSV Export

**Verwendung:**
```python
from invoice_matching import InvoiceMatcher

matcher = InvoiceMatcher(toleranz_prozent=1.0)
matcher.lade_rechnungen([...])
matcher.lade_zahlungen([...])

ergebnis = matcher.match()
print(f"{ergebnis['stats']['match_rate']*100:.0f}% gematcht")
```

---

### 3. GoBD Compliance Checker

**Features:**
- Alle 11 Pflichtangaben nach § 14 UStG prüfen
- Chronologische Rechnungsnummern prüfen
- Unveränderbarkeit (SHA-256 Hash)
- Batch-Prüfung
- Detaillierte Berichte

**Verwendung:**
```python
from gobd_checker import Rechnung, Rechnungsposition, GoBDChecker

rechnung = Rechnung(
    rechnungsnr="RE-001",
    ausstellungsdatum="2024-01-15",
    lieferdatum="2024-01-10",
    steller_name="Muster GmbH",
    steller_anschrift="Musterstraße 1",
    steller_ustid="DE123456789",
    empfaenger_name="Kunde AG",
    empfaenger_anschrift="Kundenweg 42",
    positionen=[Rechnungsposition("Beratung", 10, 100, 19)]
)

checker = GoBDChecker()
ergebnis = checker.pruefe_rechnung(rechnung)
```

---

## 🧪 Testabdeckung

| Skill | Tests | Abdeckung |
|-------|-------|-----------|
| ELSTER | 34 | Steuernummer-Validierung, XML-Generierung, Betrags-Validierung |
| Invoice Matching | 31 | Matching-Algorithmus, DATEV-Export, Fehlerbehandlung |
| GoBD Checker | 33 | Alle 11 Pflichtangaben, Hash, Chronologie |

**Test-Features:**
- ✅ Alle Use-Cases abgedeckt
- ✅ Fehlerbehandlung getestet
- ✅ Edge Cases berücksichtigt
- ✅ Dataclass-Validierung

---

## 📚 DATEV & Steuerrecht Referenzen

- **GoBD:** BMF-Schreiben vom 28.11.2019
- **§ 14 UStG:** Rechnungspflichten
- **ELSTER:** amtliche XML-Schemas
- **DATEV:** Standard CSV-Formate (SKR03/SKR04)

---

## 📝 Qualitätskriterien

Jeder Skill erfüllt:
- ✅ SKILL.md mit Use-Cases
- ✅ Python-Code mit Error Handling
- ✅ 10+ Unit Tests (tatsächlich: 30+)
- ✅ Beispieldaten (JSON)
- ✅ Demo-Skript
- ✅ README.md
- ✅ DATEV-kompatibel

---

## 🎯 Nächste Schritte (optional)

Mögliche Erweiterungen:
- **ZUGFeRD/Factur-X** Rechnungs-Generierung
- **SEPA-Lastschrift** XML-Generierung
- **EÜR** (Einnahmen-Überschuss-Rechnung) Generator
- **DATEV-ASCII** Import/Export vollständig

---

## 📄 Lizenz

Alle Skills: MIT License

---

**Erstellt:** 2024-02-25  
**Status:** ✅ Produktionsreif
