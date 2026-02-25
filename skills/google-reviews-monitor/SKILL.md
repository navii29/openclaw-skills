# Skill: Google Reviews Monitor

## Description
Überwache Google Business Bewertungen für deine Unternehmen oder Wettbewerber. Erhalte sofort Benachrichtigungen bei neuen Reviews – nie wieder negative Bewertungen verpassen!

## Capabilities
- `google_reviews.fetch` - Hole aktuelle Reviews
- `google_reviews.monitor` - Überwache auf neue Reviews
- `google_reviews.analyze` - Analysiere Sentiment & Trends
- `google_reviews.report` - Generiere Berichte

## Problem
- Negative Google Reviews werden oft zu spät entdeckt
- Kein Überblick über Bewertungstrends
- Verpasste Chancen auf schnelle Reaktion
- Wettbewerber-Reviews nicht im Blick

## Lösung
Automatisiertes Monitoring mit Sentiment-Analyse und sofortigen Alerts bei neuen Bewertungen.

## Features
1. **Place Monitoring** - Mehrere Standorte gleichzeitig
2. **Sentiment-Analyse** - Positive/Negative Erkennung
3. **Sterne-Filter** - Alert nur bei 1-3 Sterne Bewertungen
4. **Response-Tracking** - Prüfe ob auf Reviews geantwortet wurde
5. **Wettbewerbs-Analyse** - Vergleiche mit Konkurrenten
6. **Weekly Reports** - Zusammenfassungen per Email/Telegram

## API Keys Required
- **Google Places API Key** (erforderlich)
- Optional: Telegram Bot Token
- Optional: Slack Webhook

## Setup Time
5-10 Minuten

## Use Cases
- Restaurant/Reputation Management
- Lokale SEO Optimierung
- Kundenfeedback-Tracking
- Wettbewerbs-Analyse
- Franchise-Monitoring

## Tags
google, reviews, business, reputation, monitoring, sentiment, places-api, notifications

## Configuration

### Environment Variables
```bash
# Required
export GOOGLE_PLACES_API_KEY="your_api_key"

# Notifications (optional)
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
export SLACK_WEBHOOK_URL="your_webhook"

# Optional Settings
export REVIEWS_CHECK_INTERVAL=3600  # Sekunden (default: 1h)
export REVIEWS_MIN_STARS=1          # Min Sterne für Alert (1-5)
export REVIEWS_MAX_STARS=3          # Max Sterne für Alert (1-5)
```

## Usage

### CLI
```bash
# Reviews für einen Standort abrufen
python google_reviews.py --place-id "ChIJ..."

# Nach Place Name suchen
python google_reviews.py --search "Restaurant Name, Berlin"

# Monitoring starten (config-basiert)
python google_reviews.py --monitor --config places.json

# Nur negative Reviews (1-2 Sterne)
python google_reviews.py --place-id "ChIJ..." --min-stars 1 --max-stars 2

# Analyse-Report generieren
python google_reviews.py --analyze --place-id "ChIJ..."
```

### Python API
```python
from google_reviews import GoogleReviewsMonitor

monitor = GoogleReviewsMonitor()

# Reviews abrufen
reviews = monitor.get_reviews(
    place_id="ChIJ...",
    max_results=20
)

# Monitoring mit Callback
monitor.monitor_place(
    place_id="ChIJ...",
    callback=lambda review: print(f"Neu: {review.text}")
)

# Sentiment-Analyse
sentiment = monitor.analyze_sentiment(reviews)
print(f"Positiv: {sentiment.positive}%")
```

### Config File (places.json)
```json
{
  "places": [
    {
      "name": "Mein Restaurant Berlin",
      "place_id": "ChIJ...",
      "alert_stars_min": 1,
      "alert_stars_max": 3,
      "notifications": ["telegram", "slack"]
    },
    {
      "name": "Wettbewerber A",
      "place_id": "ChIJ...",
      "alert_stars_min": 1,
      "alert_stars_max": 5,
      "notifications": ["telegram"]
    }
  ],
  "check_interval": 3600,
  "weekly_report": true
}
```

## Output Format

### Telegram Nachricht (Negative Review)
```
⭐ <b>Neue Google Bewertung</b>

⚠️ <b>1 ⭐ Bewertung</b>
🏪 Mein Restaurant Berlin

📝 "Essen war kalt, Service unfreundlich..."
👤 Max Mustermann • Vor 2 Stunden

🔗 Auf Google antworten
```

### Weekly Report
```
📊 <b>Weekly Review Report</b>
🏪 Mein Restaurant Berlin

⭐ Durchschnitt: 4.2/5 (+0.1)
📝 Neue Reviews: 12
😊 Positiv: 8 (67%)
😐 Neutral: 2 (17%)
😠 Negativ: 2 (17%)

⚡ Unbeantwortet: 3

Top Keywords:
• "guter Service" (5x)
• "leckeres Essen" (4x)
• "lange Wartezeit" (2x)
```

## API Limits
- Google Places API: 100,000 requests/day (free tier)
- Reviews: Max 5 reviews per place per request
- Empfohlenes Polling: 1x pro Stunde

## Getting API Key

1. [Google Cloud Console](https://console.cloud.google.com/) öffnen
2. Neues Projekt erstellen oder bestehendes wählen
3. **Places API** aktivieren
4. **API Key** erstellen unter "Credentials"
5. Key auf Places API einschränken (empfohlen)
6. Billing einrichten (notwendig, aber free tier ausreichend)

## Finding Place IDs

### Option 1: Tool
https://developers.google.com/maps/documentation/places/web-service/place-id

### Option 2: API
```bash
curl "https://maps.googleapis.com/maps/api/place/findplacefromtext/json?\
input=Restaurant%20Name%20Berlin\
&inputtype=textquery\
&fields=place_id,name\
&key=YOUR_API_KEY"
```

## Category Tips
- Restaurants: ChIJ... (varies by location)
- Hotels: ChIJ...
- Shops: ChIJ...
- Services: ChIJ...

## Legal Notice
- Google Places API Terms beachten
- Keine massenhafte Datenspeicherung
- Nur für legitime Geschäftszwecke
