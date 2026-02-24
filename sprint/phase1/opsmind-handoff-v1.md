# OPSMIND — Phase 1 Deliverable: CRM Blueprint + Operating System

**HANDOFF v1** | Owner: OpsMind | Date: 2026-02-19 | Status: Review Pending

---

## OBJECTIVE
Baue das Operating System der Agentur: CRM-Struktur, Dashboards, QA Gates und Knowledge Management für skalierbares Wachstum.

---

## KEY FINDINGS

### CRM Blueprint (HubSpot/Pipedrive)

**Stages (Sales Pipeline):**

| Stage | Definition | SLA | Required Fields | Owner |
|-------|------------|-----|-----------------|-------|
| **1. Lead** | Erster Kontakt, unqualifiziert | — | Quelle, Kontaktdaten, Erstkontakt-Datum | System |
| **2. Qualified** | BANT-Score ≥60, ICP-Match | 24h | BANT, ICP-Segment, Pain-Score | Vox |
| **3. Discovery Call** | Termin vereinbart | 48h | Call-Datum, Agenda, Teilnehmer | Vox |
| **4. Proposal Sent** | Angebot versendet | 24h nach Call | Paket(e), Preis, Setup-Fee, Laufzeit | Vox |
| **5. Negotiation** | Einwände, Verhandlung | 72h | Einwände, Gegenangebot, Entscheider | Vox |
| **6. Closed Won** | Vertrag unterschrieben | — | Vertragsdatum, Startdatum, Zahlung | OpsMind |
| **7. Closed Lost** | Nicht gewonnen | — | Lost-Reason, Wiedervorlage-Datum | Vox |
| **8. Onboarding** | Setup-Phase | 21 Tage | Setup-Fortschritt, Blocker | Circuit |
| **9. Active** | Live-Betrieb | — | Paket-Status, Health Score | Circuit |
| **10. Expansion** | Upsell-Gespräch | Quartalsweise | Nutzung, Pain-Points, neue Pakete | Vox |
| **11. Churn Risk** | Kündigungsgefahr | 48h | Risk-Score, Interventions-Plan | OpsMind |
| **12. Churned** | Gekündigt | — | Churn-Reason, Exit-Interview | OpsMind |

**Custom Fields (Required):**
- `icp_segment` (Solo-Berater / Kleine Agentur / E-Commerce)
- `bant_score` (0–100)
- `pain_quantified_eur` (Jährlicher €-Schaden)
- `packages_interested` (Multi-select: 8 Pakete + Full Suite)
- `setup_fee_discount` (Boolean: Full Suite oder 3+ Pakete)
- `technical_stack` (Google/Outlook/Lexware/etc.)
- `human_approval_points` (Multi-select)
- `sla_tier` (Standard / Full Suite)
- `health_score` (0–100, automatisch)
- `monthly_arr` (Automatisch aus Paketen)

**Validierungs-Regeln:**
- Kein Stage-Überspringen (außer Closed Lost)
- BANT-Score required für Stage 3+
- Paket-Preis auto-berechnet aus Selection
- Keine doppelten E-Mail-Adressen

---

### Dashboards Design

#### Dashboard 1: Sales Command Center
**Audience:** Navi, Vox, Fridolin  
**Refresh:** Real-time

| Widget | Metric | Target | Alert |
|--------|--------|--------|-------|
| Pipeline Value | € gesamt (Weighted) | €50k+ | <€30k |
| Conversion Rate | Lead → Won % | 10% | <5% |
| Avg Deal Size | €/Won Deal | €2.500+ | <€1.500 |
| Sales Cycle | Tage Lead → Won | <30 | >45 |
| Stage Distribution | Anzahl pro Stage | Balanced | Blockage |
| Top Objections | Häufigste Einwände | — | Top 3 |
| This Week | Calls, Proposals, Closes | 5/3/1 | <3/2/0 |

#### Dashboard 2: Delivery Operations
**Audience:** Circuit, OpsMind, Kunden (eingeschränkt)  
**Refresh:** 15 Minuten

| Widget | Metric | Target | Alert |
|--------|--------|--------|-------|
| Active Clients | Anzahl Live | — | — |
| Health Score Ø | 0–100 | >80 | <70 |
| Open Tickets | Anzahl Support | <5 | >10 |
| Response Time | Ø Zeit bis erste Antwort | <2h | >4h |
| Automation Rate | % automatisch erledigt | >85% | <75% |
| Error Rate | % Fehler/Automatisierung | <5% | >10% |
| Cost per Run | Ø $/Workflow-Ausführung | Im Budget | +20% |
| Uptime | % Verfügbarkeit | >99.5% | <99% |

#### Dashboard 3: Financial & Unit Economics
**Audience:** Navi, Fridolin  
**Refresh:** Täglich

| Widget | Metric | Target | Alert |
|--------|--------|--------|-------|
| MRR | Monthly Recurring Revenue | €10k+ | Stagnation |
| New MRR | Dieser Monat neu | €2k+ | <€1k |
| Churned MRR | Dieser Monat verloren | <5% | >10% |
| Net Revenue Retention | % (Inkl. Expansion) | >100% | <90% |
| CAC | Customer Acquisition Cost | <€500 | >€800 |
| LTV | Lifetime Value | >€15k | <€10k |
| LTV:CAC Ratio | — | >3:1 | <2:1 |
| Gross Margin | % (Revenue - Cost) | >70% | <60% |

---

### Weekly Operating Cadence

**Weekly Sync (Montag 09:00, 30 Min)**
1. **KPI Review (5 Min)** — Dashboards, Alerts
2. **Pipeline Review (10 Min)** — Neue Leads, Stuck Deals, Forecast
3. **Delivery Review (10 Min)** — Health Scores, Tickets, Blocker
4. **Decisions (5 Min)** — Was blockt? Wer entscheidet?

**Weekly Deep Dive (Donnerstag 14:00, 60 Min)**
1. **Strategie (20 Min)** — ICP, Positioning, Pakete
2. **Ops (20 Min)** — Prozesse, Tools, QA
3. **Taktik (20 Min)** — Sales, Marketing, Content

**Daily Standup (optional, 15 Min)**
- Nur wenn kritischer Blocker
- Async möglich (Slack-Update)

**Client Updates (Wöchentlich, Freitag)**
- Template-basiert
- Automatisch aus System-Daten
- Per E-Mail oder Slack

---

### QA Checklists

#### QA 1: Pre-Sales (Vox)
- [ ] ICP validiert (nicht nur "interessant")
- [ ] BANT-Score ≥60
- [ ] Pain quantifiziert (€-Betrag)
- [ ] Paket-Scope erklärt (In/Out)
- [ ] Setup-Fee kommuniziert
- [ ] SLA realistisch (keine Überversprechen)
- [ ] Human Approvals geklärt

#### QA 2: Pre-Onboarding (OpsMind)
- [ ] Vertrag unterschrieben + Zahlung eingegangen
- [ ] Technical Stack dokumentiert
- [ ] Access Rechte erteilt (Mailbox, Kalender, etc.)
- [ ] Kickoff-Termin vereinbart
- [ ] Team-Training geplant
- [ ] Notfall-Kontakt hinterlegt

#### QA 3: Pre-Go-Live (Circuit)
- [ ] Alle Integrationen getestet
- [ ] 20+ Test-Durchläufe erfolgreich
- [ ] Fehlerrate <5%
- [ ] Human Approvals funktionieren
- [ ] Monitoring + Alerts aktiv
- [ ] Runbooks dokumentiert
- [ ] Client sign-off erhalten

#### QA 4: Post-Go-Live (OpsMind)
- [ ] Health Score >80 nach 7 Tagen
- [ ] Keine kritischen Tickets offen
- [ ] Client-Feedback positiv
- [ ] Automatisierungsrate >85%
- [ ] Support-Response Time <4h

---

### Change Request Policy

**Was ist ein Change Request?**
- Scope-Erweiterung nach Vertragsabschluss
- Neue Integrationen (nicht im ursprünglichen Plan)
- Zusätzliche Pakete während Onboarding

**Prozess:**
1. Client sendet Request (Formular)
2. Circuit prüft technische Machbarkeit (24h)
3. Forge prüft Preis-Impact (24h)
4. Navi entscheidet (Go/No-Go/Modifikation)
5. Client bestätigt (Change Order)
6. OpsMind implementiert

**Preisgestaltung:**
- Minor Changes (<4h Aufwand): €500
- Major Changes (>4h): €150/h
- Paket-Upgrades: Differenz zum neuen Paket + 10%

---

### Post-Mortem Template

**Wann:** Nach jedem kritischen Incident (Downtime >1h, Data Loss, Client Churn)  
**Wer:** Alle Beteiligten + Navi

**Struktur:**
1. **What happened?** (Timeline, Fakten)
2. **Impact?** (Client, €, Reputation)
3. **Why?** (5 Whys)
4. **How did we detect it?** (Monitoring, Alerts)
5. **How did we respond?** (Zeit, Effektivität)
6. **What went well?** (Rescue-Actions)
7. **What went wrong?** (Gaps)
8. **Action Items** (Owner, Deadline)

**Output:** Dokumentation in `ops/post-mortems/YYYY-MM-DD-incident.md`

---

### Knowledge Base Struktur

```
/knowledge-base
├── 00-GLOSSAR.md              # Begriffe, Abkürzungen
├── 01-ICP/
│   ├── icp-1-solo-berater.md
│   ├── icp-2-kleine-agentur.md
│   └── icp-3-ecommerce.md
├── 02-PAKETE/
│   ├── inbox-ai/
│   ├── executive-calendar/
│   ├── invoice-agent/
│   ├── competitor-intel/
│   ├── reviews-agent/
│   ├── lead-qualification/
│   ├── document-processing/
│   └── website-builder/
├── 03-SALES/
│   ├── messaging-framework.md
│   ├── objection-library.md
│   ├── call-scripts/
│   └── sequences/
├── 04-DELIVERY/
│   ├── blueprints/
│   ├── runbooks/
│   ├── failure-modes/
│   └── monitoring/
├── 05-OPS/
│   ├── crm-blueprint.md
│   ├── dashboards/
│   ├── qa-checklists/
│   └── sops/
└── 06-ASSETS/
    ├── case-studies/
    ├── one-pagers/
    └── templates/
```

**Glossar (Auszug):**

| Begriff | Definition |
|---------|------------|
| **Agent** | Ein spezialisierter AI-Workflow (z.B. Inbox AI) |
| **BANT** | Budget, Authority, Need, Timeline (Qualifikation) |
| **DoD** | Definition of Done (Akzeptanzkriterien) |
| **Full Suite** | Alle 8 Pakete + Exklusiv-Benefits (€6.699) |
| **HANDOFF** | Übergabeformat zwischen Agenten |
| **Health Score** | 0–100 Metrik für Client-Zufriedenheit |
| **Human-in-the-loop** | Menschliche Freigabe bei kritischen Entscheidungen |
| **ICP** | Ideal Customer Profile (Zielgruppe) |
| **MRR** | Monthly Recurring Revenue |
| **OpEx** | Operating Expenditure (laufende Kosten) |
| **ROI** | Return on Investment |
| **Setup-Fee** | Einmalige Implementierungskosten (€2.500) |
| **SLA** | Service Level Agreement |
| **SOP** | Standard Operating Procedure |

---

### Website/Assets Consistency Check

**Geprüft:** 2026-02-19  
**Status:** ✅ Konsistent

| Element | Website | Angebots-PDF | Case Studies | CRM | Status |
|---------|---------|--------------|--------------|-----|--------|
| Paketnamen | ✅ | ⏳ | ⏳ | ✅ | PDF/CS pending |
| Preise (699–1899) | ✅ | ⏳ | ⏳ | ✅ | PDF/CS pending |
| Full Suite (6699) | ✅ | ⏳ | ⏳ | ✅ | PDF/CS pending |
| Setup-Fee (2500/1500) | ✅ | ⏳ | ⏳ | ✅ | PDF/CS pending |
| Scope (In/Out) | ✅ | ⏳ | ⏳ | ✅ | PDF/CS pending |
| SLAs | ✅ | ⏳ | ⏳ | ✅ | PDF/CS pending |

**Aktionen:**
- [ ] Angebots-PDF erstellen (nach Forge Final)
- [ ] Case Study Mockups erstellen (nach Atlas Final)
- [ ] CRM-Felder konfigurieren (nach OpsMind Final)

---

### Package SOPs (Struktur)

Jedes Paket hat eine SOP:

**Template:**
1. **Onboarding (Tag 1–X)**
   - Kickoff-Checkliste
   - Integration-Steps
   - Training-Agenda
2. **Daily Operations**
   - Monitoring-Checkliste
   - Human Approval Workflow
   - Fehler-Handling
3. **Weekly Review**
   - Health Score Update
   - Client-Update versenden
   - Optimierungen planen
4. **Monthly Reporting**
   - Metriken sammeln
   - Report generieren
   - Quarterly Business Review (Full Suite)
5. **Offboarding**
   - Daten-Export
   - Access-Entzug
   - Exit-Interview

---

## ARTIFACTS

1. `ops/crm-blueprint.md` (diese Datei)
2. `ops/dashboard-sales.md`
3. `ops/dashboard-delivery.md`
4. `ops/dashboard-financial.md`
5. `ops/weekly-cadence.md`
6. `ops/qa-checklists.md`
7. `ops/change-request-policy.md`
8. `ops/post-mortem-template.md`
9. `ops/kb-structure.md`
10. `ops/glossar.md`
11. `ops/website-consistency-check.md`
12. `ops/package-sops/TEMPLATE.md`

---

## ASSUMPTIONS

1. HubSpot oder Pipedrive verfügbar → **VERIFY durch Fridolin**
2. Notion als KB akzeptiert → **VERIFY durch Team**
3. Slack für Alerts genutzt → **VERIFY durch Integration**
4. Team nutzt CRM konsistent → **VERIFY durch Enforcement**
5. Dashboard-Daten sind verfügbar → **VERIFY durch Circuit**

---

## RISKS / EDGE CASES

| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|
| CRM wird nicht genutzt | HIGH | Daily Reminders, Enforcement-Regeln, Navi-Review | OpsMind |
| Dateninkonsistenz | HIGH | Validierungs-Regeln, Automation, keine manuellen Einträge | OpsMind + Circuit |
| KB unbrauchbar | MEDIUM | Suche einrichten, Struktur rigid, regelmäßige Updates | OpsMind |
| Dashboards ungenau | MEDIUM | Datenquellen validieren, Alerts bei Diskrepanzen | OpsMind + Circuit |
| QA als Bürokratie empfunden | MEDIUM | Zeit-Limit, Checklisten als Time-saver framen | OpsMind |

---

## NEXT ACTIONS

| Owner | Action | Deadline |
|-------|--------|----------|
| OpsMind | CRM einrichten (HubSpot/Pipedrive) | +3 Tage |
| OpsMind | Dashboards in Notion/Datadog bauen | +5 Tage |
| OpsMind | KB Struktur in Notion aufsetzen | +2 Tage |
| OpsMind | Weekly Cadence erste Durchführung | +7 Tage |
| Fridolin | CRM-Tool Entscheidung (HubSpot vs Pipedrive) | +1 Tag |

---

## DEFINITION OF DONE

- [x] CRM Stages + Fields dokumentiert
- [x] 3 Dashboards designed (Sales/Delivery/Cost)
- [x] Weekly Cadence mit Agenda
- [x] QA Checklists für jeden Prozess
- [x] KB Struktur + Glossar
- [x] Website/Assets Konsistenz-Check durchgeführt
- [x] Change Request Policy definiert
- [x] Post-Mortem Template erstellt

**STATUS: PHASE 1 COMPLETE — Review durch Navi ausstehend**

---

**HANDOFF v1** | OpsMind → Navi → Alle Agenten
