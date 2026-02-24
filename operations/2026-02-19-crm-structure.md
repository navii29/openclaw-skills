# CRM-Struktur & KPI-Cockpits

**Erstellt von:** OPSMIND (COO/Operations)  
**Datum:** 2026-02-19  
**Bericht an:** NAVII (CEO)

---

## 📋 Übersicht

Dieses Dokument definiert die vollständige CRM-Struktur, Sales Pipeline, Delivery Tracking und Kostenkontrolle für den operativen Betrieb.

---

## 1. Pipeline Stages: New Lead → Closed Won/Lost

### Stage 0: NEW LEAD
| Attribut | Wert |
|----------|------|
| **Zweck** | Initialer Eingang aller neuen Kontakte |
| **SLA** | 4 Stunden (First Response) |
| **Owner** | Sales Development Rep (SDR) |
| **Exit Criteria** | Lead qualifiziert durch BANT-Framework |

#### Exit Criteria Checklist:
- [ ] Budget bestätigt (mind. €5K Projektgröße)
- [ ] Authority identifiziert (Decision Maker benannt)
- [ ] Need validiert (Pain Point dokumentiert)
- [ ] Timeline definiert (Start innerhalb 6 Monate)

---

### Stage 1: QUALIFIED LEAD
| Attribut | Wert |
|----------|------|
| **Zweck** | Qualifizierte Leads für aktive Bearbeitung |
| **SLA** | 24 Stunden (Discovery Call gebucht) |
| **Owner** | Account Executive (AE) |
| **Exit Criteria** | Discovery Call durchgeführt & Bedarf verifiziert |

#### Exit Criteria Checklist:
- [ ] Discovery Call absolviert
- [ ] Use Case dokumentiert
- [ ] Technical Requirements erfasst
- [ ] Competitor Landscape notiert
- [ ] Next Steps vereinbart

---

### Stage 2: PROPOSAL SENT
| Attribut | Wert |
|----------|------|
| **Zweck** | Angebot versendet, in Verhandlung |
| **SLA** | 48 Stunden (Follow-up nach Sendung) |
| **Owner** | Account Executive (AE) |
| **Exit Criteria** | Feedback zum Angebot erhalten |

#### Exit Criteria Checklist:
- [ ] Angebot versendet
- [ ] Preisgespräch geführt
- [ ] Objektionen dokumentiert
- [ ] Timeline für Entscheidung vereinbart
- [ ] Technical Validation abgeschlossen (falls nötig)

---

### Stage 3: NEGOTIATION
| Attribut | Wert |
|----------|------|
| **Zweck** | Vertragsverhandlung, Legal/Procurement |
| **SLA** | 5 Werktage (Vertragsentwurf oder Update) |
| **Owner** | Account Executive + Legal |
| **Exit Criteria** | Vertrag unterschrieben oder final abgelehnt |

#### Exit Criteria Checklist:
- [ ] Vertragsbedingungen finalisiert
- [ ] Legal Review abgeschlossen
- [ ] Security Review bestanden (falls nötig)
- [ ] Procurement Approval erhalten
- [ ] Unterschrift oder dokumentierter Abbruch

---

### Stage 4: CLOSED WON
| Attribut | Wert |
|----------|------|
| **Zweck** | Gewonnener Deal, Übergabe an Delivery |
| **SLA** | 24 Stunden (Handover an Delivery) |
| **Owner** | Account Executive → Delivery Manager |
| **Exit Criteria** | N/A (Final Stage) |

#### Auto-Trigger bei Entry:
- [ ] Deal-Größe in Forecast aktualisiert
- [ ] Kickoff-Call gebucht (innerhalb 1 Woche)
- [ ] Delivery Team notifiziert
- [ ] Projekt-Ordner erstellt

---

### Stage 5: CLOSED LOST
| Attribut | Wert |
|----------|------|
| **Zweck** | Verlorener Deal mit Learnings |
| **SLA** | 48 Stunden (Lost Reason dokumentiert) |
| **Owner** | Account Executive |
| **Exit Criteria** | N/A (Final Stage) |

#### Required bei Entry:
- [ ] Lost Reason ausgewählt (Price, Timing, Features, Competitor, No Budget)
- [ ] Learning dokumentiert
- [ ] Re-engagement Datum gesetzt (mindestens 6 Monate)

---

## 2. Required Fields pro Stage

### Stage 0: NEW LEAD (Required)
| Field | Typ | Beschreibung |
|-------|-----|--------------|
| `lead_source` | Dropdown | Web, Referral, Event, Cold Outreach, Partner |
| `company_name` | Text | Firmenname |
| `contact_email` | Email | Primärer Kontakt |
| `contact_phone` | Phone | Telefonnummer |
| `industry` | Dropdown | SaaS, E-Commerce, Healthcare, Finance, Other |
| `created_date` | Date | Automatisch |
| `sdr_owner` | User | Zugewiesener SDR |

### Stage 1: QUALIFIED LEAD (Required + Stage 0)
| Field | Typ | Beschreibung |
|-------|-----|--------------|
| `ae_owner` | User | Zugewiesener Account Executive |
| `discovery_call_date` | Date | Datum des Discovery Calls |
| `estimated_budget` | Currency | Geschätztes Budget (€) |
| `decision_maker` | Text | Name des Decision Makers |
| `use_case_summary` | Textarea | Zusammenfassung Use Case |
| `technical_requirements` | Multi-select | API, Integration, Custom Dev, Support |
| `competitors` | Multi-select | Liste der Wettbewerber |
| `expected_close_date` | Date | Geschätztes Closing-Datum |

### Stage 2: PROPOSAL SENT (Required + vorherige)
| Field | Typ | Beschreibung |
|-------|-----|--------------|
| `proposal_sent_date` | Date | Datum der Angebotsversendung |
| `proposal_value` | Currency | Angebotswert (€) |
| `proposal_version` | Text | Versionsnummer (v1.0, v1.1, etc.) |
| `proposal_notes` | Textarea | Spezifische Angebotsdetails |
| `feedback_received` | Boolean | Feedback vom Kunden erhalten |
| `next_action_date` | Date | Nächstes geplantes Follow-up |

### Stage 3: NEGOTIATION (Required + vorherige)
| Field | Typ | Beschreibung |
|-------|-----|--------------|
| `contract_sent_date` | Date | Vertragsversand-Datum |
| `negotiation_notes` | Textarea | Verhandlungspunkte |
| `legal_review_status` | Dropdown | Pending, In Review, Approved, Rejected |
| `security_review_status` | Dropdown | N/A, Pending, In Review, Approved |
| `procurement_contact` | Text | Ansprechpartner Procurement |

### Stage 4: CLOSED WON (Required + vorherige)
| Field | Typ | Beschreibung |
|-------|-----|--------------|
| `closed_date` | Date | Abschlussdatum |
| `final_contract_value` | Currency | Finaler Vertragswert (€) |
| `contract_start_date` | Date | Vertragsbeginn |
| `contract_end_date` | Date | Vertragsende (bei Subscription) |
| `delivery_manager` | User | Zugewiesener Delivery Manager |
| `kickoff_date` | Date | Geplanter Kickoff-Termin |
| `payment_terms` | Dropdown | Net 14, Net 30, Net 60, Prepaid |

### Stage 5: CLOSED LOST (Required)
| Field | Typ | Beschreibung |
|-------|-----|--------------|
| `closed_date` | Date | Abschlussdatum |
| `lost_reason` | Dropdown | Price, Timing, Features, Competitor, No Budget, Other |
| `lost_reason_details` | Textarea | Detaillierte Begründung |
| `competitor_won` | Text | Gewonnener Wettbewerber (falls zutreffend) |
| `re_engagement_date` | Date | Geplantes Re-Engagement |
| `lessons_learned` | Textarea | Learnings für zukünftige Deals |

---

## 3. Weekly Sales Dashboard Template

### 📊 Dashboard: SALES PERFORMANCE (Woche ending: ___________)

#### Section A: Pipeline Overview
| Metric | Diese Woche | Letzte Woche | Veränderung | Ziel |
|--------|-------------|--------------|-------------|------|
| Neue Leads | | | | 25/Woche |
| Qualifizierte Leads | | | | 10/Woche |
| Proposals Sent | | | | 5/Woche |
| Deals in Negotiation | | | | - |
| Closed Won (Anzahl) | | | | 3/Woche |
| Closed Won (€) | | | | €50K/Woche |
| Closed Lost (Anzahl) | | | | < 30% |
| Win Rate % | | | | > 70% |

#### Section B: Pipeline by Stage (Wert in €)
```
NEW LEAD:          €__________ (___ Deals)
QUALIFIED LEAD:    €__________ (___ Deals)
PROPOSAL SENT:     €__________ (___ Deals)
NEGOTIATION:       €__________ (___ Deals)
────────────────────────────────────────────
PIPELINE TOTAL:    €__________
WEIGHTED PIPELINE: €__________
```

#### Section C: Top Deals (by Value)
| Rang | Unternehmen | Stage | Wert (€) | Close Probability | Expected Close |
|------|-------------|-------|----------|-------------------|----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

#### Section D: Sales Activity (Diese Woche)
| Aktivität | Anzahl | Ziel | Status |
|-----------|--------|------|--------|
| Outreach Calls | | 50 | |
| Discovery Calls | | 10 | |
| Demos | | 5 | |
| Proposals Created | | 5 | |
| Follow-ups | | 30 | |
| Meetings | | 8 | |

#### Section E: Lead Source Performance
| Source | Leads | Qualified | Conversion % | Won Deals | Revenue |
|--------|-------|-----------|--------------|-----------|---------|
| Web | | | | | |
| Referral | | | | | |
| Event | | | | | |
| Cold Outreach | | | | | |
| Partner | | | | | |

#### Section F: Forecast (Next 30/60/90 Days)
| Zeitraum | Pipeline | Weighted | Commit | Best Case |
|----------|----------|----------|--------|-----------|
| Next 30 Days | | | | |
| Next 60 Days | | | | |
| Next 90 Days | | | | |

#### Section G: Blockers & Action Items
| Issue | Owner | Due Date | Status |
|-------|-------|----------|--------|
| | | | |
| | | | |

---

## 4. Weekly Delivery Dashboard Template

### 📊 Dashboard: DELIVERY PERFORMANCE (Woche ending: ___________)

#### Section A: Project Portfolio Overview
| Status | Anzahl | % Gesamt | Gesamtwert (€) |
|--------|--------|----------|----------------|
| 🟢 On Track | | | |
| 🟡 At Risk | | | |
| 🔴 Off Track | | | |
| ⏸️ On Hold | | | |
| ✅ Completed | | | |
| **TOTAL** | | 100% | |

#### Section B: Active Projects Health Check
| Projekt | Kunde | PM | Status | Progress | Budget Used | Next Milestone | Risk Level |
|---------|-------|----|--------|----------|-------------|----------------|------------|
| | | | | % | % | | |
| | | | | % | % | | |
| | | | | % | % | | |
| | | | | % | % | | |

#### Section C: Milestone Tracking (Diese Woche)
| Milestone | Projekt | Geplant | Tatsächlich | Status | Owner |
|-----------|---------|---------|-------------|--------|-------|
| | | | | | |
| | | | | | |
| | | | | | |

#### Section D: Resource Utilization
| Team Member | Role | Capacity | Allocated | Utilization % | Projects |
|-------------|------|----------|-----------|---------------|----------|
| | | 40h | h | % | |
| | | 40h | h | % | |
| | | 40h | h | % | |
| | | 40h | h | % | |

#### Section E: Support & Incidents
| Typ | Eröffnet | Geschlossen | Backlog | Avg Resolution Time |
|-----|----------|-------------|---------|---------------------|
| P1 - Critical | | | | < 4h |
| P2 - High | | | | < 24h |
| P3 - Medium | | | | < 72h |
| P4 - Low | | | | < 5 Tage |
| **TOTAL** | | | | |

#### Section F: Customer Satisfaction (CSAT)
| Metric | Diese Woche | MTD | Ziel |
|--------|-------------|-----|------|
| CSAT Score | /5 | /5 | > 4.5 |
| NPS | | | > 50 |
| Response Time (Avg) | h | h | < 4h |
| Resolution Time (Avg) | h | h | < 24h |

#### Section G: Upcoming Go-Lives (Next 30 Days)
| Projekt | Kunde | Go-Live Date | Status | Checklist Complete |
|---------|-------|--------------|--------|-------------------|
| | | | | % |
| | | | | % |
| | | | | % |

#### Section H: Financials (Delivery)
| Metric | Budget | Actual | Variance | Forecast |
|--------|--------|--------|----------|----------|
| Projekt-A (€) | | | | |
| Projekt-B (€) | | | | |
| Projekt-C (€) | | | | |
| **Total Projects** | | | | |
| Support Costs | | | | |
| **Delivery P&L** | | | | |

#### Section I: Blockers & Escalations
| Issue | Projekt | Impact | Owner | Mitigation | Status |
|-------|---------|--------|-------|------------|--------|
| | | | | | |
| | | | | | |

---

## 5. Cost Tracking Budget (AI-Kostenlimits)

### 💰 AI COST CONTROL FRAMEWORK

#### 5.1 Monatliche Budget-Limits

| Kategorie | Budget Limit | Warnschwelle (80%) | Critical (100%) | Owner |
|-----------|--------------|-------------------|-----------------|-------|
| **AI API Calls (LLM)** | €2,000 | €1,600 | €2,000 | CTO/Operations |
| **AI Infrastructure** | €1,000 | €800 | €1,000 | DevOps |
| **AI Tools & Subscriptions** | €500 | €400 | €500 | Operations |
| **AI Training/Finetuning** | €1,000 | €800 | €1,000 | ML Engineer |
| **AI Monitoring & Logging** | €200 | €160 | €200 | DevOps |
| **Puffer/Emergency** | €300 | - | - | CTO |
| **TOTAL AI BUDGET** | **€5,000** | **€4,000** | **€5,000** | **COO** |

#### 5.2 Daily Limits & Rate Limiting

| Service | Daily Limit | Rate Limit | Cost/1K Calls | Action bei Limit |
|---------|-------------|------------|---------------|------------------|
| OpenAI GPT-4o | €100/Tag | 100 RPM | €0.01-0.03 | Queue + Notify |
| OpenAI GPT-4o-mini | €50/Tag | 200 RPM | €0.001-0.003 | Auto-downgrade |
| Anthropic Claude | €50/Tag | 50 RPM | €0.008-0.024 | Queue + Notify |
| Embeddings | €20/Tag | - | €0.0001 | Batch processing |
| Image Generation | €30/Tag | - | €0.04-0.08 | Approval required |

#### 5.3 Cost Allocation by Team/Project

| Team/Project | Monatliches Limit | aktueller Verbrauch | % Budget |
|--------------|-------------------|---------------------|----------|
| Product/Dev Core | €1,500 | | |
| Customer Support AI | €800 | | |
| Sales/Marketing AI | €600 | | |
| Internal Operations | €500 | | |
| R&D/Experiments | €600 | | |
| Infrastructure | €1,000 | | |

#### 5.4 Cost Monitoring Alerts

```yaml
Alert_Levels:
  INFO:
    - threshold: 50% of daily limit
    - action: Log only
    - notify: None
    
  WARNING:
    - threshold: 80% of daily limit OR 80% of monthly budget
    - action: Email + Slack
    - notify: Team Lead + Operations
    
  CRITICAL:
    - threshold: 95% of daily limit OR 90% of monthly budget
    - action: Immediate notification + Auto-throttling
    - notify: CTO + COO + CEO
    
  EMERGENCY:
    - threshold: 100% of any limit
    - action: Service suspension + Emergency call
    - notify: All Leadership + Finance
```

#### 5.5 Weekly Cost Report Template

```
═══════════════════════════════════════════════════════════════
  AI COST REPORT - Week ending: [DATE]
═══════════════════════════════════════════════════════════════

📊 WEEKLY SUMMARY
────────────────────────────────────────────────────────────────
Budget Spent:        €________ / €1,250 (weekly prorated)
Budget Remaining:    €________
Projected Monthly:   €________ (vs. €5,000 limit)
Variance:            €________ (___% over/under)

📈 USAGE BY SERVICE
────────────────────────────────────────────────────────────────
OpenAI GPT-4o:       €________ (___%)
OpenAI GPT-4o-mini:  €________ (___%)
Anthropic Claude:    €________ (___%)
Embeddings:          €________ (___%)
Image Gen:           €________ (___%)
Other:               €________ (___%)

🏢 USAGE BY TEAM
────────────────────────────────────────────────────────────────
Product/Dev:         €________ (___%)
Support AI:          €________ (___%)
Sales/Marketing:     €________ (___%)
Operations:          €________ (___%)
R&D:                 €________ (___%)

🚨 ANOMALIES & ALERTS
────────────────────────────────────────────────────────────────
[ ] Spike detected on [DAY]: €_____ (___% over average)
[ ] Unusual pattern: _______________________________
[ ] Service near limit: ____________________________

✅ ACTIONS TAKEN
────────────────────────────────────────────────────────────────
1. ________________________________________________
2. ________________________________________________

📋 NEXT WEEK FORECAST
────────────────────────────────────────────────────────────────
Expected Usage: €________
Risk Level: [LOW / MEDIUM / HIGH]
Recommendations: _________________________________

═══════════════════════════════════════════════════════════════
Report generated by: OPSMIND
Next review: [DATE + 7 days]
═══════════════════════════════════════════════════════════════
```

#### 5.6 Cost Optimization Rules

| # | Regel | Trigger | Action | Owner |
|---|-------|---------|--------|-------|
| 1 | Auto-downgrade | Token count > 4K | Switch GPT-4o → GPT-4o-mini | System |
| 2 | Batch jobs | Non-urgent processing | Schedule off-peak hours | DevOps |
| 3 | Caching | Repeated queries | Cache 24h where possible | Engineering |
| 4 | Approval gate | Single request > €50 | Require manual approval | CTO |
| 5 | Model selection | Default for new features | Start with cheapest viable | Engineering |
| 6 | Review cycle | Monthly | Optimize prompts for efficiency | ML Engineer |

#### 5.7 Emergency Procedures

**Bei Erreichen des monatlichen Limits (€5,000):**

1. **Immediate (0-1h):**
   - Alle nicht-kritischen AI-Services pausieren
   - Notfall-Channel (Slack/Discord) benachrichtigen
   - Finance Team informieren

2. **Short-term (1-24h):**
   - CTO/COO entscheiden über Budget-Erhöhung
   - Kritische Services whitelisten
   - Kunden-Impact bewerten

3. **Medium-term (24-72h):**
   - Wurzelursache analysieren
   - Kostenoptimierungsplan erstellen
   - Neue Limits kommunizieren

---

## 📎 Anhänge

### A. Quick Reference: SLA Matrix

| Stage | Response | Next Action | Total Cycle Time |
|-------|----------|-------------|------------------|
| New Lead | 4h | 24h | - |
| Qualified | - | 24h | 2-7 Tage |
| Proposal | - | 48h | 7-14 Tage |
| Negotiation | - | 5 Tage | 14-30 Tage |
| Closed Won | 24h | Handover | - |

### B. Revenue Recognition Rules
- Subscription: Monatlich über Vertragslaufzeit
- Project: Milestone-basiert oder linear über Dauer
- Support: Monatlich im Voraus

### C. Approval Matrix

| Aktion | Limit | Approver |
|--------|-------|----------|
| Discount < 10% | - | AE |
| Discount 10-20% | - | Sales Manager |
| Discount > 20% | - | CEO |
| Custom Terms | - | Legal + CEO |
| AI Budget Override | €500+ | CTO + COO |

---

## 📝 Änderungshistorie

| Version | Datum | Autor | Änderung |
|---------|-------|-------|----------|
| 1.0 | 2026-02-19 | OPSMIND | Initial Release |

---

**Nächste Review:** 2026-03-19 (monatlich)

**Dokument Owner:** OPSMIND (COO/Operations)  
**Genehmigt durch:** NAVII (CEO) - [Pending Signature]
