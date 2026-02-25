# Skill: Amazon Seller Central Alerts

## Description
Automatische Überwachung von Amazon Seller Central für neue Bestellungen, Kundenrezensionen, Lagerbestandswarnungen und Performance-Benachrichtigungen – direkt via Telegram oder Slack.

## Capabilities
- `amazon.poll_orders` - Prüft auf neue Bestellungen
- `amazon.poll_reviews` - Überwacht neue Kundenrezensionen
- `amazon.poll_inventory` - Lagerbestandswarnungen
- `amazon.poll_notifications` - Performance- & Account-Benachrichtigungen

## Problem
- Amazon Seller Central Benachrichtigungen gehen in Email-Flut unter
- Verzögerte Reaktion auf negative Bewertungen
- Überraschungen bei Lagerengpässen
- Wichtige Performance-Warnungen werden übersehen

## Lösung
Automatisierte Polling-Lösung via Amazon Selling Partner API (SP-API) mit sofortigen Alerts an Telegram/Slack.

## Features
1. **Bestellungs-Monitoring** - Sofort-Benachrichtigung bei neuen Bestellungen
2. **Review-Tracking** - Alerts bei neuen Kundenbewertungen (besonders 1-3 Sterne)
3. **Inventory-Alerts** - Warnung bei niedrigem Lagerbestand
4. **Performance-Monitoring** - Account Health & Policy Notifications

## API Keys Required
- Amazon SP-API Credentials (LWA Client ID, Client Secret)
- AWS Access Key + Secret (IAM User)
- Refresh Token (Self-Authorization)
- Telegram Bot Token ODER Slack Webhook URL

## Setup Time
10-15 Minuten

## Use Cases
- Echtzeit-Bestellungsübersicht für Teams
- Schnelle Reaktion auf negative Bewertungen
- Proaktives Lager-Management
- Account Health Monitoring

## Tags
amazon, sp-api, seller-central, e-commerce, telegram, slack, notifications, fba, fbm

## Configuration

### Environment Variables
```bash
# Amazon SP-API
AMAZON_LWA_CLIENT_ID=your_client_id
AMAZON_LWA_CLIENT_SECRET=your_client_secret
AMAZON_REFRESH_TOKEN=your_refresh_token
AMAZON_AWS_ACCESS_KEY=your_aws_key
AMAZON_AWS_SECRET_KEY=your_aws_secret
AMAZON_MARKETPLACE_ID=A1PA6795UKMFR9  # DE marketplace

# Notifications (choose one or both)
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
SLACK_WEBHOOK_URL=your_slack_webhook
```

## Usage

### CLI
```bash
# Einmalige Prüfung (alle Kategorien)
python amazon_seller_alerts.py --check-all

# Nur Bestellungen prüfen
python amazon_seller_alerts.py --orders

# Nur Reviews prüfen
python amazon_seller_alerts.py --reviews

# Als Daemon laufen lassen (alle 5 Min)
python amazon_seller_alerts.py --daemon --interval 300

# Test-Notification senden
python amazon_seller_alerts.py --test
```

### Python API
```python
from amazon_seller_alerts import AmazonSellerAlerts

alerts = AmazonSellerAlerts()

# Check for new orders
new_orders = alerts.check_orders()

# Check for new reviews
new_reviews = alerts.check_reviews()

# Check inventory alerts
inventory_alerts = alerts.check_inventory()
```

## Output Format

### Telegram Nachricht (Bestellung)
```
🛒 <b>Neue Amazon Bestellung</b>

📦 Order-ID: 304-1234567-1234567
👤 Kunde: Max M.
💰 Betrag: €49.99
📊 Menge: 2 Artikel
🚚 Versand: FBA

🕐 25.02.2025 14:30
```

### Telegram Nachricht (Review)
```
⭐ <b>Neue Amazon Bewertung</b>

⚠️ Bewertung: ⭐ (1/5)
📦 ASIN: B08N5WRWNW
📝 Titel: "Defekt angekommen"
💬 "Produkt war bereits beschädigt..."

🔗 Amazon Seller Central öffnen
```

## Rate Limits
- Orders API: 20 requests/sec
- Notifications API: 10 requests/sec
- Empfohlenes Polling: 5 Minuten für Orders, 15 Min für Reviews

## Documentation
- [Amazon SP-API Docs](https://developer-docs.amazon.com/sp-api/)
- [Notifications API](https://developer-docs.amazon.com/sp-api/docs/notifications-api-v1-use-case-guide)
