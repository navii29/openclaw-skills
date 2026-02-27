# DHL Paket Tracker 🇩🇪

**Automatisierte DHL-Sendungsverfolgung mit Telegram-Benachrichtigungen**

Perfekt für E-Commerce-Unternehmer, Agenturen und alle, die ihre Pakete im Blick behalten wollen.

## 🚀 Schnellstart

### 1. Installation

```bash
cd skills/dhl-paket-tracker
pip install requests
chmod +x dhl_tracker.py
```

### 2. API Keys einrichten

```bash
# DHL API (kostenlos)
export DHL_API_KEY="dein_dhl_api_key"

# Telegram Bot (für Alerts)
export dhl-paket-tracker_BOT_TOKEN="dein_bot_token"
export dhl-paket-tracker_CHAT_ID="deine_chat_id"
```

**DHL API Key:** https://developer.dhl.com/ (Track API abonnieren)

**Telegram Bot:** @BotFather → /newbot → Token kopieren

**Chat ID:** Schreibe @userinfobot → ID kopieren

### 3. Testen

```bash
# Einzelnes Paket tracken
./dhl_tracker.py track 00340434161234567890

# Zur Überwachung hinzufügen
./dhl_tracker.py add 00340434161234567890 "Kundenauftrag #1234"

# Alle Pakete prüfen
./dhl_tracker.py check
```

## 📋 Befehle

| Befehl | Beschreibung |
|--------|-------------|
| `track <nr>` | Einmaliges Tracking |
| `add <nr> [--desc "..."]` | Zur Überwachung hinzufügen |
| `check` | Alle Pakete auf Änderungen prüfen |
| `list` | Alle überwachten Pakete anzeigen |
| `remove <nr>` | Aus Überwachung entfernen |

## ⏰ Automatisierung

### Cronjob (alle 30 Minuten)

```bash
# Crontab öffnen
crontab -e

# Eintrag hinzufügen
*/30 * * * * cd /pfad/zu/skills/dhl-paket-tracker && ./dhl_tracker.py check > /dev/null 2>&1
```

### Systemd Timer (empfohlen für Server)

```bash
# Service erstellen
sudo nano /etc/systemd/system/dhl-tracker.service
```

```ini
[Unit]
Description=DHL Paket Tracker

[Service]
Type=oneshot
WorkingDirectory=/pfad/zu/skills/dhl-paket-tracker
ExecStart=/usr/bin/python3 dhl_tracker.py check
Environment=DHL_API_KEY=xxx
Environment=dhl-paket-tracker_BOT_TOKEN=xxx
Environment=dhl-paket-tracker_CHAT_ID=xxx
```

```bash
# Timer erstellen
sudo nano /etc/systemd/system/dhl-tracker.timer
```

```ini
[Unit]
Description=Run DHL Tracker every 30 minutes

[Timer]
OnCalendar=*:0/30
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable dhl-tracker.timer
sudo systemctl start dhl-tracker.timer
```

## 💡 Use Cases

### E-Commerce Seller
```python
from dhl_tracker import DHLTracker

tracker = DHLTracker()

# Bei jeder Bestellung
for order in new_orders:
    tracker.add_tracking(
        order.tracking_number, 
        f"Bestellung #{order.id} - {order.customer_name}"
    )
```

### WooCommerce Integration
```php
// functions.php
add_action('woocommerce_order_status_completed', function($order_id) {
    $order = wc_get_order($order_id);
    $tracking = $order->get_meta('_tracking_number');
    
    // Rufe Python-Script auf
    exec("cd /skills/dhl-paket-tracker && ./dhl_tracker.py add {$tracking} 'WC-{$order_id}'");
});
```

### Shopify Integration
```javascript
// Webhook-Handler
app.post('/webhook/order-fulfilled', (req, res) => {
  const tracking = req.body.fulfillments[0].tracking_number;
  exec(`./dhl_tracker.py add ${tracking} "Shopify-${req.body.name}"`);
  res.sendStatus(200);
});
```

## 📱 Telegram Alerts

Empfange sofortige Benachrichtigungen bei:
- ✅ Zustellung
- 🚚 Status-Änderungen
- ⚠️ Zustellproblemen
- 📦 Annahme im Paketshop

Beispiel:
```
🚚 DHL Status-Update

📦 Kundenauftrag #1234
🔢 00340434161234567890

⬅️ Sendung eingegangen
➡️ In Transport

📍 Frankfurt, DE
🕐 27.02.2026 14:30

📅 Geschätzte Zustellung: 28.02.2026
```

## 🔧 Troubleshooting

| Problem | Lösung |
|---------|--------|
| "Authentication failed" | DHL API Key prüfen unter developer.dhl.com |
| "Sendung nicht gefunden" | Tracking-Nummer muss mit 0034 beginnen |
| Keine Telegram-Nachrichten | Bot Token und Chat ID prüfen |
| "API limit exceeded" | Max. 1.000 Calls/Monat im Free Tier |

## 📝 Tracking-Nummern-Formate

| Dienst | Format | Beispiel |
|--------|--------|----------|
| DHL Paket | 0034... | 00340434161234567890 |
| DHL Express | 10 Stellen | 1234567890 |

## 🆕 Roadmap

- [ ] DPD Integration
- [ ] Hermes Integration
- [ ] UPS Integration
- [ ] GLS Integration
- [ ] Web-Dashboard
- [ ] Zustellungs-Prognose

## 📄 Lizenz

MIT License - Made with ❤️ for the German market

---

**Fragen?** Erstelle ein Issue oder kontaktiere uns!
