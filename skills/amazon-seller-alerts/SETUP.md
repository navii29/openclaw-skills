# Amazon Seller Central Alerts - Setup Guide

## Schnellstart

### 1. Amazon SP-API Einrichtung

#### a) Amazon Developer Account
1. Registriere dich bei [Amazon Developer Portal](https://developer.amazon.com/)
2. Erstelle eine neue App im Seller Central
3. Wähle "Self Authorization" für deinen eigenen Account

#### b) IAM User in AWS erstellen
```bash
# In AWS Console:
# 1. IAM → Users → Add user
# 2. Name: amazon-sp-api
# 3. Access type: Programmatic access
# 4. Attach policies: AmazonSellingPartnerAPIAccess
# 5. Sichere Access Key ID und Secret
```

#### c) Environment Variablen setzen
```bash
# ~/.bashrc oder ~/.zshrc hinzufügen:

# Amazon SP-API Credentials
export AMAZON_LWA_CLIENT_ID="your_client_id"
export AMAZON_LWA_CLIENT_SECRET="your_client_secret"
export AMAZON_REFRESH_TOKEN="your_refresh_token"
export AMAZON_AWS_ACCESS_KEY="your_aws_key"
export AMAZON_AWS_SECRET_KEY="your_aws_secret"
export AMAZON_MARKETPLACE_ID="A1PA6795UKMFR9"  # DE

# Notification Channels (mindestens eine)
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
# ODER
export SLACK_WEBHOOK_URL="your_slack_webhook"
```

### 2. Telegram Bot erstellen

1. Schreibe [@BotFather](https://t.me/BotFather) auf Telegram
2. Sende `/newbot`
3. Folge den Anweisungen
4. Kopiere den Token
5. Schreibe deinem Bot eine Nachricht
6. Finde deine Chat ID: `https://api.telegram.org/bot<TOKEN>/getUpdates`

### 3. Installation

```bash
cd skills/amazon-seller-alerts
pip install -r requirements.txt
```

### 4. Test

```bash
# Test-Notification senden
python amazon_seller_alerts.py --test

# Einmalige Prüfung
python amazon_seller_alerts.py --check-all

# Als Daemon starten (alle 5 Minuten)
python amazon_seller_alerts.py --daemon --interval 300
```

### 5. Automatisierung (cron/systemd)

#### Cron (alle 5 Minuten)
```bash
# crontab -e
*/5 * * * * cd /path/to/skills/amazon-seller-alerts && python amazon_seller_alerts.py --check-all >> /var/log/amazon_alerts.log 2>&1
```

#### macOS LaunchAgent (~/Library/LaunchAgents/com.amazon.alerts.plist)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.amazon.alerts</string>
    <key>ProgramArguments</key>
    <array>
        <string>python3</string>
        <string>/path/to/amazon_seller_alerts.py</string>
        <string>--daemon</string>
        <string>--interval</string>
        <string>300</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/amazon_alerts.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/amazon_alerts.err</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.amazon.alerts.plist
launchctl start com.amazon.alerts
```

## Troubleshooting

### 403 Forbidden Error
- Prüfe SP-API Berechtigungen in Seller Central
- Stelle sicher dass die IAM Policies korrekt sind

### Rate Limiting
- SP-API hat Limits: 20 req/s für Orders
- Das Tool implementiert automatisches Pacing

### Keine Notifications
- Prüfe TELEGRAM_CHAT_ID (muss die Chat ID sein, nicht der Username)
- Teste mit `--test` Flag
- Prüfe Logs in `~/.amazon_seller_alerts/`

## SP-API Berechtigungen

Erforderliche Berechtigungen in Seller Central:
- **Inventory and Order Tracking**: Orders, Inventory
- **Pricing**: Optional für Preis-Alerts
- **Reports**: Für erweiterte Reports

## Support

- [SP-API Documentation](https://developer-docs.amazon.com/sp-api/)
- [Notifications API Guide](https://developer-docs.amazon.com/sp-api/docs/notifications-api-v1-use-case-guide)
