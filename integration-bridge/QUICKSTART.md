┌─────────────────────────────────────────────────────────────────────────────┐
│                    HUBSPOT ↔ OPENCLAW BRIDGE - QUICK REFERENCE             │
└─────────────────────────────────────────────────────────────────────────────┘

📁 FILES CREATED
────────────────
/research/learning-session-2-automation-integration.md   # Vollständige Dokumentation
/integration-bridge/hubspot-openclaw-bridge.json         # n8n Workflow (Import-fertig)
/integration-bridge/README.md                            # Setup-Anleitung
/integration-bridge/config/client-template.yaml          # Kunden-Konfiguration

🚀 QUICK START (5 Minuten)
───────────────────────────
1. n8n öffnen: https://navii-automation.app.n8n.cloud
2. "Import from File" → hubspot-openclaw-bridge.json
3. Credentials einrichten (OpenClaw, HubSpot, Slack)
4. BRIDGE_API_KEY als Environment Variable setzen
5. Webhook-URL kopieren

📡 WEBHOOK URL
──────────────
https://navii-automation.app.n8n.cloud/webhook/hubspot-deal-bridge

🔑 REQUIRED ENVIRONMENT VARIABLES
─────────────────────────────────
BRIDGE_API_KEY          # Für Webhook-Auth
OPENCLAW_TOKEN          # OpenClaw Gateway Token
HUBSPOT_TOKEN           # HubSpot Private App Token

🧪 TEST CURL
────────────
curl -X POST https://navii-automation.app.n8n.cloud/webhook/hubspot-deal-bridge \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_BRIDGE_API_KEY" \
  -d '{
    "objectId": "123456789",
    "portalId": "9876543",
    "properties": {
      "company": {"value": "Test GmbH"},
      "email": {"value": "test@example.com"},
      "amount": {"value": "15000"}
    }
  }'

💰 PRICING FÜR KUNDEN
─────────────────────
Starter:     €1.500 Setup + €250/Monat (500 Deals)
Growth:      €2.500 Setup + €500/Monat (2.000 Deals)
Enterprise:  €5.000 Setup + €1.000/Monat (Unlimited)

📊 ROI: 20 Deals × 20min × €50/h = €333 gespart vs €250 Kosten = +33% ROI

✨ WHAT IT DOES
───────────────
1. HubSpot Deal Created → Webhook → Bridge
2. Bridge → OpenClaw Agent (Research)
3. Agent analysiert: Company, Tech-Stack, Outreach-Angle
4. Bridge → HubSpot (Custom Properties)
5. Slack Alert für HIGH Priority Deals

🔧 HUBSPOT CUSTOM PROPERTIES (MÜSSEN ERSTELLT WERDEN)
──────────────────────────────────────────────────────
• lead_score        (Number)
• company_size      (Single-line text)
• ai_research_notes (Multi-line text)
• ai_priority       (Dropdown: LOW/MEDIUM/HIGH)
• ai_enriched_at    (Date)
• ai_tech_signals   (Multi-line text)

📋 NEXT STEPS
─────────────
[ ] HubSpot Test-Account verbinden
[ ] Custom Properties in HubSpot erstellen
[ ] Ersten Test-Deal durchlaufen lassen
[ ] Kunden-Angebot erstellen (CRM Intelligence Bridge)
[ ] Bestehenden HubSpot-Kunden anbieten

🎯 VALUE PROPOSITION
────────────────────
"Automatische Deal-Intelligence: Ihr Sales-Team spart 
15-30 Minuten Recherche pro Lead. Jeder Deal kommt 
voranalysiert mit Score, Unternehmensdaten und 
Outreach-Empfehlung."
