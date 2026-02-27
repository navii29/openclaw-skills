# DHL Paket Tracker

## Overview

Automatisiertes DHL-Sendungsverfolgungssystem mit Telegram-Benachrichtigungen. Trackt Pakete, erkennt Statusänderungen und sendet sofort Alerts.

**German Market Focus:** DHL ist der dominierende Paketdienstleister in Deutschland (~50% Marktanteil).

## Use Cases

- **E-Commerce Seller:** Automatisches Tracking aller ausgehenden Sendungen
- **Agenturen:** Überwachung von Kundenlieferungen
- **Private Nutzer:** Nie mehr Pakete verpassen
- **Einkaufsabteilungen:** Bestellungen im Blick behalten

## Features

| Feature | Status |
|---------|--------|
| DHL Sendungsverfolgung via API | ✅ |
| Telegram Notifications | ✅ |
| Status-Change Detection | ✅ |
| Multi-Paket Tracking | ✅ |
| Deutsche Status-Meldungen | ✅ |
| Zustellungs-Prognose | ✅ |

## Requirements

```bash
pip install requests python-telegram-bot
```

## Environment Variables

```
DHL_API_KEY=your_dhl_api_key          # DHL Entwickler Portal
dhl-paket-tracker_BOT_TOKEN=xxx       # Telegram Bot Token
dhl-paket-tracker_CHAT_ID=xxx         # Telegram Chat ID
```

## Quick Start

```python
from dhl_tracker import DHLTracker

tracker = DHLTracker()

# Einzelnes Paket tracken
result = tracker.track("00340434161234567890")
print(result)

# Neues Paket zur Überwachung hinzufügen
tracker.add_tracking("00340434161234567890", "Kundenauftrag #1234")

# Alle Pakete prüfen (Status-Änderungen werden gemeldet)
tracker.check_all()
```

## DHL API Setup

1. Registrieren unter: https://developer.dhl.com/
2. "Track API" abonnieren (kostenlos bis 1.000 Calls/Monat)
3. API Key generieren

## CLI Usage

```bash
# Paket tracken
python dhl_tracker.py track 00340434161234567890

# Zur Überwachung hinzufügen
python dhl_tracker.py add 00340434161234567890 "Mein Paket"

# Alle überwachten Pakete prüfen
python dhl_tracker.py check

# Liste aller Pakete
python dhl_tracker.py list
```

## Data Structure

Pakete werden in `tracking_db.json` gespeichert:
```json
{
  "00340434161234567890": {
    "description": "Kundenauftrag #1234",
    "last_status": "Zugestellt",
    "last_update": "2026-02-27T14:30:00",
    "history": [...]
  }
}
```

## Telegram Messages

![Zustellung](https://i.imgur.com/example1.png)
*Automatische Benachrichtigung bei Statusänderung*

## Rate Limits

- DHL API: 1.000 Calls/Monat (Free Tier)
- Empfohlen: Check alle 30 Minuten für aktive Pakete

## German Status Codes

| DHL Status | Bedeutung |
|------------|-----------|
| pre-transit | Sendung eingegangen |
| transit | In Zustellung |
| delivered | Zugestellt |
| failure | Zustellproblem |

## Integration Examples

### Mit WooCommerce
```python
# Bei Bestellung automatisch tracken
tracker.add_tracking(order.tracking_number, f"Bestellung #{order.id}")
```

### Als Cronjob (alle 30 Min)
```bash
*/30 * * * * cd /skills/dhl-paket-tracker && python dhl_tracker.py check
```

## Troubleshooting

**Problem:** "Authentication failed"
→ Lösung: DHL API Key prüfen unter https://developer.dhl.com/

**Problem:** "Sendung nicht gefunden"
→ Lösung: DHL-Tracking-Nummern beginnen meist mit 0034...

## Roadmap

- [ ] DPD Integration
- [ ] UPS Integration  
- [ ] Hermes Integration
- [ ] Zustellungszeit-Prognose ML
- [ ] Web-Dashboard

## License

MIT - Für den deutschen E-Commerce-Markt optimiert 🇩🇪
