# 🚀 n8n Workflows für Navii Automation

## Übersicht

| Workflow | Beschreibung | Trigger | Output |
|----------|--------------|---------|--------|
| **🔗 LinkedIn Lead Intelligence** | Empfängt Profile, scored, generiert Outreach | Webhook | Notion + Slack |
| **📊 Daily Lead Report** | Täglicher Report über Pipeline | Schedule (9AM) | Slack + Email |
| **🤖 AI Content Generator** | Generiert LinkedIn/Twitter Content | Webhook | Notion Calendar |
| **📧 Outreach Email Sequenz** | Automatisierte Email-Sequenz für neue Leads | Notion Trigger | Gmail + Slack |
| **🌐 Website Change Monitor** | Überwacht Wettbewerber-Websites | Schedule (6h) | Slack Alert |

---

## Setup

### 1. Credentials einrichten

Gehe in n8n zu **Settings → Credentials** und füge hinzu:

- **Notion API** → Integration Token von notion.so/my-integrations
- **Slack API** → Bot Token von api.slack.com/apps
- **Gmail OAuth2** → OAuth Credentials von Google Cloud Console
- **OpenAI API** → API Key von platform.openai.com

### 2. Workflows importieren

1. Öffne n8n: http://localhost:5678
2. Klicke **Add Workflow**
3. **Import from File** wählen
4. JSON-Datei aus diesem Ordner auswählen
5. **Credential IDs anpassen** (siehe unten)
6. **Speichern & Aktivieren**

### 3. Credential IDs anpassen

In jedem Workflow findest du Platzhalter wie:
```json
"credentials": {
  "notionApi": {
    "id": "YOUR_NOTION_CREDENTIAL_ID",
    "name": "Notion API"
  }
}
```

Ersetze `YOUR_NOTION_CREDENTIAL_ID` mit der tatsächlichen ID aus deinen n8n Credentials.

**Schneller Weg:**
- Credentials in n8n erstellen
- Workflow importieren
- n8n zeigt "Unknown Credential" an
- Auf das Node klicken → Credentials aus Dropdown wählen

---

## Workflow Details

### 🔗 LinkedIn Lead Intelligence

**Input (Webhook):**
```json
{
  "name": "Max Mustermann",
  "title": "CEO",
  "company": "TechStart GmbH",
  "headline": "CEO @ TechStart | SaaS | AI",
  "url": "https://linkedin.com/in/max-m"
}
```

**Flow:**
1. Lead Scoring (0-100 Punkte)
2. Outreach-Message generieren
3. In Notion speichern
4. Bei HOT Leads: Slack Alert

**Output:**
- Notion Database Entry
- Slack Notification (nur HOT)

---

### 📊 Daily Lead Report

**Schedule:** Täglich um 9:00 Uhr

**Flow:**
1. Liest alle Leads aus Notion (letzte 7 Tage)
2. Aggregiert Stats (Total, HOT, WARM, COLD)
3. Top 5 HOT Leads extrahieren
4. Formatiert Report
5. Sendet an Slack + Email

**Output:**
```
📊 Daily Lead Report

Stats:
• Total: 23
• 🔥 HOT: 8
• ⚡ WARM: 12
• 🧊 COLD: 3

Top HOT Leads:
• Max Mustermann @ TechStart (95 pts)
• Anna Schmidt @ SaaS GmbH (88 pts)
...
```

---

### 🤖 AI Content Generator

**Input (Webhook):**
```json
{
  "topic": "Warum AI-Automation kein Luxus mehr ist",
  "audience": "Tech-Gründer",
  "tone": "provokant, aber fundiert"
}
```

**Flow:**
1. OpenAI generiert LinkedIn Post
2. OpenAI generiert Twitter/X Variation
3. Kombiniert Output
4. Speichert in Notion Content Calendar

**Output:**
- LinkedIn Post (150-200 Wörter)
- Twitter/X Version (max 280 Zeichen)
- Hashtags
- Saved to Notion

---

### 📧 Outreach Email Sequenz

**Trigger:** Neuer Lead in Notion mit Status = NEW

**Flow:**
1. Prüft ob Email vorhanden
2. Wählt Template basierend auf Tier (HOT/WARM/COLD)
3. Personalisiert mit Name, Firma, Titel
4. Sendet Email via Gmail
5. Updated Lead Status zu CONTACTED
6. Slack Notification

**Templates:**
- HOT: Direkter Value-Proposition, konkrete Zahlen
- WARM: Frage-basiert, explorativ
- COLD: Allgemein, Beziehungsaufbau

---

### 🌐 Website Change Monitor

**Schedule:** Alle 6 Stunden

**Flow:**
1. Lädt definierte Websites
2. Berechnet MD5-Hash des Content
3. Vergleicht mit vorherigem Hash
4. Bei Änderung: Slack Alert
5. Speichert neuen Hash

**Use Cases:**
- Wettbewerber-Preisänderungen
- Neue Features beobachten
- Industry News Monitoring

---

## Notion Datenbanken

### LinkedIn Leads

Properties:
- Name (Title)
- Firma (Text)
- Titel (Text)
- Score (Number)
- Tier (Select: 🔥 HOT, ⚡ WARM, 🧊 COLD)
- Status (Select: NEW, CONTACTED, REPLY, MEETING, WON, LOST)
- Location (Text)
- LinkedIn (URL)
- Outreach (Text)
- Signals (Text)
- Email (Email)
- Contacted At (Date)

### Content Calendar

Properties:
- Content (Text)
- Variations (Text)
- Topic (Text)
- Status (Select: Draft, Review, Published)
- Created (Date)
- Platform (Multi-select: LinkedIn, Twitter, Instagram)

### Website Monitor

Properties:
- Name (Title)
- URL (URL)
- Hash (Text)
- Last Checked (Date)

---

## API Endpunkte

### LinkedIn Lead Intelligence
```bash
curl -X POST http://localhost:5678/webhook/linkedin-lead \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Max Mustermann",
    "title": "CEO",
    "company": "TechStart GmbH",
    "headline": "CEO @ TechStart | SaaS",
    "url": "https://linkedin.com/in/max"
  }'
```

### AI Content Generator
```bash
curl -X POST http://localhost:5678/webhook/generate-content \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Die Zukunft der AI-Automation",
    "audience": "C-Level Entscheider",
    "tone": "professionell"
  }'
```

---

## Tips

1. **Test Mode:** Vor Aktivierung auf "Execute Once" klicken zum Testen
2. **Error Handling:** Aktiviere "Continue On Fail" für resilientere Workflows
3. **Rate Limits:** Füge "Wait" Nodes hinzu bei API-heavy Workflows
4. **Monitoring:** Aktiviere "Save Execution Progress" für Debugging

---

## Nächste Schritte

- [ ] Credentials einrichten
- [ ] Workflows importieren
- [ ] Notion Datenbanken erstellen
- [ ] Erste Test-Runs durchführen
- [ ] Workflows aktivieren
- [ ] Monitoring einrichten
