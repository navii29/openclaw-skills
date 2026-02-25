# Google Reviews Monitor - Setup Guide

## Schnellstart

### 1. Google Places API Key erstellen

1. [Google Cloud Console](https://console.cloud.google.com/) öffnen
2. Neues Projekt erstellen: "Reviews Monitor"
3. **APIs & Services** → **Library**
4. Suche "Places API" → **Enable**
5. **Credentials** → **Create Credentials** → **API Key**
6. (Optional) Key auf Places API einschränken

### 2. Installation

```bash
cd skills/google-reviews-monitor
pip3 install -r requirements.txt
```

### 3. Environment setzen

```bash
export GOOGLE_PLACES_API_KEY="your_api_key_here"
```

### 4. Place ID finden

```bash
# Suche nach Ort
python google_reviews.py --search "Restaurant Name, Berlin"

# Kopiere die Place ID aus der Ausgabe
```

### 5. Reviews abrufen

```bash
# Reviews anzeigen
python google_reviews.py --place-id "ChIJ..."

# Mit Sentiment-Analyse
python google_reviews.py --place-id "ChIJ..." --analyze

# Nur negative (1-2 Sterne)
python google_reviews.py --place-id "ChIJ..." --min-stars 1 --max-stars 2
```

### 6. Mit Notifications (optional)

#### Telegram:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Jetzt werden Alerts gesendet
python google_reviews.py --place-id "ChIJ..."
```

#### Slack:
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

### 7. Monitoring mit Config

Erstelle `places.json`:

```json
{
  "places": [
    {
      "name": "Mein Restaurant",
      "place_id": "ChIJ123...",
      "alert_stars_min": 1,
      "alert_stars_max": 3
    },
    {
      "name": "Café Zweigstelle",
      "place_id": "ChIJ456...",
      "alert_stars_min": 1,
      "alert_stars_max": 5
    }
  ],
  "check_interval": 3600
}
```

Starte Monitoring:
```bash
python google_reviews.py --monitor --config places.json
```

### 8. Automatisierung (macOS)

**LaunchAgent** (`~/Library/LaunchAgents/com.google.reviews.plist`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.google.reviews</string>
    <key>ProgramArguments</key>
    <array>
        <string>python3</string>
        <string>/Users/YOURNAME/.openclaw/workspace/skills/google-reviews-monitor/google_reviews.py</string>
        <string>--monitor</string>
        <string>--config</string>
        <string>/Users/YOURNAME/places.json</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>GOOGLE_PLACES_API_KEY</key>
        <string>your_api_key</string>
        <key>TELEGRAM_BOT_TOKEN</key>
        <string>your_token</string>
    </dict>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.google.reviews.plist
```

## API Limits & Kosten

| Tier | Limit | Kosten |
|------|-------|--------|
| Free | 100,000 requests/Monat | $0 |
| Danach | pro 1,000 requests | ~$7 |

Für die meisten Nutzer bleibt es **kostenlos**.

## Environment Variables

```bash
# Required
export GOOGLE_PLACES_API_KEY="..."

# Optional Notifications
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
export SLACK_WEBHOOK_URL="..."

# Optional Settings
export REVIEWS_CHECK_INTERVAL=3600  # Sekunden
export REVIEWS_MIN_STARS=1          # Alert bei 1+ Sternen
export REVIEWS_MAX_STARS=3          # Alert bei 3- Sternen
```

## CLI Beispiele

```bash
# Suche nach Ort
python google_reviews.py --search "Starbucks Berlin Mitte"

# Reviews anzeigen
python google_reviews.py --place-id "ChIJn8vo2lZKqEcRmR..."

# Analyse
python google_reviews.py --place-id "ChIJ..." --analyze

# Als JSON speichern
python google_reviews.py --place-id "ChIJ..." --output reviews.json

# Monitor mit Config
python google_reviews.py --monitor --config places.json
```

## Troubleshooting

### "API Error: REQUEST_DENIED"
- Places API ist nicht aktiviert
- API Key hat falsche Einschränkungen

### "API Error: NOT_FOUND"
- Place ID ist ungültig
- Ort wurde geschlossen

### Keine Notifications
- Prüfe Telegram Chat ID (nicht Username!)
- Teste mit `--place-id` zuerst

### Rate Limit
- Google Places API hat 100,000 req/Monat Free Tier
- Tool hat eingebautes Pacing

## Wichtige URLs

- [Google Places API Docs](https://developers.google.com/maps/documentation/places/web-service/overview)
- [Place ID Finder](https://developers.google.com/maps/documentation/places/web-service/place-id)
- [Pricing Calculator](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing)
