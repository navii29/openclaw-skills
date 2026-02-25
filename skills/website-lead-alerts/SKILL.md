# Skill: Website Lead Scraper + Telegram Alerts

## Use Case
Deutsche Dienstleister (Webdesign, Beratung, Agenturen) wissen nicht sofort, wenn potenzielle Kunden Kontakt aufnehmen. Dieser Skill überwacht Websites und sendet sofortige Telegram-Alerts.

## Problem
- Kontaktformulare werden nicht sofort gesehen
- Preisanfragen verzögern sich
- Wettbewerber sind schneller
- Nachts/Wochenende keine Reaktion

## Lösung
Website Monitoring:
1. Website/Kontaktseite überwachen (HTTP-Checks)
2. Neue Einträge/Kontakte erkennen
3. Sofortige Telegram-Benachrichtigung
4. Lead-Priorisierung basierend auf Keywords

## Inputs
- Website URL(s) zum Überwachen
- Telegram Bot Token
- Chat ID
- Keywords für Priorisierung (optional)

## Outputs
- Telegram Nachrichten:
  ```
  🎯 NEUER LEAD!
  👤 Name: Max Mustermann
  📧 Email: max@firma.de
  💬 Nachricht: "Angebot für Website..."
  🔥 Priorität: HOCH
  🌐 Quelle: Kontaktformular
  ```

## API Keys Required
- Telegram Bot Token

## Setup Time
5 Minuten

## Use Cases
- Kontaktformular-Monitoring
- Preisanfragen-Tracking
- Livechat-Integration
- Bewerbungen-Tracking

## Tags
website, monitoring, leads, telegram, alerts, scraping, sales
