#!/usr/bin/env python3
"""
DHL Paket Tracker - German Market Focus
Automatisierte Sendungsverfolgung mit Telegram Alerts
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Optional, Dict, List

# Constants
DHL_API_URL = "https://api-eu.dhl.com/track/shipments"
DB_FILE = "tracking_db.json"

class DHLTracker:
    """DHL Paket Tracking mit Status-Change Detection"""
    
    def __init__(self):
        self.api_key = os.getenv("DHL_API_KEY")
        self.bot_token = os.getenv("dhl-paket-tracker_BOT_TOKEN")
        self.chat_id = os.getenv("dhl-paket-tracker_CHAT_ID")
        self.db = self._load_db()
        
        if not self.api_key:
            raise ValueError("DHL_API_KEY nicht gesetzt!")
    
    def _load_db(self) -> Dict:
        """Lade Tracking-Datenbank"""
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_db(self):
        """Speichere Tracking-Datenbank"""
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=2, ensure_ascii=False)
    
    def track(self, tracking_number: str) -> Optional[Dict]:
        """
        Track ein einzelnes Paket via DHL API
        
        Args:
            tracking_number: DHL Tracking-Nummer (z.B. 00340434161234567890)
            
        Returns:
            Dict mit Tracking-Informationen oder None bei Fehler
        """
        headers = {
            "DHL-API-Key": self.api_key,
            "Accept": "application/json"
        }
        
        params = {
            "trackingNumber": tracking_number
        }
        
        try:
            response = requests.get(
                DHL_API_URL,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("shipments"):
                return self._parse_shipment(data["shipments"][0])
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API Fehler: {e}")
            return None
    
    def _parse_shipment(self, shipment: Dict) -> Dict:
        """Parse DHL API Response in lesbares Format"""
        status = shipment.get("status", {})
        events = shipment.get("events", [])
        
        # Letztes Event = aktueller Status
        latest_event = events[0] if events else {}
        
        return {
            "tracking_number": shipment.get("id"),
            "status_code": status.get("statusCode"),
            "status": self._translate_status(status.get("status")),
            "description": latest_event.get("description"),
            "timestamp": latest_event.get("timestamp"),
            "location": self._format_location(latest_event.get("location", {})),
            "estimated_delivery": shipment.get("estimatedTimeOfDelivery"),
            "events": [
                {
                    "timestamp": e.get("timestamp"),
                    "status": e.get("status"),
                    "description": e.get("description"),
                    "location": self._format_location(e.get("location", {}))
                }
                for e in events[:5]  # Nur letzte 5 Events
            ]
        }
    
    def _translate_status(self, status: str) -> str:
        """Übersetze DHL Status-Codes ins Deutsche"""
        translations = {
            "pre-transit": "📦 Sendung eingegangen",
            "transit": "🚚 In Transport",
            "delivered": "✅ Zugestellt",
            "failure": "⚠️ Zustellproblem",
            "return-transit": "🔄 Rücksendung",
            "returned": "↩️ Zurückgesendet"
        }
        return translations.get(status, f"📋 {status}")
    
    def _format_location(self, location: Dict) -> str:
        """Formattiere Standort-Information"""
        parts = []
        if location.get("address", {}).get("addressLocality"):
            parts.append(location["address"]["addressLocality"])
        if location.get("address", {}).get("countryCode"):
            parts.append(location["address"]["countryCode"])
        return ", ".join(parts) if parts else "Unbekannt"
    
    def add_tracking(self, tracking_number: str, description: str = "") -> bool:
        """
        Füge Tracking-Nummer zur Überwachung hinzu
        
        Args:
            tracking_number: DHL Tracking-Nummer
            description: Optionale Beschreibung (z.B. Kundenauftrag #123)
            
        Returns:
            True wenn erfolgreich
        """
        # Validierung
        if not tracking_number or len(tracking_number) < 10:
            print("❌ Ungültige Tracking-Nummer")
            return False
        
        # Teste Tracking zuerst
        result = self.track(tracking_number)
        if not result:
            print(f"❌ Sendung {tracking_number} nicht gefunden")
            return False
        
        self.db[tracking_number] = {
            "description": description or f"Paket {tracking_number[-4:]}",
            "added_at": datetime.now().isoformat(),
            "last_status": result["status"],
            "last_check": datetime.now().isoformat(),
            "history": [result]
        }
        
        self._save_db()
        print(f"✅ {tracking_number} zur Überwachung hinzugefügt")
        print(f"   Status: {result['status']}")
        if result.get('estimated_delivery'):
            print(f"   Geschätzte Zustellung: {result['estimated_delivery']}")
        return True
    
    def check_all(self) -> List[Dict]:
        """
        Prüfe alle überwachten Pakete auf Status-Änderungen
        
        Returns:
            Liste der Pakete mit Status-Änderungen
        """
        changes = []
        
        for tracking_number, data in self.db.items():
            print(f"🔍 Prüfe {tracking_number}...", end=" ")
            
            result = self.track(tracking_number)
            if not result:
                print("⚠️ Nicht gefunden")
                continue
            
            current_status = result["status"]
            previous_status = data.get("last_status", "")
            
            if current_status != previous_status:
                print(f"🔄 UPDATE: {previous_status} → {current_status}")
                
                # Update DB
                self.db[tracking_number]["last_status"] = current_status
                self.db[tracking_number]["last_check"] = datetime.now().isoformat()
                self.db[tracking_number]["history"].insert(0, result)
                
                # Notification
                self._send_notification(tracking_number, result, previous_status)
                
                changes.append({
                    "tracking_number": tracking_number,
                    "old_status": previous_status,
                    "new_status": current_status,
                    "data": result
                })
            else:
                print(f"✓ {current_status}")
                self.db[tracking_number]["last_check"] = datetime.now().isoformat()
        
        self._save_db()
        return changes
    
    def _send_notification(self, tracking_number: str, data: Dict, old_status: str):
        """Sende Telegram Benachrichtigung bei Status-Änderung"""
        if not self.bot_token or not self.chat_id:
            print("   ⚠️ Telegram nicht konfiguriert")
            return
        
        desc = self.db.get(tracking_number, {}).get("description", "Paket")
        
        emoji = "🚚"
        if "Zugestellt" in data["status"]:
            emoji = "✅"
        elif "Problem" in data["status"]:
            emoji = "⚠️"
        elif "Transport" in data["status"]:
            emoji = "🚛"
        
        message = f"""{emoji} <b>DHL Status-Update</b>

📦 <b>{desc}</b>
🔢 {tracking_number}

⬅️ <i>{old_status}</i>
➡️ <b>{data['status']}</b>

📍 {data.get('location', 'Unbekannt')}
🕐 {self._format_time(data.get('timestamp'))}
"""
        
        if data.get('estimated_delivery'):
            message += f"\n📅 Geschätzte Zustellung: {data['estimated_delivery'][:10]}"
        
        self._send_telegram(message)
    
    def _send_telegram(self, message: str):
        """Sende Nachricht an Telegram"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            print("   📱 Telegram gesendet")
        except Exception as e:
            print(f"   ❌ Telegram Fehler: {e}")
    
    def _format_time(self, timestamp: str) -> str:
        """Formatiere Timestamp für deutsche Anzeige"""
        if not timestamp:
            return "Unbekannt"
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%d.%m.%Y %H:%M")
        except:
            return timestamp[:16] if timestamp else "Unbekannt"
    
    def list_all(self):
        """Zeige alle überwachten Pakete"""
        if not self.db:
            print("Keine Pakete in Überwachung")
            return
        
        print(f"\n📦 {len(self.db)} Pakete in Überwachung:\n")
        print(f"{'Tracking-Nr':<25} {'Beschreibung':<25} {'Status':<25} {'Letzte Prüfung'}")
        print("-" * 100)
        
        for tn, data in self.db.items():
            desc = data.get("description", "")[:23]
            status = data.get("last_status", "")[:23]
            checked = data.get("last_check", "")[:16] if data.get("last_check") else "Nie"
            print(f"{tn:<25} {desc:<25} {status:<25} {checked}")
    
    def remove(self, tracking_number: str) -> bool:
        """Entferne Paket aus Überwachung"""
        if tracking_number in self.db:
            del self.db[tracking_number]
            self._save_db()
            print(f"✅ {tracking_number} entfernt")
            return True
        print(f"❌ {tracking_number} nicht gefunden")
        return False


def main():
    """CLI Interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DHL Paket Tracker")
    parser.add_argument("command", choices=["track", "add", "check", "list", "remove"],
                       help="Auszuführender Befehl")
    parser.add_argument("tracking_number", nargs="?", help="DHL Tracking-Nummer")
    parser.add_argument("--desc", "-d", default="", help="Beschreibung des Pakets")
    
    args = parser.parse_args()
    
    tracker = DHLTracker()
    
    if args.command == "track":
        if not args.tracking_number:
            print("❌ Tracking-Nummer erforderlich")
            sys.exit(1)
        
        result = tracker.track(args.tracking_number)
        if result:
            print(f"\n📦 Tracking-Ergebnis für {args.tracking_number}:\n")
            print(f"Status: {result['status']}")
            print(f"Beschreibung: {result.get('description', 'N/A')}")
            print(f"Standort: {result.get('location', 'N/A')}")
            print(f"Zeit: {tracker._format_time(result.get('timestamp'))}")
            
            if result.get('events'):
                print("\n📜 Letzte Events:")
                for event in result['events'][:3]:
                    print(f"  • {tracker._format_time(event.get('timestamp'))}: {event.get('description', 'N/A')}")
        else:
            print("❌ Sendung nicht gefunden")
            sys.exit(1)
    
    elif args.command == "add":
        if not args.tracking_number:
            print("❌ Tracking-Nummer erforderlich")
            sys.exit(1)
        tracker.add_tracking(args.tracking_number, args.desc)
    
    elif args.command == "check":
        changes = tracker.check_all()
        if changes:
            print(f"\n🔄 {len(changes)} Status-Änderung(en) erkannt")
        else:
            print("\n✅ Keine Änderungen")
    
    elif args.command == "list":
        tracker.list_all()
    
    elif args.command == "remove":
        if not args.tracking_number:
            print("❌ Tracking-Nummer erforderlich")
            sys.exit(1)
        tracker.remove(args.tracking_number)


if __name__ == "__main__":
    main()
