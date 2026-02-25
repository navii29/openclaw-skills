# Skill: WooCommerce Order Alerts

## Use Case
Deutsche WooCommerce Shop-Betreiber erhalten sofortige Benachrichtigungen für neue Bestellungen – keine teuren Plugins nötig.

## Problem
- Neue Bestellungen werden nicht sofort gesehen
- Ständiges Login ins WooCommerce Backend
- Express-Bestellungen verzögern sich
- Keine mobile Benachrichtigung

## Lösung
WooCommerce Webhook Integration:
1. Webhook für neue Bestellungen einrichten
2. Bestelldaten parsen
3. Formatierte Nachricht senden (Telegram/WhatsApp)
4. Prioritäts-Labels (Express, B2B, etc.)

## Inputs
- WooCommerce Webhook (order.created)
- Telegram Bot Token
- Chat ID

## Outputs
- Telegram/WhatsApp Nachricht:
  ```
  🛒 NEUE BESTELLUNG #1234
  👤 Maria Schmidt
  📧 maria@web.de
  💰 €149,99
  📦 3 Artikel
  🚚 Expressversand
  ```

## API Keys Required
- Telegram Bot Token

## Setup Time
5 Minuten

## Use Cases
- Echtzeit-Bestelltracking
- Express-Bestellungen priorisieren
- B2B-Kunden sofort bedienen
- Team-Benachrichtigungen

## Tags
woocommerce, wordpress, e-commerce, telegram, notifications, orders
