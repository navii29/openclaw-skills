# Skill: Shopify Order-to-Telegram Alerts

## Use Case
Deutsche Shopify-Händler erhalten sofort Telegram-Benachrichtigungen für neue Bestellungen – ohne teure Apps oder monatliche Kosten.

## Problem
- Shopify-Benachrichtigungs-Emails gehen unter
- Händler verpassen wichtige Bestellungen
- Echtzeit-Überblick fehlt

## Lösung
Webhook-Integration: Neue Shopify-Bestellung → Sofortige Telegram-Nachricht mit Bestell-details.

## Inputs
- Shopify Webhook (Order Create)
- Telegram Bot Token
- Telegram Chat ID

## Outputs
- Formatierte Telegram-Nachicht:
  ```
  🛒 Neue Bestellung #1001
  👤 Max Mustermann
  💰 €89,99
  📦 3 Artikel
  🚚 Standardversand
  ```

## API Keys Required
- Shopify API Key + Secret
- Telegram Bot Token

## Setup Time
5 Minuten

## Use Cases
- Echtzeit-Bestelltracking
- Schnelle Reaktion auf Express-Bestellungen
- Team-Benachrichtigungen

## Tags
shopify, e-commerce, telegram, notifications, orders, webhook
