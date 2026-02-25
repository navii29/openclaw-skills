# Skill: Stripe Payment Alerts

## Use Case
Deutsche SaaS- und E-Commerce-Unternehmen nutzen Stripe für Zahlungen. Dieser Skill sendet sofortige Benachrichtigungen für wichtige Zahlungsereignisse.

## Problem
- Neue Abonnements werden nicht sofort gesehen
- Failed Payments verschleifen
- Keine Echtzeit-Einblicke in Umsatz
- Manueller Stripe-Login notwendig

## Lösung
Stripe Webhook Integration:
1. Stripe Events empfangen (Webhooks)
2. Wichtige Events filtern
3. Formatierte Benachrichtigungen senden
4. Kunden-Info anreichern

## Inputs
- Stripe Webhook Secret
- Stripe API Key (optional)
- Telegram Bot Token oder Slack Webhook

## Outputs
- Telegram/Slack Nachrichten:
  ```
  💰 NEUE ZAHLUNG!
  👤 Kunde: Max Mustermann
  📧 max@firma.de
  💵 Betrag: €99.00
  📝 Produkt: Pro Plan (Monatlich)
  🎯 MRR: +€99
  ```

## API Keys Required
- Stripe Secret Key
- Telegram Bot Token oder Slack Webhook URL

## Setup Time
5 Minuten

## Use Cases
- Neue Abonnement-Benachrichtigungen
- Failed Payment Alerts
- Umsatz-Tracking
- Churn-Warnungen

## Tags
stripe, payments, saas, billing, telegram, slack, webhooks, notifications
