#!/usr/bin/env python3
"""
Website Lead Scraper + Telegram Alerts
Monitor websites for new leads and send instant Telegram notifications.
"""

import requests
import re
import json
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Lead:
    """Represents a captured lead."""
    source: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    timestamp: str = ""
    priority: str = "normal"
    keywords_found: List[str] = None
    
    def __post_init__(self):
        if self.keywords_found is None:
            self.keywords_found = []
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    @property
    def unique_id(self) -> str:
        """Generate unique ID for deduplication."""
        content = f"{self.source}{self.email}{self.message}"[:100]
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    @property
    def summary(self) -> str:
        """Short summary for notifications."""
        name = self.name or "Unbekannt"
        msg = (self.message or "")[:50]
        return f"{name}: {msg}..."


class LeadScraper:
    """Scrape and monitor websites for leads."""
    
    # High-value keywords for priority detection (German)
    HIGH_PRIORITY_KEYWORDS = [
        'angebot', 'kostenvoranschlag', 'preis', 'budget',
        'sofort', 'dringend', 'eilig', 'schnellstmöglich',
        'projekt', 'website', 'webseite', 'shop', 'onlineshop',
        'marketing', 'seo', 'werbung', 'beratung'
    ]
    
    # Contact form selectors/patterns
    FORM_PATTERNS = [
        r'name[=":\s]+["\']?([^"\'>\s]+)',
        r'email[=":\s]+["\']?([^"\'>\s]+)',
        r'telefon[=":\s]+["\']?([^"\'>\s]+)',
        r'nachricht[=":\s]+["\']?([^"\'>]+)',
    ]
    
    def __init__(self, state_file: str = "lead_state.json"):
        self.state_file = state_file
        self.seen_ids: Set[str] = self._load_state()
    
    def _load_state(self) -> Set[str]:
        """Load previously seen lead IDs."""
        try:
            if Path(self.state_file).exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('seen_ids', []))
        except Exception as e:
            print(f"Warning: Could not load state: {e}")
        return set()
    
    def _save_state(self):
        """Save seen lead IDs."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'seen_ids': list(self.seen_ids),
                    'last_update': datetime.now().isoformat()
                }, f)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")
    
    def extract_leads_from_html(self, html: str, source_url: str) -> List[Lead]:
        """Extract lead information from HTML."""
        leads = []
        
        # Simple extraction - in production would use proper parsing
        # Look for email patterns
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, html)
        
        # Look for phone patterns (German)
        phone_pattern = r'(?:\+49|0)[\d\s\-/]{6,20}'
        phones = re.findall(phone_pattern, html)
        
        # Look for contact form submissions in JSON/script tags
        json_pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
        json_matches = re.findall(json_pattern, html, re.DOTALL)
        
        for match in json_matches:
            try:
                data = json.loads(match)
                # Recursively search for contact data
                self._extract_from_dict(data, source_url, leads)
            except:
                pass
        
        # If no structured data found, create generic lead
        if not leads and (emails or phones):
            lead = Lead(
                source=source_url,
                email=emails[0] if emails else None,
                phone=phones[0] if phones else None
            )
            leads.append(lead)
        
        return leads
    
    def _extract_from_dict(self, data: dict, source: str, leads: List[Lead]):
        """Recursively extract lead data from dict."""
        if isinstance(data, dict):
            # Check for contact/lead keys
            contact_keys = ['contact', 'lead', 'inquiry', 'submission', 'kontakt', 'anfrage']
            for key in contact_keys:
                if key in data:
                    entry = data[key]
                    if isinstance(entry, dict):
                        lead = self._dict_to_lead(entry, source)
                        if lead:
                            leads.append(lead)
                    elif isinstance(entry, list):
                        for item in entry:
                            if isinstance(item, dict):
                                lead = self._dict_to_lead(item, source)
                                if lead:
                                    leads.append(lead)
            
            # Recurse
            for value in data.values():
                if isinstance(value, (dict, list)):
                    self._extract_from_dict(value, source, leads)
        elif isinstance(data, list):
            for item in data:
                self._extract_from_dict(item, source, leads)
    
    def _dict_to_lead(self, data: dict, source: str) -> Optional[Lead]:
        """Convert dict to Lead object."""
        # Map common field names
        name = data.get('name') or data.get('fullName') or data.get('vorname') or data.get('nachname')
        email = data.get('email') or data.get('eMail') or data.get('mail')
        phone = data.get('phone') or data.get('telefon') or data.get('tel') or data.get('mobile')
        message = data.get('message') or data.get('nachricht') or data.get('comment') or data.get('anfrage')
        
        if email or phone:
            lead = Lead(
                source=source,
                name=name,
                email=email,
                phone=phone,
                message=message
            )
            lead = self._analyze_priority(lead)
            return lead
        return None
    
    def _analyze_priority(self, lead: Lead) -> Lead:
        """Analyze lead priority based on keywords."""
        text = f"{lead.message or ''} {lead.email or ''}".lower()
        
        found_keywords = []
        for keyword in self.HIGH_PRIORITY_KEYWORDS:
            if keyword in text:
                found_keywords.append(keyword)
        
        lead.keywords_found = found_keywords
        
        # Set priority
        if len(found_keywords) >= 3:
            lead.priority = "🔥 KRITISCH"
        elif len(found_keywords) >= 1:
            lead.priority = "⚡ HOCH"
        else:
            lead.priority = "📌 NORMAL"
        
        return lead
    
    def check_website(self, url: str) -> List[Lead]:
        """Check website for new leads."""
        try:
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            leads = self.extract_leads_from_html(response.text, url)
            
            # Filter only new leads
            new_leads = []
            for lead in leads:
                if lead.unique_id not in self.seen_ids:
                    new_leads.append(lead)
                    self.seen_ids.add(lead.unique_id)
            
            self._save_state()
            return new_leads
            
        except Exception as e:
            print(f"Error checking {url}: {e}")
            return []


class TelegramNotifier:
    """Send lead notifications via Telegram."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def format_message(self, lead: Lead) -> str:
        """Format lead for Telegram."""
        name = lead.name or "👤 Unbekannt"
        email = lead.email or "Nicht angegeben"
        phone = lead.phone or "Nicht angegeben"
        message = (lead.message or "Keine Nachricht")[:200]
        source = lead.source.replace('https://', '').replace('http://', '')[:50]
        
        emoji = "🎯"
        if "KRITISCH" in lead.priority:
            emoji = "🚨"
        elif "HOCH" in lead.priority:
            emoji = "⚡"
        
        keywords = ", ".join(lead.keywords_found[:5]) if lead.keywords_found else "Keine"
        
        return f"""{emoji} <b>NEUER LEAD!</b>

<b>👤 Name:</b> {name}
<b>📧 Email:</b> {email}
<b>📱 Telefon:</b> {phone}

<b>💬 Nachricht:</b>
<i>{message}</i>

<b>🔥 Priorität:</b> {lead.priority}
<b>🔑 Keywords:</b> {keywords}
<b>🌐 Quelle:</b> {source}
<b>🕐 Zeit:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
    
    def send_notification(self, lead: Lead) -> bool:
        """Send lead notification."""
        url = f"{self.api_url}/sendMessage"
        
        payload = {
            "chat_id": self.chat_id,
            "text": self.format_message(lead),
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200 and response.json().get('ok')
        except Exception as e:
            print(f"Error sending Telegram notification: {e}")
            return False
    
    def send_batch_notification(self, leads: List[Lead]) -> int:
        """Send multiple notifications, return count sent."""
        sent = 0
        for lead in leads:
            if self.send_notification(lead):
                sent += 1
                time.sleep(0.5)  # Rate limiting
        return sent


class LeadMonitor:
    """Main monitoring orchestrator."""
    
    def __init__(self, telegram_token: str, telegram_chat: str):
        self.scraper = LeadScraper()
        self.notifier = TelegramNotifier(telegram_token, telegram_chat)
    
    def monitor(self, urls: List[str]) -> Dict:
        """Monitor multiple websites for leads."""
        print(f"🔍 Monitoring {len(urls)} websites...\n")
        
        all_new_leads = []
        
        for url in urls:
            print(f"📡 Checking: {url}")
            leads = self.scraper.check_website(url)
            if leads:
                print(f"   🎯 Found {len(leads)} new lead(s)")
                all_new_leads.extend(leads)
            else:
                print(f"   ✓ No new leads")
        
        print(f"\n📊 Total new leads: {len(all_new_leads)}")
        
        # Send notifications
        if all_new_leads:
            print("📤 Sending Telegram notifications...")
            sent = self.notifier.send_batch_notification(all_new_leads)
            print(f"   ✅ Sent {sent}/{len(all_new_leads)} notifications")
        
        return {
            "websites_checked": len(urls),
            "new_leads": len(all_new_leads),
            "notifications_sent": len(all_new_leads)  # Simplified
        }


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Website Lead Scraper + Telegram Alerts')
    parser.add_argument('--token', required=True, help='Telegram Bot Token')
    parser.add_argument('--chat', required=True, help='Telegram Chat ID')
    parser.add_argument('--urls', nargs='+', required=True, help='URLs to monitor')
    parser.add_argument('--interval', type=int, help='Monitoring interval in seconds (for daemon mode)')
    
    args = parser.parse_args()
    
    monitor = LeadMonitor(args.token, args.chat)
    
    if args.interval:
        # Daemon mode
        print(f"🤖 Daemon mode: checking every {args.interval}s")
        while True:
            monitor.monitor(args.urls)
            print(f"⏳ Sleeping {args.interval}s...\n")
            time.sleep(args.interval)
    else:
        # One-time check
        result = monitor.monitor(args.urls)
        
        # Save report
        report_file = f"lead_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Report saved: {report_file}")


if __name__ == "__main__":
    main()
