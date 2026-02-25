# Skill: Email zu Slack Support-Tickets

## Use Case
Deutsche Unternehmen erhalten Support-Anfragen per Email. Dieser Skill wandelt Emails in Slack-Tickets um für Team-Transparenz.

## Problem
- Support-Emails gehen unter
- Keine Team-Übersicht wer was bearbeitet
- Wichtige Anfragen werden vergessen
- Keine Priorisierung

## Lösung
Email-Monitoring mit Slack-Integration:
1. IMAP-Postfach überwachen
2. Neue Support-Emails erkennen
3. Slack-Thread mit Ticket-Info erstellen
4. Automatische Priorisierung

## Inputs
- IMAP-Zugangsdaten (Gmail/Ionos/etc)
- Slack Webhook/Bot Token
- Support-Email-Adresse

## Outputs
- Slack Nachrichten:
  ```
  🎫 NEUES TICKET #123
  👤 Kunde: max@kunde.de
  📧 Betreff: Login Problem
  🔥 Priorität: HOCH (Dringend!)
  📝 Nachricht: "Ich kann mich nicht einloggen..."
  👥 Status: 🔴 Offen
  ```

## API Keys Required
- Slack Bot Token oder Webhook URL

## Setup Time
10 Minuten

## Use Cases
- Support-Team Koordination
- Kundenbeschwerden tracking
- Bug-Reports sammeln
- Angebotsanfragen verteilen

## Tags
email, support, tickets, slack, imap, customer-service
