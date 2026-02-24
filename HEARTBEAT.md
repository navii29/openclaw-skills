# HEARTBEAT.md

## Moltbook (alle 30 Minuten)
Wenn 30 Minuten seit letztem Check vergangen:
1. Prüfe Claim-Status via /api/v1/agents/status
2. Wenn claimed: Lese Feed (Feed?sort=new&limit=10)
3. Engagiere bei relevanten Posts (E-Commerce, Automation, OpenClaw)
4. Update lastMoltbookCheck in memory/heartbeat-state.json

## Outreach-Tracking (täglich)
Wenn 24h seit letztem Check:
1. Prüfe moltbook-DM/Notifications auf Kundenanfragen
2. Dokumentiere Fortschritt in memory/sales-pipeline.md
