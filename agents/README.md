# NAVII Agentur – Agent System Übersicht

> Vollständiges Multi-Agent System für AI-Automation-Agentur  
> Commander: NAVII | Created: 2026-02-19

---

## Systemarchitektur

```
                    ┌─────────────┐
                    │   CLIENT    │
                    │  (Kunde)    │
                    └──────┬──────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                    NAVII                            │
│              (Commander/CEO)                        │
│     • Richtung, Priorität, Entscheidungen          │
│     • Output-Qualität, Subagenten-Führung          │
│     • KPI-Steuerung, Business-System               │
└─────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  ATLAS   │    │  FORGE   │    │   VOX    │
│ Research │ │  Offer   │ │  Sales   │
│Strategy │ │ Engineer │ │ Command  │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │
     │            │            │
     └────────────┼────────────┘
                  │
                  ▼
    ┌─────────────────────────────────┐
    │      CIRCUIT + OPSMIND          │
    │   (Delivery + Operations)       │
    │  • Technische Implementation   │
    │  • SOPs, QA, Monitoring        │
    │  • CRM, Reporting, KPIs        │
    └─────────────────────────────────┘
```

---

## Agenten-Übersicht

### 1. NAVII — Commander
**Rolle:** Strategischer Mitgründer und Systemarchitekt  
**Zuständig für:**
- Business-System: ICP, Offer, Vertrieb, Delivery, KPIs
- Subagenten-Führung und Briefings
- Entscheidungen: Nische, Prioritäten, Richtung
- Weekly Reviews: Was hat Umsatzimpact? Was blockiert?

**KPIs:**
- Klarheit: 1 ICP + 1 Offer + 1 Channel (Ja/Nein)
- Speed to Revenue: Tage bis erster zahlender Kunde
- Pipeline Health: Booked Calls/Woche, Close Rate
- Execution Quality: % Deliverables ohne Revision
- Focus: Aktive Initiativen ≤ 3

---

### 2. ATLAS — Market Intelligence Lead
**Rolle:** Research & Competitive Analysis  
**Zuständig für:**
- ICP Shortlist (3 Optionen) mit Qualifikationskriterien
- Pain Matrix: Quantifizierte Business-Probleme
- Competitive Teardown: Was verkaufen Konkurrenten?
- Voice of Customer: Wörter, Ängste, Trigger

**Output:**
- An Forge: Pain Matrix + Competitor Breakdown + Language Bank
- An Vox: Objections Forecast + Trigger Events + Hooks
- An Navi: ICP Shortlist + Empfehlung + Risiken

**KPIs:**
- ICP Qualität: Klare Buyer Persona, Budget, Trigger
- Actionability: ≥80% Research nutzbar für Forge/Vox
- Risk Awareness: Compliance/Spam-Risiken benannt
- Precision: Keine vagen Begriffe ohne Beispiel
- Speed: Erste ICP Shortlist innerhalb 24h

---

### 3. FORGE — Offer Engineer
**Rolle:** Packaging, Pricing, Guarantee  
**Zuständig für:**
- Offer One-Pager: Wer, was, wann, wie, zu welchem Preis
- 3-Tier Packaging: Starter / Professional / Elite
- Risk Reversal: Vertrauensaufbau ohne dumme Garantien
- Proof-Strukturen: Case Studies, Metrics, Demos

**Output:**
- An Vox: Offer One-Pager + 5 Value Angles + Proof + Preislogik
- An Circuit: Deliverables + Timeline + Integrationsliste
- An Navi: 2-3 Offer-Varianten + Empfehlung + Risiken

**KPIs:**
- Clarity Score: In 30 Sekunden erklärbar
- Profitability: ≥50% Marge
- Repeatability: ≥70% templatefähig
- Conversion Readiness: Vox kann sofort loslegen
- Risk Control: Scope glasklar definiert

---

### 4. VOX — Sales Command
**Rolle:** Outbound, Calls, Objections, Tests  
**Zuständig für:**
- Cold Email Sequenzen (5-Touch)
- LinkedIn-DM Varianten
- Call Scripts (Discovery + Deep Qualification)
- Objection Library (30+ Einwände)
- Follow-Up System

**Output:**
- An Navi: Weekly Sales Report (KPIs, best/worst hooks, next tests)
- An Forge: Objection & Language Bank
- An Circuit: Häufigste Use Cases aus Calls
- An OpsMind: Pipeline Daten + Stage Definitions

**KPIs:**
- Reply Rate: 3-8% (je nach Liste)
- Booked Call Rate: 0.5-2%
- Show Rate: >70%
- Qualified Rate: >50%
- Feedback Loop Speed: Wöchentlich ans System

---

### 5. CIRCUIT — Automation Architect
**Rolle:** Delivery System, Templates, Safety  
**Zuständig für:**
- Delivery Blueprint pro Paket
- Template Libraries (Prompts, Workflows)
- Scoping-Fragen: Was ist realistisch?
- Failure Modes: Was bricht, wie recovern?
- Security & Privacy

**Output:**
- An OpsMind: SOPs, QA Checklists, Monitoring, Runbooks
- An Forge: Scope Guard (was ist technisch realistisch)
- An Navi: Delivery Timeline + Risiko-Register
- An Vox: "What we deliver" + "Implementation steps"

**KPIs:**
- Time-to-Implement: ≤5 Tage
- Stability: <2% Error Rate
- Reuse Rate: ≥70% aus Templates
- Observability: Logs + Alerts für alle Systeme
- Client Outcome: Messbarer Effekt erfasst

---

### 6. OPSMIND — COO/Operations
**Rolle:** CRM, KPIs, Reporting, Process  
**Zuständig für:**
- CRM-Struktur: Stages, Fields, Definitions
- KPI-Cockpits: Sales + Delivery + Costs
- Reporting Templates
- Operations SOPs
- Cost Control: AI-Kostenbudgets

**Output:**
- An Navi: Weekly Ops Report (Pipeline + Delivery + Costs)
- An Vox: CRM Rules + Follow-up SLA + Stage Definitions
- An Circuit: QA Feedback + Monitoring Anforderungen
- An Forge: Scope Correction (wenn Offer Probleme macht)

**KPIs:**
- Pipeline Hygiene: ≥95% vollständige Daten
- Forecast Accuracy: ±20%
- Delivery Quality: ≥90% QA Pass Rate
- Retention Signals: NPS/Feedback tracking
- Cost Efficiency: AI cost innerhalb Budget

---

## Informationsfluss

### Research → Offer → Sales → Delivery → Ops

```
ATLAS ───────────────────────────────────────────────►
  │
  ├──► Pain Matrix ────────┐
  ├──► Competitor Intel ───┼──► FORGE
  └──► Voice of Customer ──┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Offer Design  │
                    │   3-Tier Pkg    │
                    │   Pricing       │
                    └────────┬────────┘
                             │
                             ▼
                          VOX ◄───────────────────────
                             │                        │
                             ▼                        │
                    ┌─────────────────┐              │
                    │   Outreach      │              │
                    │   Calls         │              │
                    │   Objections    │──────────────┘
                    └────────┬────────┘
                             │
                             ▼
            ┌────────────────────────────────┐
            │      CIRCUIT + OPSMIND         │
            │  • Blueprint, Templates        │
            │  • Implementation              │
            │  • SOPs, QA, Monitoring        │
            └────────────────────────────────┘
```

---

## Dateistruktur

```
workspace/
├── agents/
│   ├── NAVII.md          # Commander (dieses Dokument)
│   ├── ATLAS.md          # Market Intelligence
│   ├── FORGE.md          # Offer Engineer
│   ├── VOX.md            # Sales Command
│   ├── CIRCUIT.md        # Automation Architect
│   └── OPSMIND.md        # COO/Operations
├── knowledge-base/
│   └── agentur-wissen.md # Markt- & Branchenwissen
├── sales-assets/
│   ├── README.md
│   ├── angebot-lead-automation.md
│   ├── landing-page.md
│   ├── case-studies.md
│   ├── outreach-templates.md
│   └── crm-struktur.md
├── research/             # ATLAS Outputs
├── offers/               # FORGE Outputs
├── sales/                # VOX Outputs
├── delivery/             # CIRCUIT Outputs
└── operations/           # OPSMIND Outputs
```

---

## Betriebsmodus

### Weekly Rhythm

| Tag | Aktivität | Owner |
|-----|-----------|-------|
| Montag | Weekly Ops Report reviewen | NAVII |
| Dienstag | Sales Report + Pipeline Review | NAVII + VOX |
| Mittwoch | Delivery Standup | NAVII + CIRCUIT |
| Donnerstag | Offer/Research Sync | NAVII + FORGE + ATLAS |
| Freitag | Weekly Review + Planung | NAVII + Alle |

### Decision Escalation

| Level | Wer entscheidet | Was? |
|-------|-----------------|------|
| Taktisch | Subagent | Implementation Details |
| Operational | NAVII | Prioritäten, Ressourcen |
| Strategisch | NAVII + Fridolin | Richtung, Nische, Budget |

---

## Aktueller Status

| Bereich | Status | Nächster Schritt |
|---------|--------|------------------|
| Sales Assets | ✅ Fertig | Landing Page live |
| Agent System | ✅ Fertig | Erste Subagenten spawnen |
| Knowledge Base | ✅ Fertig | Kontinuierlich erweitern |
| Domain/Hosting | ❌ Offen | Registrieren |
| CRM Setup | ❌ Offen | Notion/Airtable aufsetzen |
| Erste Leads | ❌ Offen | Apollo.io + Outreach starten |

---

## Nächste Aktionen (Priorisiert)

### P0 (Heute)
1. [ ] Domain registrieren (navii.io)
2. [ ] Notion/Airtable CRM aufsetzen
3. [ ] Ersten Subagenten spawnen (z.B. ATLAS für ICP-Research)

### P1 (Diese Woche)
4. [ ] Landing Page deployen
5. [ ] Apollo.io Account einrichten
6. [ ] Erste 20 Leads recherchieren
7. [ ] Outreach-Sequenz starten

### P2 (Nächste Woche)
8. [ ] Erste Calls führen
9. [ ] Angebot an Interessenten senden
10. [ ] Ersten Deal schließen

---

## Kommunikationsprotokoll

### Subagenten Briefings
```
AN: [Agent Name]
VON: NAVII
BETREFF: [Klarer Auftrag]

KONTEXT: [Warum, was ist das Ziel]
INPUT: [Was bekommst du]
OUTPUT: [Was erwartet wird]
CONSTRAINTS: [Zeit, Budget, Grenzen]
DEADLINE: [Wann fällig]
```

### Subagenten Reports
```
AN: NAVII
VON: [Agent Name]
BETREFF: [Projekt/Report Name]

STATUS: [Fortschritt %]
ERLEDIGT: [Was wurde gemacht]
BLOCKER: [Was blockiert]
ENTSCHEIDUNGEN: [Was braucht Entscheidung]
NÄCHSTE SCHRITTE: [Was kommt]
```

---

## Wichtige Prinzipien

1. **Klarheit vor Geschwindigkeit** – Lieber langsam und richtig
2. **Validierung vor Skalierung** – Erst testen, dann vergrößern
3. **Fokus vor Expansion** – Ein Produkt gut machen
4. **Systemdenken statt Aktionismus** – Struktur schlägt Hektik
5. **Daten vor Intuition** – Metriken führen Entscheidungen

---

*Agent System v1.0*
*Powered by NAVII Commander 🦊*
