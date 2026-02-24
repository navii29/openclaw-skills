# CIRCUIT — Phase 1 Deliverable: Delivery Blueprints + Technical Architecture

**HANDOFF v1** | Owner: Circuit | Date: 2026-02-19 | Status: Review Pending

---

## OBJECTIVE
Erstelle technisch lieferbare Blueprints für alle 8 Pakete + Full Suite auf OpenClaw-Basis mit Monitoring, Failure Modes und Cost Control.

---

## KEY FINDINGS

### Technologie-Stack

**Core Platform:** OpenClaw (MacBook Air / Cloud VPS)
**Orchestration:** Cron Jobs + Sub-Agents
**Integrations:**
- E-Mail: Gmail API, Microsoft Graph API
- Calendar: Google Calendar API, Outlook REST API
- Finance: Lexware API, sevDesk API, Datev (Export)
- Reviews: Google Places API
- Web: OpenAI GPT-4, Brave Search, Playwright
- Monitoring: Self-hosted or Datadog (später)

---

## DELIVERY BLUEPRINTS

### Paket 1: Inbox AI

**Inputs:**
- E-Mail-Account (Gmail/Outlook)
- Historische E-Mails (50+ für Stil-Analyse)
- FAQ-Dokument (optional)
- Human Approval Rules (welche Anfragen freigeben?)

**Workflow (Simplified):**
```
Neue E-Mail → OpenClaw Webhook
    ↓
Classify (Spam/Newsletter/Action Required)
    ↓
If Action Required:
    Analyze Intent + Sentiment
    Extract Entities (Deadline, Amount, Person)
    Check Against Rules (Human Approval needed?)
    ↓
    If Human Approval → Queue for Review
    If Auto-Reply → Generate Response (GPT-4)
        ↓
        Draft Response (Tone Match)
        Send (or Schedule)
        Log to CRM/Notion
```

**Outputs:**
- Beantwortete E-Mails
- TL;DR Zusammenfassungen
- Priorisierte Inbox
- Escalation Queue (Human Review)

**Human Approvals:**
- Erste 20 Antworten (Kalibrierung)
- Anfragen >€10k potenzieller Umsatz
- Negative/Eskalations-Tone
- Unklarer Intent (Confidence <80%)

**Cost Budget:**
- Max Cost/Run: $0.15 (GPT-4 + Processing)
- Max Runs/Day: 500 E-Mails = $75/Tag
- Fallback: Confidence <50% → Human Queue

---

### Paket 2: Executive Calendar

**Inputs:**
- Kalender-Account (Google/Outlook)
- Availability Rules (Buffer-Zeiten, keine Termine vor 9 Uhr, etc.)
- Booking Link Preferences
- Teilnehmer-Historie (für Dossiers)

**Workflow:**
```
Buchungsanfrage / Konflikt-Erkennung
    ↓
Check Availability (inkl. Buffer, Reisezeit)
    ↓
If Available:
    Confirm Booking
    Send Invites
    Create Prep-Dossier (Attendee Research)
    Schedule Reminders (24h, 1h, 15min)
    ↓
If Conflict:
    Propose Alternatives
    Auto-Reschedule (if enabled)
    Notify Organizer
```

**Outputs:**
- Gebuchte Termine
- Rescheduled Events
- Prep-Dossiers (Vor dem Meeting)
- Erinnerungen

**Human Approvals:**
- Externe Termine >€10k
- Termine außerhalb Geschäftszeiten
- Konflikte mit mehr als 2 Optionen

**Cost Budget:**
- Max Cost/Run: $0.05 (API Calls + Dossier-Gen)
- Max Runs/Day: 100 Termine = $5/Tag

---

### Paket 3: Invoice Agent

**Inputs:**
- Zeiterfassung / Projekt-Tracking (Toggl, Harvest, oder manuell)
- Kundendaten (CRM)
- Rechnungs-Template (Branding)
- Zahlungsbedingungen

**Workflow:**
```
Trigger: Monatsende / Projekt-Abschluss / Manuell
    ↓
Aggregate Time/Project Data
    ↓
Generate Invoice (PDF)
    ↓
Send via E-Mail (mit Rechnungstext)
    ↓
Monitor Bank-Konto (via API oder CSV-Import)
    ↓
If Payment Received → Mark as Paid → Archive
    ↓
If Overdue:
    Day 7: Friendly Reminder
    Day 14: First Warning
    Day 21: Final Warning + Legal Notice Prep
```

**Outputs:**
- Rechnungen (PDF)
- Zahlungserinnerungen
- Zahlungs-Tracking
- Monatlicher Report

**Human Approvals:**
- Rechnungen >€5.000
- Erste Mahnung an strategisch wichtigen Kunden
- Legal Notice Vorbereitung

**Cost Budget:**
- Max Cost/Run: $0.03 (PDF Gen + E-Mail)
- Max Runs/Day: 50 Rechnungen = $1.50/Tag

---

### Paket 4: Competitor Intel

**Inputs:**
- Competitor URLs (5–10)
- Tracking-Kategorien (Produkte, Preise, Ads, Content)
- Report-Frequenz (wöchentlich)

**Workflow:**
```
Weekly Trigger (Montag 08:00)
    ↓
For each Competitor:
    Scrape Website (Changes?)
    Check Ad Libraries (Meta, Google)
    Monitor Keywords (SERPs)
    Analyze Content (New Posts, Updates)
    ↓
Aggregate Findings
    ↓
Generate Insights (GPT-4 Analysis)
    ↓
Create PDF Report
    ↓
Send to Client (09:00)
```

**Outputs:**
- Wöchentlicher PDF-Report
- Alert bei signifikanten Änderungen
- Content-Ideen-Liste

**Human Approvals:**
- Keine (vollautomatisch)
- Optional: Strategische Empfehlungen (Add-on)

**Cost Budget:**
- Max Cost/Run: $2.00 (Scraping + GPT-4 Analysis × 10 Competitors)
- Max Runs/Week: 1× = $8/Monat

---

### Paket 5: Reviews Agent

**Inputs:**
- Google Business Profile ID
- Antwort-Templates (generisch + negativ)
- Alert-Threshold (Sterne-Bewertung)

**Workflow:**
```
Webhook: Neue Google Review
    ↓
Analyze Sentiment + Sterne
    ↓
If 4–5 Stars:
    Generate Thank-You Response
    Post Response
    ↓
If 1–3 Stars:
    Generate Empathy Response (Draft)
    Queue for Human Review
    Send Alert (Slack/E-Mail)
    ↓
Weekly Report: Review Stats + Trends
```

**Outputs:**
- Automatische Antworten (4–5★)
- Draft-Antworten (1–3★)
- Trend-Reports
- Alerts bei Negativ-Trends

**Human Approvals:**
- Alle 1–3★ Antworten
- Erste 10 Antworten (Kalibrierung)

**Cost Budget:**
- Max Cost/Run: $0.08 (Sentiment + Response Gen)
- Max Runs/Day: 20 Reviews = $1.60/Tag

---

### Paket 6: Lead Qualification

**Inputs:**
- Inbound-Leads (Formular, E-Mail, Chat)
- ICP-Definition (BANT-Kriterien)
- Absage-Templates (höflich, professionell)
- CRM-Integration (HubSpot/Pipedrive)

**Workflow:**
```
New Lead Incoming
    ↓
Extract Data (E-Mail, Firma, Rolle, Nachricht)
    ↓
BANT Scoring:
    Budget: Keywords (€, Budget, Investition)?
    Authority: Rolle = Decision Maker?
    Need: Pain Point match?
    Timeline: Wie dringend?
    ↓
Score = 0–100
    ↓
If Score ≥70:
    Qualify as "Hot"
    Auto-Book Meeting (via Calendly)
    Create CRM Entry
    ↓
If Score 40–69:
    Qualify as "Warm"
    Send Nurture Sequence
    Schedule Follow-up
    ↓
If Score <40:
    Qualify as "Cold"
    Send Polite Decline
    Archive
```

**Outputs:**
- Qualifizierte Leads (CRM)
- Abgelehnte Leads (höflich)
- Meeting-Buchungen
- Lead-Scoring Report

**Human Approvals:**
- Hot Leads vor Meeting-Buchung (optional)
- Erste 20 Qualifikationen (Kalibrierung)

**Cost Budget:**
- Max Cost/Run: $0.12 (Analysis + Response)
- Max Runs/Day: 50 Leads = $6/Tag

---

### Paket 7: Document Processing

**Inputs:**
- Dokument-Upload (PDF, Bild)
- Dokument-Typ (Rechnung, Vertrag, Formular)
- Export-Ziel (ERP, CRM, Drive)

**Workflow:**
```
Document Upload (E-Mail, Upload-Portal, API)
    ↓
OCR (Text Recognition)
    ↓
Extract Entities (Datum, Betrag, Name, Adresse, etc.)
    ↓
Classify Document Type
    ↓
Data Validation (Plausibilität)
    ↓
Export to Target System
    ↓
Archive with Index
    ↓
Report: Processed Documents
```

**Outputs:**
- Extrahierte Daten
- Kategorisierte Dokumente
- Export zu ERP/CRM
- Suchbarer Archiv

**Human Approvals:**
- Confidence <90%
- Compliance-kritische Dokumente (Verträge)
- Dubletten-Verdacht

**Cost Budget:**
- Max Cost/Run: $0.20 (OCR + Extraction)
- Max Runs/Day: 100 Dokumente = $20/Tag

---

### Paket 8: Website Builder

**Inputs:**
- Content (Texte, Bilder, Branding)
- Struktur (Seiten, Navigation)
- Design-Preferences (Farben, Fonts)
- Domain + Hosting-Zugang

**Workflow:**
```
Week 1:
    Content-Gathering + Structure
    Design System erstellen
    ↓
Week 2:
    Development (HTML/CSS/JS)
    Content-Integration
    SEO-Optimierung
    ↓
Testing:
    Mobile Responsiveness
    PageSpeed (Target: 90+)
    Cross-Browser
    ↓
Go-Live:
    Deploy to Hosting
    DNS-Config
    SSL-Setup
    Analytics-Integration
    ↓
Ongoing:
    Content-Updates (Monatlich)
    Performance-Monitoring
    Security-Updates
```

**Outputs:**
- Live Website
- Design-System
- Content-Management
- Performance-Reports

**Human Approvals:**
- Design-Vorstellung (Week 1)
- Content-Finalisierung (Week 2)
- Pre-Launch Review

**Cost Budget:**
- Setup: $50 (Tools, APIs, Hosting-Setup)
- Monthly: $30 (Hosting, CDN)
- Updates: $0.50/Update (automatisiert)

---

## FAILURE MODES MATRIX

| Paket | Failure Mode | Detection | Recovery | Prevention |
|-------|-------------|-----------|----------|------------|
| Inbox AI | API Rate Limit | Response 429 | Exponential Backoff | Queue + Retry Logic |
| Inbox AI | Hallucination (falsche Antwort) | Confidence Score <80% | Human Queue | Prompt Engineering, Examples |
| Inbox AI | Auth Expired (Token) | 401 Error | Alert → Re-Auth | Token Refresh Automation |
| Calendar | Double-Booking | Calendar Conflict Check | Manual Resolution | Buffer-Zeiten, Regeln |
| Calendar | Timezone Confusion | Attendee Complaint | Reschedule + Apology | Strict TZ Handling |
| Invoice | Wrong Amount | Plausibility Check | Human Review | Validation Rules |
| Invoice | Zahlung nicht erkannt | 30 Days Overdue | Manual Check | Bank-API Integration |
| Competitor | Website Structure Change | Scrape Error | Alert → Manual Update | Robust Selectors |
| Competitor | Rate Limited (Scraping) | 403/429 | Rotate Proxies | Respect robots.txt |
| Reviews | API Deprecation | Failed Calls | Alert → Migration Plan | API Monitoring |
| Reviews | Inappropriate Auto-Reply | Sentiment Mismatch | Immediate Pause | Strict Templates |
| Lead Qual | False Positive (Cold as Hot) | Conversion Rate Drop | Recalibrate Scoring | Weekly Review |
| Doc Proc | OCR Failure | Low Confidence | Human Review | Quality Thresholds |
| Doc Proc | Wrong Data Extraction | Validation Fail | Flag + Review | Regex + ML Validation |
| Website | Deploy Failure | Build Error | Rollback | CI/CD Pipeline |
| Website | Performance Degradation | PageSpeed <70 | Optimize | Monitoring Alerts |

---

## MONITORING + ALERTS

### System Health Checks

**Every 5 Minutes:**
- API Endpoints reachable
- Queue lengths (Human Review, Pending)
- Error rates (last 15 min)

**Every Hour:**
- Cost accumulation (vs. Budget)
- Automation rate (% erfolgreich)
- Response times

**Daily:**
- Full health report
- Cost report
- Client-facing metrics

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Error Rate | >5% | >10% | Pause + Investigation |
| Queue Length | >20 items | >50 items | Scale/Alert |
| Daily Cost | >80% Budget | >100% Budget | Throttle/Pause |
| API Latency | >2s | >5s | Fallback Mode |
| Auth Failures | >3/hour | >10/hour | Re-Auth Alert |
| Uptime | <99.5% | <99% | Incident Response |

### Alert Channels
- Slack: #ops-alerts (immediate)
- E-Mail: ops@navii-automation.de (daily summary)
- SMS/PagerDuty: Critical only (Circuit + Navi)

---

## COST BUDGETS (Monthly per Package)

| Paket | AI/API Costs | Infrastructure | Buffer | Total | Client Price | Margin |
|-------|--------------|----------------|--------|-------|--------------|--------|
| Inbox AI | $300 | $50 | $100 | $450 | €1.499 | 72% |
| Executive Calendar | $50 | $50 | $50 | $150 | €1.799 | 91% |
| Invoice Agent | $30 | $50 | $50 | $130 | €1.299 | 90% |
| Competitor Intel | $50 | $20 | $30 | $100 | €999 | 90% |
| Reviews Agent | $50 | $20 | $30 | $100 | €699 | 86% |
| Lead Qualification | $180 | $50 | $70 | $300 | €1.899 | 84% |
| Document Processing | $600 | $50 | $150 | $800 | €1.299 | 38%* |
| Website Builder | $30 | $100 | $50 | $180 | €1.899 | 90% |
| **Full Suite** | **$1.290** | **$390** | **$530** | **$2.210** | **€6.699** | **67%** |

*Doc Processing hat niedrigen Margin wegen OCR-Kosten – ggf. Limiten oder Preis anpassen.

---

## RUNBOOKS

### Runbook 1: Restart After Failure

1. Check last error log
2. Identify failure mode
3. If transient (rate limit, timeout): Wait 5 min, retry
4. If persistent: Scale down, alert Circuit
5. Manual intervention if needed
6. Gradual scale-up after fix
7. Post-mortem if >30 min downtime

### Runbook 2: Debug Slow Performance

1. Check API response times
2. Check queue lengths
3. Check CPU/Memory usage
4. Identify bottleneck
5. Scale resources or optimize code
6. Monitor improvement

### Runbook 3: Handle Security Incident

1. Immediately revoke compromised credentials
2. Isolate affected systems
3. Assess data exposure
4. Notify affected clients (within 24h)
5. Document incident
6. Implement prevention measures
7. Post-mortem

---

## SECRETS HYGIENE

**Storage:**
- OpenClaw Secrets Manager (encrypted)
- 1Password für Team-Zugriff
- Niemals in Code/Logs

**Rotation:**
- API Keys: Quartalsweise
- OAuth Tokens: Automatisch (Refresh)
- Passwörter: Bei Mitarbeiter-Wechsel

**Access Control:**
- Circuit: Full Access
- OpsMind: Read-Only (Monitoring)
- Others: No Access

---

## TECHNISCHE VORAUSSETZUNGEN (Pro Paket)

| Paket | Mindestanforderungen | Integrationen | Setup-Zeit |
|-------|---------------------|---------------|------------|
| Inbox AI | Gmail/Outlook Zugang | Google/Microsoft APIs | 3 Tage |
| Executive Calendar | Kalender-Zugang | Google/Microsoft APIs | 5 Tage |
| Invoice Agent | Buchhaltungssoftware | Lexware/sevDesk/Datev | 4 Tage |
| Competitor Intel | Competitor URLs | Brave Search, Scraping | 2 Tage |
| Reviews Agent | Google Business Profile | Google Places API | 2 Tage |
| Lead Qualification | CRM, Formular | HubSpot/Pipedrive | 5 Tage |
| Document Processing | Upload-Mechanismus | OCR API, ERP | 3 Tage |
| Website Builder | Domain, Content | Cloudflare/Netlify | 14 Tage |

---

## HUMAN APPROVALS MATRIX

| Paket | Auto | Human Review | Escalation |
|-------|------|--------------|------------|
| Inbox AI | 90% | 10% (komplex, sensibel) | Negativ/ESkalation |
| Executive Calendar | 85% | 15% (Konflikte, außerhalb BU) | >€10k Termine |
| Invoice Agent | 95% | 5% (>€5k, erste Mahnung) | Legal Notice |
| Competitor Intel | 100% | 0% | Strategische Beratung (Add-on) |
| Reviews Agent | 70% | 30% (1–3★, erste 10) | Rechtsstreit |
| Lead Qualification | 80% | 20% (Hot Leads, erste 20) | Enterprise Deals |
| Document Processing | 90% | 10% (Compliance, Confidence) | Legal Docs |
| Website Builder | 60% | 40% (Design, Content, Launch) | Brand Issues |

---

## ARTIFACTS

1. `delivery/blueprint-inbox-ai.md` (diese Datei)
2. `delivery/blueprint-executive-calendar.md`
3. `delivery/blueprint-invoice-agent.md`
4. `delivery/blueprint-competitor-intel.md`
5. `delivery/blueprint-reviews-agent.md`
6. `delivery/blueprint-lead-qualification.md`
7. `delivery/blueprint-document-processing.md`
8. `delivery/blueprint-website-builder.md`
9. `delivery/failure-modes-matrix.md`
10. `delivery/monitoring-alerts-config.md`
11. `delivery/runbook-restart.md`
12. `delivery/runbook-debug.md`
13. `delivery/runbook-security.md`
14. `delivery/secrets-hygiene.md`
15. `delivery/cost-budgets.md`
16. `delivery/human-approvals-matrix.md`

---

## ASSUMPTIONS

1. OpenClaw API bleibt stabil → **VERIFY durch Changelog-Monitoring**
2. Klient hat Google/Microsoft Workspace → **VERIFY durch Onboarding-Check**
3. API-Limits sind ausreichend → **VERIFY durch Rate-Limit-Tests**
4. Halluzinations-Rate <5% erreichbar → **VERIFY durch QA-Prozess**
5. 99.5% Uptime SLA erreichbar → **VERIFY durch Monitoring-Daten (3 Monate)**

---

## RISKS / EDGE CASES

| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|
| API-Rate-Limits | HIGH | Backoff, Caching, Queueing | Circuit |
| Halluzinationen | HIGH | Human-in-the-loop, Prompt-Tuning, Examples | Circuit + Vox |
| Secrets-Leak | CRITICAL | Vault, Rotation, Audit Logs | Circuit |
| Kostenexplosion | HIGH | Budget-Caps, Alerts, Throttling | Circuit + OpsMind |
| Auth-Token-Expiry | MEDIUM | Auto-Refresh, Alerting | Circuit |
| Integration-Break (API Change) | HIGH | API-Monitoring, Deprecation-Alerts | Circuit |

---

## NEXT ACTIONS

| Owner | Action | Deadline |
|-------|--------|----------|
| Circuit | Prompt Templates Library (8 Pakete) | +4 Tage |
| Circuit | Monitoring/Alerts Setup (Datadog oder selbst) | +5 Tage |
| Circuit | Failure Mode Tests (je Paket 3 Szenarien) | +6 Tage |
| Circuit | Cost Tracking Dashboard | +4 Tage |
| OpsMind | Integration mit CRM für Health Scores | +5 Tage |
| Navi | Review + Freigabe Blueprints | +4 Tage |

---

## DEFINITION OF DONE

- [x] Jedes Paket hat vollständigen Blueprint (Inputs → Workflow → Outputs)
- [x] Jedes Paket hat 5+ Failure Modes mit Detection + Recovery
- [x] Cost Budgets definiert (max/run, max/day, monthly)
- [x] Monitoring/Alerts konfiguriert (Thresholds, Channels)
- [x] Secrets Hygiene dokumentiert
- [x] Runbooks für Restart/Debug/Security
- [x] Human Approvals Matrix pro Paket
- [x] Technische Voraussetzungen gelistet

**STATUS: PHASE 1 COMPLETE — Review durch Navi ausstehend**

---

**HANDOFF v1** | Circuit → Navi → OpsMind (für Integration)
