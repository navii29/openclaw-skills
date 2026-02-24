# 🎯 LinkedIn Lead Pipeline

> Automatisierte Lead-Intelligence für die AI-Agentur

## 📊 Pipeline Übersicht

| Tier | Anzahl | Status |
|------|--------|--------|
| 🔥 HOT | 0 | Kontaktieren |
| ⚡ WARM | 0 | Beobachten |
| 🧊 COLD | 0 | Archivieren |

---

## 🔥 HOT Leads (Score 80-100)

| Name | Firma | Titel | Score | Status | Outreach |
|------|-------|-------|-------|--------|----------|
| Max Mustermann | TechStart GmbH | CEO & Co-Founder | 100 | NEW | [LinkedIn](="#") |

### Lead Details: Max Mustermann

- **URL:** https://linkedin.com/in/saas-founder-berlin
- **Location:** Berlin, Germany
- **Score:** 100/100
- **Signals:**
  - ✅ Title: CEO (+25)
  - ✅ Title: Founder (+25)
  - ✅ Industry: SaaS (+15)
  - ✅ Industry: AI (+20)
  - ✅ Decision maker (+10)

**Outreach Message (LinkedIn):**
> Hi Max, als CEO & Co-Founder bei TechStart GmbH interessieren Sie sich sicher für operative Effizienz. Wir helfen Tech-Führungskräften, 10+ Stunden/Woche durch AI-Automation zu sparen. Interesse an einem 15-minütigen Austausch?

---

## ⚡ WARM Leads (Score 60-79)

*Noch keine WARM Leads in der Pipeline*

---

## 🧊 COLD Leads (Score <60)

*Noch keine COLD Leads in der Pipeline*

---

## 🔄 Workflow

### 1. Lead Discovery
- Chrome Extension scannt LinkedIn-Suchergebnisse
- Profil-Daten werden extrahiert (Name, Titel, Firma, About)

### 2. Lead Scoring (100 Punkte System)
- **Titel:** CEO/Founder (+25), CTO (+20), Head of (+15)
- **Industrie:** AI/Automation (+20), SaaS (+15), Tech (+10)
- **Status:** Decision maker (+10), Automation-Interesse (+15)

### 3. Outreach Generation
- Automatisch generierte Messages basierend auf Tier
- Personalisiert mit Name, Firma, Industrie
- Verfügbar als LinkedIn DM oder Email

### 4. Pipeline Management
- Status: NEW → CONTACTED → REPLY → MEETING → WON/LOST
- Notizen pro Lead
- Follow-up Reminder

---

## 🛠️ Automation Commands

```bash
# Lead hinzufügen
node agents/linkedin-orchestrator.js process <linkedin-url>

# Pipeline anzeigen
node agents/linkedin-orchestrator.js pipeline

# Täglichen Report
node agents/linkedin-orchestrator.js report
```

---

## 📈 KPIs

- **Leads/Week:** Ziel: 20
- **HOT Lead Rate:** Ziel: >30%
- **Conversion Meeting:** Ziel: >10%
- **Response Rate:** Ziel: >15%

---

*Letzte Aktualisierung: 2026-02-19*
