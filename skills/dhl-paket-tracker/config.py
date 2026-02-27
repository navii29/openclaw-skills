# DHL Paket Tracker

__version__ = "1.0.0"
__author__ = "Navii Automation"
__description__ = "Automatisierte DHL-Sendungsverfolgung mit Telegram Alerts"

# Deutsche Status-Übersetzungen
STATUS_TRANSLATIONS = {
    "pre-transit": "📦 Sendung eingegangen",
    "transit": "🚚 In Transport",
    "delivered": "✅ Zugestellt",
    "failure": "⚠️ Zustellproblem",
    "return-transit": "🔄 Rücksendung",
    "returned": "↩️ Zurückgesendet"
}

# Emoji Mapping für Status
STATUS_EMOJIS = {
    "delivered": "✅",
    "failure": "⚠️",
    "transit": "🚚",
    "pre-transit": "📦",
    "return-transit": "🔄",
    "returned": "↩️"
}

# DHL API Endpoints
DHL_API_BASE = "https://api-eu.dhl.com"
DHL_TRACK_ENDPOINT = "/track/shipments"

# Rate Limiting
MAX_REQUESTS_PER_MONTH = 1000  # DHL Free Tier
DEFAULT_CHECK_INTERVAL = 30  # Minuten

# Datenbank
DB_FILE = "tracking_db.json"
MAX_HISTORY_ENTRIES = 50
