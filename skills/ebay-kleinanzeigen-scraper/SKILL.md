# Skill: eBay Kleinanzeigen Scraper

## Description
Überwache eBay Kleinanzeigen automatisch nach neuen Angeboten. Erhalte sofort Benachrichtigungen wenn Produkte deiner Wunschliste verfügbar werden – ideal für Schnäppchenjäger und Reseller.

## Capabilities
- `kleinanzeigen.search` - Suche nach Anzeigen
- `kleinanzeigen.monitor` - Überwache Suche nach neuen Einträgen
- `kleinanzeigen.scrape_details` - Extrahiere Detail-Informationen

## Problem
- Gute Angebote auf eBay Kleinanzeigen sind oft nach Minuten weg
- Manuelles Suchen mehrmals täglich ist zeitaufwändig
- Wichtige Angebote werden verpasst

## Lösung
Automatisierte Scraping-Lösung mit intelligentem Caching und sofortigen Alerts.

## Features
1. **Keyword-basierte Suche** - Mehrere Suchbegriffe gleichzeitig
2. **Preis-Filter** - Min/Max Preis pro Suche
3. **Kategorien-Filter** - Elektronik, Möbel, Autos, etc.
4. **Standort-Filter** - Umkreis-Suche mit PLZ
5. **Deduplizierung** - Keine doppelten Benachrichtigungen
6. **Bilder-Extraktion** - Vorschaubilder in Notifications

## API Keys Required
- Keine API Keys nötig (Web Scraping)
- Optional: Telegram Bot Token für Notifications
- Optional: Slack Webhook für Notifications

## Setup Time
5-10 Minuten

## Use Cases
- Preis-Schnäppchen finden
- Seltene Sammlerstücke tracken
- Auto/Motorrad Deals
- Immobilien-Markt beobachten
- Reseller Opportunities

## Tags
ebay, kleinanzeigen, scraper, deals, monitoring, telegram, notifications, price-tracking

## Configuration

### Environment Variables
```bash
# Notifications (optional)
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
SLACK_WEBHOOK_URL=your_slack_webhook

# Optional: Rate limiting
KLEINANZEIGEN_DELAY=3  # Sekunden zwischen Requests
KLEINANZEIGEN_MAX_PAGES=5  # Max Seiten pro Suche
```

## Usage

### CLI
```bash
# Einmalige Suche
python ebay_kleinanzeigen.py --search "iPhone 15 Pro" --max-price 800

# Mit Standort-Filter
python ebay_kleinanzeigen.py --search "Vespa" --city "Berlin" --radius 50

# Mehrere Suchbegriffe (aus JSON)
python ebay_kleinanzeigen.py --config searches.json

# Überwachungs-Modus (alle 10 Min)
python ebay_kleinanzeigen.py --monitor --config searches.json --interval 600

# Kategorie-Suche
python ebay_kleinanzeigen.py --search "MacBook" --category 161  # Elektronik
```

### Python API
```python
from ebay_kleinanzeigen import KleinanzeigenScraper

scraper = KleinanzeigenScraper()

# Einfache Suche
results = scraper.search(
    query="PlayStation 5",
    max_price=500,
    city="München",
    radius=20
)

# Monitoring
scraper.monitor_search(
    query="Lego Star Wars",
    callback=lambda ad: print(f"Neu: {ad.title}")
)
```

### Config File (searches.json)
```json
{
  "searches": [
    {
      "query": "iPhone 15 Pro",
      "max_price": 900,
      "min_price": 500,
      "category": 161,
      "city": "Berlin",
      "radius": 30,
      "keywords": ["256GB", "Unlocked"]
    },
    {
      "query": "Vespa GTS 300",
      "max_price": 4000,
      "category": 305,
      "city": "Hamburg",
      "radius": 100
    }
  ],
  "notifications": {
    "telegram": true,
    "slack": false
  },
  "check_interval": 300
}
```

## Output Format

### Telegram Nachricht
```
🔍 <b>Neues eBay Kleinanzeigen Angebot</b>

📱 iPhone 15 Pro 256GB - Neuwertig
💰 <b>750 € VB</b>
📍 Berlin (10115)
👤 MaxMüller123

📝 Verkaufe mein iPhone 15 Pro in Neuwertigem Zustand...

🔗 https://www.kleinanzeigen.de/s-anzeige/...
```

## Rate Limits
- eBay Kleinanzeigen hat keine offizielle API
- Empfohlene Delays: 3-5 Sekunden zwischen Requests
- Max 50 Seiten pro Stunde empfohlen

## Legal Notice
Dieses Tool ist für private Nutzung gedacht. Respektiere die AGB von eBay Kleinanzeigen und überlaste die Server nicht.

## Category IDs
- 161 - Elektronik
- 176 - Handys
- 245 - Computer
- 80 - Möbel
- 305 - Motorräder & Roller
- 210 - Autos
- 297 - Immobilien

Vollständige Liste: https://www.ebay-kleinanzeigen.de/s-kategorien.html
