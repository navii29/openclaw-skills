# NAVII SPRINT BRIEFINGS — Knowledge Ingestion + Package Mastering

---

## BRIEFING 1: ATLAS (Market Intelligence)

**Objective:** Baue ein vollständiges Markt- und Wettbewerbs-Verständnis auf, das alle Verkaufs- und Delivery-Entscheidungen informiert.

### Kontext
Wir verkaufen 8 AI-Agenten-Pakete (699€–1.899€/Monat) + Full Suite (6.699€). Wir brauchen quantitative Pain-Daten, echte Kunden-Sprache und Competitor-Intelligence, um Positionierung und Einwandbehandlung zu stärken.

### Constraints
- Evidence-basiert (keine Vermutungen)
- DSGVO-konforme Recherche
- Quellen dokumentiert und verifizierbar

### Erwarteter Output (HANDOFF v1)

#### Key Findings / Decisions Needed
- ICP Shortlist (3 Segmente) mit Buyer Persona, Triggern, Budget-Range
- Pain Matrix: Zeitverlust/Stunde × Häufigkeit = €-Impact pro Paket
- Customer Language Bank: 20+ Original-Zitate aus Foren/LinkedIn/Reddit
- Competitor Teardowns (3–5): Offer/Angle/Proof/Pricing/Delivery
- Top 15 Objections Forecast + "What they really mean" + Testplan
- Package Learning Notes: Welches ICP kauft welches Paket + Trigger + messbarer Outcome

#### Artifacts
- `research/icp-analysis.md`
- `research/pain-matrix.md`
- `research/competitor-teardown.md`
- `research/objection-forecast.md`
- `research/language-bank.json`

#### Assumptions
1. Zielgruppe hat 50+ E-Mails/Tag (Inbox Pakete)
2. Budget für Automation ist vorhanden (bereits 1+ VA oder Software)
3. Schmerzpunkt ist Zeit, nicht Geld

#### Risks / Edge Cases
1. Dünne Datenlage bei Nischen-ICPs → Eskalation an Navi
2. Competitor-Preise nicht öffentlich → Schätzungen markieren
3. Language Bank nicht repräsentativ → Quellen-Diversität prüfen

#### Next Actions
| Owner | Action | Deadline |
|-------|--------|----------|
| Atlas | ICP-Recherche abschließen | +2 Tage |
| Atlas | 5 Competitor Deep-Dives | +3 Tage |
| Atlas | Objection Forecast final | +4 Tage |

#### Definition of Done (DoD)
- [ ] 3 ICPs mit validierten Pain-Points (Evidence: High)
- [ ] Pain Matrix mit €-Beträgen (quantiifziert)
- [ ] 20+ Language-Bank-Einträge mit Quellen
- [ ] 5 Competitor-Profile (vollständig)
- [ ] 15 Objections mit „What they really mean"

---

## BRIEFING 2: FORGE (Offer Engineer)

**Objective:** Strukturiere unsere 8 Pakete + Full Suite zu einer schlüssigen, verkaufbaren Offer-Matrix mit klarer Preisleiter und Begründung.

### Kontext
Preise fix: Einzel 699€–1.899€, Full Suite 6.699€, Setup 2.500€. Jedes Paket braucht klaren Scope, Outcome, SLA und menschliche Freigabe-Punkte.

### Constraints
- Preise nicht verhandelbar (699–1.899 Range)
- Scope muss lieferbar sein (Circuit validiert)
- Setup Fee logisch integrieren

### Erwarteter Output (HANDOFF v1)

#### Key Findings / Decisions Needed
- Preisleiter-Zuordnung: Welches Paket in welchen Tier (699/999/1.299/1.499/1.799/1.899)
- One-Pager pro Paket (Outcome, Ideal für, In/Out Scope, Setup, Approvals, SLA)
- Full Suite One-Pager (6.699€) + exklusive Benefits + Upsell-Logik
- Setup-Fee Integration: Was ist inklusive (Lead-to-Meeting Automation)
- Proof Plan: Case Study Skeletons (3) + Demo Assets
- Package Masterbook Kapitel: komplette Matrix

#### Artifacts
- `packages/inbox-ai.md` (Reply + Triage combined)
- `packages/executive-calendar.md`
- `packages/invoice-agent.md`
- `packages/competitor-intelligence.md`
- `packages/reviews-agent.md`
- `packages/lead-qualification.md` (Zusatzpaket)
- `packages/document-processing.md` (Zusatzpaket)
- `packages/full-suite.md`
- `packages/setup-fee-breakdown.md`
- `assets/case-study-skeletons.md`

#### Assumptions
1. Value-Based Pricing (nicht Cost-Plus)
2. Setup Fee = 2.500€ deckt 4 Wochen Onboarding
3. Full Suite = 8 Pakete + Exklusivitäten

#### Risks / Edge Cases
1. Scope Creep bei „einfachen" Paketen → klare Out-of-Scope-Listen
2. Setup Fee als Stolperstein → Value-Framing wichtig
3. Preis-Tabu bei deutschen Kunden → Psychologie-Tricks nutzen

#### Next Actions
| Owner | Action | Deadline |
|-------|--------|----------|
| Forge | Preisleiter finalisieren | +2 Tage |
| Forge | 8 One-Pager + Full Suite | +4 Tage |
| Forge | Case Study Skeletons | +5 Tage |

#### Definition of Done (DoD)
- [ ] Jedes Paket hat klaren Preis (699–1.899)
- [ ] Jedes Paket hat In/Out-of-Scope-Liste
- [ ] Full Suite zeigt 40%+ Rabatt vs. Einzel
- [ ] Setup Fee ist logisch eingebunden
- [ ] 3 Case Study Skeletons (fiktiv aber plausibel)

---

## BRIEFING 3: VOX (Sales Command)

**Objective:** Baue eine vollständige Sales Engine mit Messaging, Sequenzen, Scripts und Objection Library, die ohne Navi skaliert.

### Kontext
Wir verkaufen B2B-Dienstleistungen (699€–6.699€/Monat). Sales-Prozess: LinkedIn/E-Mail → Call → Proposal → Close. Compliance-kritisch (DSGVO, UWG).

### Constraints
- Keine Täuschung
- Opt-out immer möglich
- Ramp-up: max 50 Mails/Tag in Woche 1
- Stop-If: Bounce >5%, Complaints >0.1%

### Erwarteter Output (HANDOFF v1)

#### Key Findings / Decisions Needed
- Messaging Framework pro Paket + Full Suite (Problem-Agitate-Solution)
- 2 LinkedIn Sequenzen (je 5 Touches) + Opt-out
- 2 Cold Email Sequenzen (je 5 Touches) + Opt-out
- Call Script (kurz 5min + lang 15min) + Discovery Sheet
- Qualification Rules (BANT-Score pro Paket)
- Objection Library (30) mit Antworten + Paket-Karten
- A/B Test Plan + KPI Targets
- Package Masterbook Kapitel: „How to sell each package in 30 seconds"

#### Artifacts
- `sales/messaging-framework.md`
- `sales/linkedin-sequence-a.md`
- `sales/linkedin-sequence-b.md`
- `sales/email-sequence-a.md`
- `sales/email-sequence-b.md`
- `sales/call-script-short.md`
- `sales/call-script-long.md`
- `sales/discovery-sheet.md`
- `sales/objection-library.md`
- `sales/ab-test-plan.md`
- `sales/weekly-report-template.md`

#### Assumptions
1. ICP ist auf LinkedIn aktiv
2. E-Mail-Deliverability ist konfigurierbar (DNS/DKIM)
3. Sales-Zyklus: 2–4 Wochen

#### Risks / Edge Cases
1. Compliance-Verstoß → Stop-If-Regeln strikt
2. Sequenzen zu aggressiv → A/B-Testing mit kleinem Sample
3. Objections nicht vorhersehbar → kontinuierliches Update

#### Next Actions
| Owner | Action | Deadline |
|-------|--------|----------|
| Vox | Messaging Framework | +2 Tage |
| Vox | Sequenzen (LinkedIn + E-Mail) | +4 Tage |
| Vox | Objection Library (30) | +5 Tage |

#### Definition of Done (DoD)
- [ ] 4 Sequenzen (je 5 Touches) mit Opt-out
- [ ] 2 Call Scripts mit Discovery Sheet
- [ ] 30 Objections mit Antworten
- [ ] Compliance-Check bestanden (Stop-If definiert)
- [ ] A/B Test Plan mit KPI Targets

---

## BRIEFING 4: CIRCUIT (Automation Architect)

**Objective:** Erstelle lieferbare Blueprints für alle 8 Pakete + Full Suite, die 24/7 autonom laufen mit Monitoring, Alerts und Fallbacks.

### Kontext
Alle Pakete laufen auf OpenClaw. Jeder Agent braucht: Inputs → Workflow → Outputs → QA Gates. Kostenkontrolle und Restart-Safety Pflicht.

### Constraints
- Max Cost/Run definiert pro Paket
- Max Runs/Day limitiert
- Secrets niemals in Code
- Logging + Alerts Pflicht

### Erwarteter Output (HANDOFF v1)

#### Key Findings / Decisions Needed
- Delivery Blueprint pro Paket (Inputs, Workflow, Roles, Outputs, QA)
- Prompt/Agent Template Library (copy-paste ready)
- Failure Modes (min 5) + Detection + Recovery je Paket
- Monitoring/Alerts + Cost Budgets je Paket
- Runbooks (restart/debug) + Secrets Standards
- Package Masterbook Kapitel: technische Voraussetzungen, Integrationen, Zeitplan

#### Artifacts
- `delivery/blueprint-inbox-ai.md`
- `delivery/blueprint-executive-calendar.md`
- `delivery/blueprint-invoice.md`
- `delivery/blueprint-competitor-intel.md`
- `delivery/blueprint-reviews.md`
- `delivery/blueprint-lead-qual.md`
- `delivery/blueprint-doc-processing.md`
- `delivery/prompt-templates/` (Unterordner)
- `delivery/failure-modes-matrix.md`
- `delivery/monitoring-alerts-config.md`
- `delivery/runbooks/` (Unterordner)
- `delivery/secrets-hygiene.md`

#### Assumptions
1. OpenClaw API stabil
2. Klient hat Google Workspace oder Microsoft 365
3. Webhook-Integrationen möglich

#### Risks / Edge Cases
1. API-Rate-Limits → Backoff-Strategien
2. Halluzinationen bei E-Mail-Antworten → Human-in-the-loop
3. Secrets-Leak → Vault-Integration Pflicht
4. Kostenexplosion → Budget-Caps + Alerts

#### Next Actions
| Owner | Action | Deadline |
|-------|--------|----------|
| Circuit | 8 Delivery Blueprints | +4 Tage |
| Circuit | Prompt Template Library | +5 Tage |
| Circuit | Monitoring + Alerts Setup | +6 Tage |

#### Definition of Done (DoD)
- [ ] Jedes Paket hat vollständigen Blueprint
- [ ] Jedes Paket hat 5+ Failure Modes mit Recovery
- [ ] Cost Budgets definiert (max/run, max/day)
- [ ] Monitoring/Alerts konfiguriert
- [ ] Secrets Hygiene dokumentiert
- [ ] Runbooks für Restart/Debug

---

## BRIEFING 5: OPSMIND (COO/Operations)

**Objective:** Baue das Operating System der Agentur: CRM, Dashboards, QA Gates und Knowledge Management, das skaliert ohne Chaos.

### Kontext
Wir brauchen eine einheitliche Wahrheit für Sales, Delivery und Reporting. Alle Agenten müssen konsistent arbeiten und übergreifen.

### Constraints
- CRM muss mit Paket-Preisen (699–6.699) umgehen können
- Daten-Hygiene: keine doppelten Leads
- Weekly Cadence Pflicht

### Erwarteter Output (HANDOFF v1)

#### Key Findings / Decisions Needed
- CRM Blueprint (Stages, Fields, SLAs, Owner Rules)
- Dashboards (Sales/Delivery/Cost) + Schwellenwerte
- Weekly Operating Cadence (Agenda, Inputs, Decisions)
- QA Checklists + Change Request Policy + Post-Mortem Template
- Knowledge Base Struktur + Glossar + MEMORY/BACKLOG/KPI Snapshot
- Website/Assets Konsistenz-Check: Preise/Scope überall identisch
- Package Masterbook Kapitel: SOPs pro Paket (Onboarding → Delivery → Reporting)

#### Artifacts
- `ops/crm-blueprint.md`
- `ops/dashboards-config.md`
- `ops/weekly-cadence.md`
- `ops/qa-checklists.md`
- `ops/change-request-policy.md`
- `ops/post-mortem-template.md`
- `ops/knowledge-base-structure.md`
- `ops/glossar.md`
- `ops/website-consistency-check.md`
- `ops/package-sops/` (Unterordner)

#### Assumptions
1. HubSpot oder Pipedrive als CRM
2. Notion als KB
3. Slack für Alerts

#### Risks / Edge Cases
1. CRM wird nicht genutzt → Enforcement-Regeln
2. Dateninkonsistenz → Validierungs-Regeln
3. Knowledge Base unbrauchbar → Suche + Struktur wichtig

#### Next Actions
| Owner | Action | Deadline |
|-------|--------|----------|
| OpsMind | CRM Blueprint final | +2 Tage |
| OpsMind | Dashboards Design | +3 Tage |
| OpsMind | KB Struktur + Glossar | +4 Tage |
| OpsMind | Website Consistency Check | +5 Tage |

#### Definition of Done (DoD)
- [ ] CRM Stages + Fields dokumentiert
- [ ] 3 Dashboards designed (Sales/Delivery/Cost)
- [ ] Weekly Cadence mit Agenda
- [ ] QA Checklists für jedes Paket
- [ ] KB Struktur + Glossar
- [ ] Website/Assets Konsistenz bestätigt

---

# SPRINT TIMELINE

| Phase | Zeitraum | Deliverables | Owner |
|-------|----------|--------------|-------|
| **Phase 1: Research** | Tag 1–4 | Quellenlisten, Research Plans, Package Learning Notes | Alle Agenten |
| **Phase 2: Synthesis** | Tag 3–7 | 3–7 Artefakte pro Agent, Package Masterbook Kapitel | Alle Agenten |
| **Phase 3: Integration** | Tag 6–9 | Unified KB, Glossar, Paket-Matrix, Preisleiter | OpsMind |
| **Phase 4: Dry Run** | Tag 8–10 | End-to-End Simulation, Einwand-Test, Lücken-Identifikation | Alle Agenten |
| **Phase 5: Patch** | Tag 9–12 | Lücken geschlossen, Templates final, MEMORY aktualisiert | OpsMind + Navi |

### Meilensteine
- **M1 (Tag 4):** Alle HANDOFF v1 aus Phase 1 vorliegen
- **M2 (Tag 7):** Alle Artefakte + Package Kapitel vorliegen
- **M3 (Tag 9):** KB konsolidiert, Glossar final
- **M4 (Tag 10):** Dry Run abgeschlossen, Lücken dokumentiert
- **M5 (Tag 12):** SPRINT DONE, MEMORY final

---

# NAVI DOD-CHECKS (Pro Phase)

### Phase 1: Research
- [ ] Jeder Agent hat 8–15 Quellen (hochwertig)
- [ ] Package Learning Notes vollständig (alle 8 Pakete)
- [ ] Evidence Levels markiert (High/Med/Low)
- [ ] HANDOFF v1 Format strikt eingehalten

### Phase 2: Synthesis
- [ ] 3–7 Artefakte pro Agent (zählbar)
- [ ] Package Masterbook Kapitel vollständig
- [ ] Alle Kernbehauptungen haben „How to verify"
- [ ] DoD für jedes Artefakt erfüllt

### Phase 3: Integration
- [ ] KB Struktur konsistent
- [ ] Glossar definiert alle Begriffe
- [ ] Paket-Matrix zeigt alle 8 Pakete + Preise
- [ ] Website/Assets Konsistenz bestätigt

### Phase 4: Dry Run
- [ ] Simulation durchlaufen (Lead → Close → Delivery)
- [ ] Alle Paket-Einwände getestet
- [ ] Lücken dokumentiert + Priorisierung
- [ ] Keine Blocker für Go-Live

### Phase 5: Patch
- [ ] Alle kritischen Lücken geschlossen
- [ ] Templates finalisiert
- [ ] MEMORY aktualisiert (max 12 Bullets)
- [ ] BACKLOG + KPI Snapshot aktuell

---

# NAVI ENTSCHEIDUNG: Paket-Matrix (Entwurf)

| Paket | Preis/Monat | Tier | Outcome (messbar) | Scope-Kern | Setup | Human Approval |
|-------|-------------|------|-------------------|------------|-------|----------------|
| **Inbox AI** | €1.499 | Core | <5min Reaktionszeit, 90% Automatisierung | Reply + Triage + Priorisierung | 3 Tage | Komplexe Anfragen |
| **Executive Calendar** | €1.799 | Premium | 0 Termin-Konflikte/Woche, 100% Erinnerungen | Selbstbuchung + Rescheduling + Prep | 5 Tage | Externe Termine >€10k |
| **Invoice Agent** | €1.299 | Standard | 100% pünktliche Rechnungen, <2% Ausfälle | Erstellen + Versand + Mahnen | 4 Tage | Mahnstufe 2+ |
| **Competitor Intel** | €999 | Entry | Wöchentlicher Report, 5–10 Competitors | Monitoring + Analysis + Content-Ideen | 2 Tage | Strategische Empfehlungen |
| **Reviews Agent** | €699 | Entry | <2h Reaktionszeit, 4.8★ Durchschnitt | Monitoring + Antworten + Alerts | 2 Tage | Negative Reviews |
| **Lead Qualification** | €1.899 | Premium | 80% qualifizierte Leads, 0 Tire-Kicker | BANT-Scoring + Absagen + Termine | 5 Tage | Qualifizierte Leads |
| **Document Processing** | €1.299 | Standard | 95% OCR-Genauigkeit, <1h Turnaround | Extraktion + Kategorisierung + Export | 3 Tage | Compliance-Docs |
| **Website Builder** | €1.899 | Premium | Live in 14 Tagen, 90+ PageSpeed | Design + Content + SEO + Hosting | 14 Tage | Brand/Design-Approval |
| **Full Suite** | €6.699 | Enterprise | 80% Admin-Arbeit automatisiert | Alle 8 Pakete + Exklusiv-Benefits | 21 Tage | Alle kritischen |

### Preis-Begründung (Tiers)
- **€699–€999 (Entry):** High-Frequency, Low-Complexity (Reviews, Competitor)
- **€1.299–€1.499 (Standard/Core):** Moderate Komplexität, hoher Impact (Inbox, Invoice, Doc Processing)
- **€1.799–€1.899 (Premium):** High-Touch, strategisch (Calendar, Lead Qual, Website)
- **€6.699 (Full Suite):** 40% Rabatt vs. Einzel + Priorisierter Support + Double Capacity

### Setup-Fee Integration (€2.500)
**Enthalten:**
- Kickoff-Workshop (2h)
- System-Setup & Integrationen
- Team-Training (1h)
- Dokumentation & Notfall-Pläne
- 30 Tage Onboarding-Support
- Lead-to-Meeting Automation (bestehende Infrastruktur)

**Rabatt:** €1.500 bei Full Suite oder 3+ Paketen

---

# ZUSATZPAKETE (Optional, einfach lieferbar)

| Paket | Preis | Warum sinnvoll |
|-------|-------|----------------|
| **Social Media Agent** | €999/Monat | LinkedIn + Twitter Posts + Scheduling. Natürliche Erweiterung von Competitor Intel. Einfach: Content aus Intel feeden, Planung automatisch. |
| **Report/Analytics Agent** | €1.299/Monat | Wöchentliche/Monatliche Reports aus allen Datenquellen. Jeder Kunde braucht Reporting – kann aus anderen Paketen Daten ziehen. |

**Empfehlung:** Social Media Agent als 9. Paket hinzufügen (komplettiert Marketing-Stack). Report Agent als Upsell/Add-on (passt zu Full Suite).

---

**SPRINT START: JETZT**
**ERSTER MEILENSTEIN: Tag 4 (Alle Phase 1 HANDOFFs)**
**FINAL DONE: Tag 12**

Navi out. 🦊
