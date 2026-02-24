# HubSpot ↔ OpenClaw Bridge

## Übersicht
Automatische Deal-Intelligence für HubSpot. Jeder neue Deal wird von einem OpenClaw Agent recherchiert und angereichert.

## Was es macht
1. Empfängt Webhook von HubSpot (Deal Created/Updated)
2. Sendet Unternehmensdaten an OpenClaw Research Agent
3. Agent analysiert: Unternehmensgröße, Tech-Stack, News, Outreach-Angle
4. Schreibt Ergebnisse zurück in HubSpot (Custom Properties)
5. Benachrichtigt Sales-Team bei HIGH Priority Deals

## Setup

### 1. HubSpot Vorbereitung

**Custom Properties erstellen:**
1. HubSpot → Settings → Properties → Deal Properties
2. Folgende Properties anlegen:
   - `lead_score` (Number)
   - `company_size` (Single-line text)
   - `ai_research_notes` (Multi-line text)
   - `ai_priority` (Dropdown: LOW, MEDIUM, HIGH)
   - `ai_enriched_at` (Date)
   - `ai_tech_signals` (Multi-line text)

**Private App erstellen:**
1. Settings → Integrations → Private Apps
2. "Create private app"
3. Scopes: `crm.objects.deals.read`, `crm.objects.deals.write`
4. Token kopieren

**Webhook einrichten:**
1. Settings → Webhooks
2. Target URL: `https://navii-automation.app.n8n.cloud/webhook/hubspot-deal-bridge`
3. Subscriptions: `deal.creation`, `deal.propertyChange` (optional)
4. API Key Header: `X-API-Key` = [aus n8n Credentials]

### 2. n8n Import

1. n8n öffnen: https://navii-automation.app.n8n.cloud
2. "Add Workflow"
3. "Import from File" → `hubspot-openclaw-bridge.json` wählen
4. Credentials einrichten:
   - **OpenClaw**: HTTP Header Auth → `Authorization: Bearer YOUR_TOKEN`
   - **HubSpot**: HTTP Header Auth → `Authorization: Bearer HUBSPOT_TOKEN`
   - **Slack**: Bot Token
5. Environment Variable `BRIDGE_API_KEY` in n8n setzen
6. Speichern & Aktivieren

### 3. Test

```bash
curl -X POST https://navii-automation.app.n8n.cloud/webhook/hubspot-deal-bridge \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_BRIDGE_API_KEY" \
  -d '{
    "objectId": "123456789",
    "portalId": "9876543",
    "properties": {
      "company": {"value": "Test GmbH"},
      "email": {"value": "max@test.de"},
      "amount": {"value": "15000"}
    }
  }'
```

## Kunden-Onboarding

### Schritt 1: HubSpot Token erhalten
- Kunde erstellt Private App
- Token sicher übermitteln (1Password Link)

### Schritt 2: Konfiguration
```yaml
# config/clients/[CLIENT_NAME].yaml
client_id: "acme-corp"
hubspot_portal_id: "1234567"
triggers:
  - event: "deal.created"
    filter: "dealValue > 5000"  # Nur Deals > €5k
actions:
  - type: "enrich"
    properties:
      - "lead_score"
      - "company_size"
      - "ai_research_notes"
  - type: "notify"
    channel: "#sales-alerts"
    condition: "priority == HIGH"
```

### Schritt 3: Webhook aktivieren
- Webhook-URL in HubSpot hinterlegen
- Test-Deal erstellen
- Validieren

## Pricing für Kunden

| Paket | Einrichtung | Monatlich | Deals/Monat |
|-------|-------------|-----------|-------------|
| Starter | €1.500 | €250 | 500 |
| Growth | €2.500 | €500 | 2.000 |
| Enterprise | €5.000 | €1.000 | Unlimited |

**ROI:** Bei 20 Deals/Monat × 20 Min Recherche × €50/Stunde = €333 gespart
**Kosten:** €250 → **Netto-ROI: +33%**

## Troubleshooting

### Webhook nicht ausgelöst
- Prüfe: HubSpot Webhook aktiviert?
- Prüfe: API Key korrekt?
- Prüfe: n8n Workflow aktiv?

### OpenClaw Agent timeout
- Standard: 120 Sekunden
- Bei langsamer Antwort: Timeout erhöhen oder async processing nutzen

### HubSpot Update fehlt
- Prüfe: Custom Properties existieren?
- Prüfe: Token hat `crm.objects.deals.write` Scope?
- Prüfe: Portal ID korrekt?

## Nächste Erweiterungen

- [ ] Pipedrive-Integration (ähnliches Pattern)
- [ ] Salesforce-Integration
- [ ] Zendesk-Ticket-Intelligence
- [ ] Automatische Task-Erstellung für HIGH Priority
- [ ] Email-Sequenz-Trigger basierend auf Priority
