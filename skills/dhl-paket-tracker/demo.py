#!/usr/bin/env python3
"""
Demo-Skript für DHL Paket Tracker
Zeigt alle Funktionen mit Mock-Daten (keine echte API nötig)
"""

import os
import sys

# Füge parent dir zum Path hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import patch, MagicMock
from dhl_tracker import DHLTracker


def demo_translate_status():
    """Demo: Deutsche Status-Übersetzungen"""
    print("\n" + "="*60)
    print("📋 DEMO: Status-Übersetzungen")
    print("="*60)
    
    tracker = DHLTracker.__new__(DHLTracker)
    
    statuses = ["pre-transit", "transit", "delivered", "failure", "return-transit"]
    
    for status in statuses:
        translated = tracker._translate_status(status)
        print(f"  {status:<15} → {translated}")


def demo_formatting():
    """Demo: Deutsche Formatierung"""
    print("\n" + "="*60)
    print("📋 DEMO: Deutsche Datums-/Orts-Formatierung")
    print("="*60)
    
    tracker = DHLTracker.__new__(DHLTracker)
    
    # Zeit-Formatierung
    timestamps = [
        "2026-02-27T14:30:00Z",
        "2026-02-27T14:30:00+01:00",
        None
    ]
    
    print("\nZeit-Formatierung:")
    for ts in timestamps:
        formatted = tracker._format_time(ts)
        print(f"  {str(ts):<35} → {formatted}")
    
    # Orts-Formatierung
    locations = [
        {"address": {"addressLocality": "Berlin", "countryCode": "DE"}},
        {"address": {"addressLocality": "München"}},
        {}
    ]
    
    print("\nOrts-Formatierung:")
    for loc in locations:
        formatted = tracker._format_location(loc)
        city = loc.get("address", {}).get("addressLocality", "N/A")
        print(f"  {city:<15} → {formatted}")


def demo_telegram_message():
    """Demo: Telegram Nachrichten-Format"""
    print("\n" + "="*60)
    print("📱 DEMO: Telegram Benachrichtigung")
    print("="*60)
    
    # Simulierte Daten
    message = """🚚 <b>DHL Status-Update</b>

📦 <b>Bestellung #1234 - Max Mustermann</b>
🔢 00340434161234567890

⬅️ <i>📦 Sendung eingegangen</i>
➡️ <b>🚚 In Transport</b>

📍 Frankfurt, DE
🕐 27.02.2026 14:30

📅 Geschätzte Zustellung: 28.02.2026
"""
    
    print("\nAussehen der Telegram-Nachricht:")
    print("-" * 40)
    print(message)
    print("-" * 40)


def demo_workflow():
    """Demo: Kompletter Workflow"""
    print("\n" + "="*60)
    print("🔄 DEMO: Kompletter Workflow")
    print("="*60)
    
    with patch.dict(os.environ, {
        "DHL_API_KEY": "demo_key",
        "dhl-paket-tracker_BOT_TOKEN": "demo_token",
        "dhl-paket-tracker_CHAT_ID": "123456789"
    }):
        with patch('dhl_tracker.DB_FILE', 'demo_tracking_db.json'):
            tracker = DHLTracker()
            
            # Mock API Response
            def mock_track(tracking_number):
                return {
                    "tracking_number": tracking_number,
                    "status": "🚚 In Transport",
                    "description": "Die Sendung wurde verladen",
                    "timestamp": "2026-02-27T14:30:00Z",
                    "location": "Berlin, DE",
                    "estimated_delivery": "2026-02-28T18:00:00Z",
                    "events": [
                        {
                            "timestamp": "2026-02-27T14:30:00Z",
                            "status": "transit",
                            "description": "Die Sendung wurde verladen",
                            "location": "Berlin, DE"
                        },
                        {
                            "timestamp": "2026-02-27T10:00:00Z",
                            "status": "pre-transit",
                            "description": "Sendung eingegangen",
                            "location": "Hamburg, DE"
                        }
                    ]
                }
            
            tracker.track = mock_track
            
            print("\n1️⃣ Paket zur Überwachung hinzufügen:")
            tracker.add_tracking("00340434161234567890", "Kundenauftrag #1234")
            
            print("\n2️⃣ Alle Pakete anzeigen:")
            tracker.list_all()
            
            # Simuliere Status-Änderung
            print("\n3️⃣ Status-Änderung simulieren:")
            tracker.db["00340434161234567890"]["last_status"] = "📦 Sendung eingegangen"
            
            def mock_track_updated(tracking_number):
                return {
                    "tracking_number": tracking_number,
                    "status": "✅ Zugestellt",  # Neuer Status!
                    "description": "Die Sendung wurde zugestellt",
                    "timestamp": "2026-02-27T16:45:00Z",
                    "location": "München, DE",
                    "estimated_delivery": None,
                    "events": [
                        {
                            "timestamp": "2026-02-27T16:45:00Z",
                            "status": "delivered",
                            "description": "Die Sendung wurde zugestellt",
                            "location": "München, DE"
                        }
                    ]
                }
            
            tracker.track = mock_track_updated
            
            with patch('dhl_tracker.requests.post') as mock_post:
                mock_post.return_value = MagicMock(raise_for_status=MagicMock())
                changes = tracker.check_all()
                print(f"\n   📱 Telegram-Nachricht würde gesendet: {len(changes)} Änderung(en)")
            
            print("\n4️⃣ Paket entfernen:")
            tracker.remove("00340434161234567890")
    
    # Cleanup
    if os.path.exists('demo_tracking_db.json'):
        os.remove('demo_tracking_db.json')


def demo_use_cases():
    """Demo: Use Cases"""
    print("\n" + "="*60)
    print("💡 DEMO: Anwendungsfälle")
    print("="*60)
    
    use_cases = """
🏪 E-Commerce Seller:
   → Automatisches Tracking aller ausgehenden Sendungen
   → Kunden benachrichtigen bei Status-Änderungen
   → Retouren im Blick behalten

🏢 Agenturen:
   → Kundenlieferungen überwachen
   → Proaktiver Support bei Zustellproblemen
   → Reporting für Einkaufsabteilungen

🏠 Private Nutzer:
   → Nie mehr Pakete verpassen
   → Alle Sendungen an einem Ort
   → Sofort-Alert bei Zustellung

📦 Einkaufsabteilungen:
   → Bestellungen tracken
   → Lieferverzögerungen früh erkennen
   → Supplier-Performance messen
"""
    
    print(use_cases)


def main():
    """Haupt-Demo"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   📦 DHL PAKET TRACKER - DEMO                            ║
║   Deutscher Markt | Telegram Alerts | E-Commerce Ready   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    demo_translate_status()
    demo_formatting()
    demo_telegram_message()
    demo_workflow()
    demo_use_cases()
    
    print("\n" + "="*60)
    print("✅ DEMO ABGESCHLOSSEN")
    print("="*60)
    print("""
Nächste Schritte:
1. API Key besorgen: https://developer.dhl.com/
2. cp .env.example .env
3. .env mit deinen Keys füllen
4. ./dhl_tracker.py track 0034043416XXXXXXXXXX

Happy Tracking! 🚚
""")


if __name__ == "__main__":
    main()
