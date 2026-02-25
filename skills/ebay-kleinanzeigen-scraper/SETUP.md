# eBay Kleinanzeigen Scraper - Setup Guide

## Schnellstart

### 1. Installation

```bash
cd skills/ebay-kleinanzeigen-scraper
pip3 install -r requirements.txt
```

### 2. Erste Suche

```bash
# Einfache Suche
python ebay_kleinanzeigen.py --search "iPhone 15 Pro" --max-price 900

# Mit Standort
python ebay_kleinanzeigen.py --search "Vespa" --city "Berlin" --radius 50

# Mehrere Seiten
python ebay_kleinanzeigen.py --search "MacBook" --pages 3
```

### 3. Mit Notifications (optional)

#### Telegram einrichten:
1. Schreibe [@BotFather](https://t.me/BotFather)
2. `/newbot` → Name vergeben → Token kopieren
3. Bot starten und Nachricht senden
4. Chat ID ermitteln:
   ```bash
   curl https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
5. Environment setzen:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   ```

#### Slack einrichten:
1. [Slack App](https://api.slack.com/apps) erstellen
2. "Incoming Webhooks" aktivieren
3. Webhook URL kopieren:
   ```bash
   export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
   ```

### 4. Monitoring mit Config

Erstelle `searches.json`:

```json
{
  "searches": [
    {
      "query": "iPhone 15 Pro",
      "max_price": 900,
      "min_price": 500,
      "category": 161,
      "city": "Berlin",
      "radius": 30
    },
    {
      "query": "Vespa GTS 300",
      "max_price": 4000,
      "category": 305,
      "city": "Hamburg",
      "radius": 100
    }
  ],
  "check_interval": 300
}
```

Starte Monitoring:
```bash
python ebay_kleinanzeigen.py --monitor --config searches.json
```

### 5. Automatisierung (macOS)

**LaunchAgent** erstellen (`~/Library/LaunchAgents/com.ebay.kleinanzeigen.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ebay.kleinanzeigen</string>
    <key>ProgramArguments</key>
    <array>
        <string>python3</string>
        <string>/Users/YOURNAME/.openclaw/workspace/skills/ebay-kleinanzeigen-scraper/ebay_kleinanzeigen.py</string>
        <string>--monitor</string>
        <string>--config</string>
        <string>/Users/YOURNAME/searches.json</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/ebay_kleinanzeigen.out</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ebay_kleinanzeigen.err</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.ebay.kleinanzeigen.plist
```

## Wichtige Kategorie IDs

| Kategorie | ID |
|-----------|-----|
| Elektronik | 161 |
| Handys | 176 |
| Computer | 245 |
| Audio & HiFi | 172 |
| Möbel | 80 |
| Wohnzimmer | 88 |
| Schlafzimmer | 86 |
| Motorräder & Roller | 305 |
| Autos | 210 |
| Fahrräder | 217 |
| Immobilien | 297 |
| Wohnungen | 199 |
| Häuser | 208 |
| Mode & Accessoires | 153 |
| Kleidung | 156 |
| Schuhe | 160 |
| Sport & Camping | 320 |
| Spielzeug | 231 |
| Bücher | 78 |
| Musik & CDs | 77 |

Vollständige Liste: https://www.ebay-kleinanzeigen.de/s-kategorien.html

## Environment Variables

```bash
# Delays (wichtig für Rate Limiting)
export KLEINANZEIGEN_DELAY=3           # Sekunden zwischen Requests
export KLEINANZEIGEN_MAX_PAGES=5       # Max Seiten pro Suche

# Notifications
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
export SLACK_WEBHOOK_URL="..."
```

## CLI Beispiele

```bash
# Elektronik in Berlin
python ebay_kleinanzeigen.py -s "MacBook Pro" -c 245 --city Berlin -r 30

# Schnäppchen unter 50€
python ebay_kleinanzeigen.py -s "zu verschenken" --max-price 50

# Autos im Umkreis
python ebay_kleinanzeigen.py -s "BMW 3er" -c 210 --city München -r 100 -p 5

# Mit JSON Output
python ebay_kleinanzeigen.py -s "Lego" --output lego_deals.json
```

## Troubleshooting

### 403 Forbidden
- User-Agent Rotation ist eingebaut
- Erhöhe `KLEINANZEIGEN_DELAY` auf 5+

### Keine Ergebnisse
- Prüfe Kategorie ID
- Teste ohne Radius-Filter
- HTML-Struktur ändert sich manchmal

### Doppelte Benachrichtigungen
- State wird in `~/.ebay_kleinanzeigen_seen.json` gespeichert
- Datei löschen um Cache zu resetten

## Legal Notice

- Nur für private Nutzung
- Nicht für kommerzielles Scraping
- Respektiere Rate Limits
- Keine serverseitigen Bots ohne Erlaubnis
