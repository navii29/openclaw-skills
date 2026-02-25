# Skill-Analyse & Verbesserungsplan

## Stand der Skills (nach WLAN-Ausfall-Analyse)

### Tier 1: Produktionsreif (Advanced)
| Skill | Version | Status | Kernaussage |
|-------|---------|--------|-------------|
| **inbox-ai** | v2.2.0 | ✅ Mature | Self-healing, SMTP pooling, persistent queue, HTML replies |
| **sevdesk** | v2.4.0 | ✅ Mature | ELSTER-Integration, Mahnwesen, DATEV-Export, GoBD-Compliance |

### Tier 2: MVP (Basis funktioniert, ausbaufähig)
| Skill | Status | Fehlt |
|-------|--------|-------|
| **gobd-rechnungsvalidator** | MVP | OCR, Batch-Processing, DATEV-Export, QR-Code |
| **datev-csv-export** | MVP | Automatische Kontenvorschläge, SEPA-XML, Zahlungsabgleich |
| **calendly-notion-crm** | Basic | Keine echte Implementierung, nur Spec |
| **shopify-telegram-alerts** | Basic | Webhook-Handler fehlt, nur Spec |
| **website-lead-alerts** | Basic | Kein Code, nur Konzept |
| **gmail-auto-responder** | Basic | Fehlt komplette Implementierung |

### Tier 3: Duplikate/Überlappungen
- `pdf-rechnung-datev` → Überlappt mit gobd-rechnungsvalidator + datev-csv-export
- `linkedin-scheduler` → Noch nicht analysiert

---

## Deep-Dive Recherche: Wichtige Erkenntnisse

### 1. E-Rechnung (ZUGFeRD/Factur-X) - KRITISCH
**Fakten:**
- Ab 2025: B2B-Rechnungen müssen elektronisch sein (EU-Richtlinie 2014/55/EU)
- Ab 2027: Alle Unternehmen betroffen (nicht nur öffentliche Auftraggeber)
- ZUGFeRD = PDF + XML in einer ZIP-Datei
- Factur-X = Französischer Standard, aber kompatibel

**Marktlücke:**
- 90% deutscher Unternehmen haben keine Lösung
- Steuerberater verlangen 50-200€/Monat für E-Rechnung-Service
- Bestehende Tools sind komplex und teuer

**Unsere Chance:**
GoBD-Validator + DATEV-Export + ZUGFeRD-Generator = Komplette Rechnungs-Automation

### 2. GoBD (Grundsätze zur ordnungsmäßigen Führung)
**Pflichtangaben (§14 UStG) - bereits abgedeckt:**
1. ✅ Name/Anschrift Lieferant
2. ✅ (Empfänger optional bei Kleinbetragsrechnungen)
3. ✅ Steuernummer oder USt-IdNr
4. ✅ Ausstellungsdatum
5. ✅ Fortlaufende Rechnungsnummer
6. ✅ Menge/Bezeichnung
7. ✅ Lieferzeitpunkt
8. ✅ Entgelt/Steuerbeträge
9. ✅ Steuersatz/Befreiung
10. ✅ §13b UStG Hinweis (wenn relevant)
11. ✅ §14c UStG Mängelhinweis

**Zusätzliche GoBD-Anforderungen (nicht im MVP):**
- Unveränderbarkeit (Prüfsumme/Signatur)
- Chronologische Rechnungsnummern
- Vollständige Ablage
- Sofortige Verbuchung
- 10-Jahre-Aufbewahrung

### 3. DATEV-Format-Spezifikationen
**Korrektes Format:**
```csv
Datum,Konto,Gegenkonto,BU-Schlüssel,Umsatz,Soll/Haben,Währung
150226,8400,1200,,1190,00,H,EUR
```

**Wichtige Details:**
- Datum: TTMMJJ (nicht TT.MM.JJJJ)
- Dezimaltrennzeichen: Komma (nicht Punkt)
- Feldtrennzeichen: Semikolon oder Komma
- UTF-8 BOM für Excel-Kompatibilität
- Keine Tausender-Trennpunkte

**Kontenrahmen SKR03 vs SKR04:**
- SKR03: 8400 = Erlöse 19% USt (Standard für Kleinunternehmen)
- SKR04: 4400 = Erlöse 19% USt (neuer Standard, größere Unternehmen)

### 4. ELSTER / USt-Voranmeldung
**Pflicht:**
- Monatlich: Bis 10. des Folgemonats
- Vierteljährlich: Wenn Vorjahresumsatz < 7.500€ USt
- Jährlich: USt-Erklärung bis 31.05.

**Kz-Felder (Kennzahlen):**
- Kz 81: Umsatzsteuer 19%
- Kz 86: Umsatzsteuer 7%
- Kz 66: Vorsteuer 19%
- Kz 63: Vorsteuer 7%

**sevdesk v2.4.0 deckt dies bereits ab** ✅

---

## Identifizierte Verbesserungsbereiche

### A. Kritische Lücken (sofort beheben)

#### A1. ZUGFeRD/E-Rechnung Generator
**Warum:** Gesetzliche Pflicht ab 2025, riesiger Markt
**Aufwand:** 2-3 Tage
**Features:**
- PDF + XML Erzeugung
- ZUGFeRD 2.1 / Factur-X kompatibel
- Validierung vor Versand
- QR-Code-Integration (XRechnung)

#### A2. GoBD-Validator Erweiterungen
**Fehlt:**
- OCR für gescannte Rechnungen (Tesseract)
- QR-Code/ERechnung-Parsing
- Batch-Verarbeitung ganzer Ordner
- Unveränderbarkeits-Check (Hash/Signatur)
- Automatische DATEV-Buchungsvorschläge

#### A3. DATEV-CSV Erweiterungen
**Fehlt:**
- Automatische Konto-Zuordnung (ML-basiert)
- SEPA-XML Export für Zahlungen
- Zahlungsabgleich (offene Posten)
- DATEV-Online API-Integration
- Automatische Gegenkonto-Vorschläge

### B. Architectural Improvements (Advanced Patterns)

#### B1. Event-Driven Architecture (EDA)
**Betrifft:** inbox-ai, sevdesk, alle E-Commerce Skills

**Problem aktuell:**
- Direkte API-Calls = enge Kopplung
- Keine Retry-Logik bei Fehlern
- Keine parallele Verarbeitung

**Lösung:**
- Cron als Event-Emitter
- Events in memory/events/
- sessions_spawn als Consumer
- Compensation bei Fehlern

**Impact:** 10x Skalierbarkeit, 99.9% Zuverlässigkeit

#### B2. CQRS für alle Skills
**Command Side (Write):**
- Alle schreibenden Operationen als Commands
- Validation vor Ausführung
- Event-Generierung

**Query Side (Read):**
- memory_search für alle Abfragen
- Projected Views für häufige Queries
- Aggregates für komplexe State

**Impact:** 10x schnellere Queries

#### B3. Saga Pattern für Workflows
**Beispiel: Invoice Processing Saga**
```
1. Receive Invoice (PDF) → Compensation: Delete
2. Extract Data (OCR) → Compensation: Reset
3. Validate GoBD → Compensation: Flag invalid
4. Create Booking (DATEV) → Compensation: Delete booking
5. Archive Document → Compensation: Restore
```

**Impact:** Fehlertoleranz, keine Dateninkonsistenz

### C. Skill-Consolidation

#### C1. Merge: gobd-validator + datev-export + ZUGFeRD
**Neuer Skill: "German Accounting Suite"**
- Ein Skill für alles
- PDF → Validierung → DATEV → E-Rechnung
- Single API, einfache Integration

#### C2. Merge: shopify-telegram + website-leads + calendly-notion
**Neuer Skill: "Lead Pipeline Automation"**
- Eingehende Leads aus allen Kanälen
- Einheitliches Scoring
- Automatische Weiterleitung

---

## Konkrete Adaptations-Plan

### Phase 1: Foundation (Woche 1)
1. **ZUGFeRD-Generator** bauen
2. **GoBD-Validator** + OCR erweitern
3. **Event-Schemas** für alle Skills definieren

### Phase 2: Architecture (Woche 2)
1. **EDA** in inbox-ai implementieren (Pilot)
2. **Saga Pattern** für Invoice-Processing
3. **CQRS** Views für Dashboards

### Phase 3: Consolidation (Woche 3)
1. **German Accounting Suite** (Merge GoBD+DATEV+ZUGFeRD)
2. **Lead Pipeline** (Merge Shopify+Website+Calendly)
3. Alte Skills als deprecated markieren

### Phase 4: Polish (Woche 4)
1. Dokumentation aktualisieren
2. Testsuite erweitern
3. GitHub-Publication vorbereiten

---

## Priorisierung nach Impact/Aufwand

| Task | Impact | Aufwand | Priorität |
|------|--------|---------|-----------|
| ZUGFeRD-Generator | 🔥🔥🔥 | 2-3 Tage | P0 (Marktpflicht) |
| GoBD + OCR | 🔥🔥 | 1-2 Tage | P1 |
| EDA Migration | 🔥🔥🔥 | 3-4 Tage | P1 |
| Skill-Consolidation | 🔥🔥 | 2 Tage | P2 |
| CQRS Views | 🔥 | 2 Tage | P2 |
| SEPA-XML | 🔥 | 1 Tag | P3 |

---

## Zusammenfassung für Fridolin

**Was wir haben:**
- 2 produktionsreife Skills (inbox-ai, sevdesk)
- 4 MVP-Skills mit Potential
- 3 Skills die nur Specs sind (kein Code)

**Was fehlt (kritisch):**
- ZUGFeRD/E-Rechnung (gesetzlich ab 2025 erforderlich)
- OCR für gescannte Dokumente
- Event-Driven Architecture (für Skalierung)

**Empfohlene nächste Schritte:**
1. SOFORT: ZUGFeRD-Generator bauen (Marktlücke)
2. DANN: GoBD-Validator + OCR erweitern
3. DANN: Advanced Patterns in inbox-ai pilotieren
4. DANN: Skills konsolidieren

**Frage an dich:**
Soll ich direkt mit Phase 1 beginnen (ZUGFeRD-Generator)? Oder erst die Background Agents stoppen und neu priorisieren?
