#!/usr/bin/env python3
"""
Competitor Intelligence Monitor v1.0.0
Automated competitor monitoring with AI-powered insights.

Usage:
    python competitor_monitor.py --setup
    python competitor_monitor.py --scan
    python competitor_monitor.py --scan --competitor competitor1
    python competitor_monitor.py --report --weekly
"""

import argparse
import json
import os
import sys
import time
import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import re

# Try to import optional dependencies
try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

# Configuration paths
CONFIG_DIR = Path.home() / ".openclaw" / "competitor-intelligence"
CONFIG_FILE = CONFIG_DIR / "config.json"
DB_FILE = CONFIG_DIR / "monitor.db"
SNAPSHOTS_DIR = CONFIG_DIR / "snapshots"

@dataclass
class PriceData:
    product: str
    price: float
    currency: str
    timestamp: datetime
    url: str
    
    def to_dict(self):
        return {
            "product": self.product,
            "price": self.price,
            "currency": self.currency,
            "timestamp": self.timestamp.isoformat(),
            "url": self.url
        }

@dataclass
class Change:
    competitor: str
    change_type: str  # 'price', 'homepage', 'news', 'product'
    product: Optional[str]
    old_value: Optional[str]
    new_value: str
    change_percent: Optional[float]
    url: str
    timestamp: datetime
    ai_insight: Optional[str] = None

class Database:
    """SQLite database for storing monitoring data."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor TEXT NOT NULL,
                    product TEXT NOT NULL,
                    price REAL NOT NULL,
                    currency TEXT DEFAULT 'EUR',
                    url TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor TEXT NOT NULL,
                    page_type TEXT NOT NULL,
                    url TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    content_preview TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competitor TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    product TEXT,
                    old_value TEXT,
                    new_value TEXT NOT NULL,
                    change_percent REAL,
                    url TEXT,
                    ai_insight TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def save_price(self, competitor: str, product: str, price: float, 
                   currency: str, url: str):
        """Save price data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO prices (competitor, product, price, currency, url)
                   VALUES (?, ?, ?, ?, ?)""",
                (competitor, product, price, currency, url)
            )
            conn.commit()
    
    def get_last_price(self, competitor: str, product: str) -> Optional[PriceData]:
        """Get most recent price for a product."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """SELECT product, price, currency, timestamp, url FROM prices
                   WHERE competitor = ? AND product = ?
                   ORDER BY timestamp DESC LIMIT 1""",
                (competitor, product)
            ).fetchone()
            
            if row:
                return PriceData(
                    product=row[0],
                    price=row[1],
                    currency=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    url=row[4]
                )
            return None
    
    def save_snapshot(self, competitor: str, page_type: str, url: str, 
                      content: str):
        """Save page snapshot."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        preview = content[:500] if len(content) > 500 else content
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO snapshots (competitor, page_type, url, content_hash, content_preview)
                   VALUES (?, ?, ?, ?, ?)""",
                (competitor, page_type, url, content_hash, preview)
            )
            conn.commit()
    
    def get_last_snapshot(self, competitor: str, page_type: str, url: str) -> Optional[Dict]:
        """Get most recent snapshot."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """SELECT content_hash, content_preview, timestamp FROM snapshots
                   WHERE competitor = ? AND page_type = ? AND url = ?
                   ORDER BY timestamp DESC LIMIT 1""",
                (competitor, page_type, url)
            ).fetchone()
            
            if row:
                return {
                    "hash": row[0],
                    "preview": row[1],
                    "timestamp": datetime.fromisoformat(row[2])
                }
            return None
    
    def save_change(self, change: Change):
        """Save detected change."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO changes (competitor, change_type, product, old_value, 
                   new_value, change_percent, url, ai_insight)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (change.competitor, change.change_type, change.product,
                 change.old_value, change.new_value, change.change_percent,
                 change.url, change.ai_insight)
            )
            conn.commit()
    
    def get_changes(self, competitor: Optional[str] = None, 
                    days: int = 7) -> List[Change]:
        """Get recent changes."""
        since = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            if competitor:
                rows = conn.execute(
                    """SELECT competitor, change_type, product, old_value, new_value,
                       change_percent, url, ai_insight, timestamp FROM changes
                       WHERE competitor = ? AND timestamp > ?
                       ORDER BY timestamp DESC""",
                    (competitor, since.isoformat())
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT competitor, change_type, product, old_value, new_value,
                       change_percent, url, ai_insight, timestamp FROM changes
                       WHERE timestamp > ?
                       ORDER BY timestamp DESC""",
                    (since.isoformat(),)
                ).fetchall()
            
            return [
                Change(
                    competitor=row[0],
                    change_type=row[1],
                    product=row[2],
                    old_value=row[3],
                    new_value=row[4],
                    change_percent=row[5],
                    url=row[6],
                    ai_insight=row[7],
                    timestamp=datetime.fromisoformat(row[8])
                )
                for row in rows
            ]

class WebScraper:
    """Web scraping with rate limiting and politeness."""
    
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.last_request = 0
        self.session = requests.Session() if REQUESTS_AVAILABLE else None
        if self.session:
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
    
    def fetch(self, url: str) -> Optional[str]:
        """Fetch URL content with rate limiting."""
        if not REQUESTS_AVAILABLE:
            print("❌ requests library not installed")
            return None
        
        # Rate limiting
        elapsed = time.time() - self.last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        
        try:
            response = self.session.get(url, timeout=30)
            self.last_request = time.time()
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"⚠️ HTTP {response.status_code} for {url}")
                return None
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            return None
    
    def extract_price(self, html: str, selector: Optional[str] = None) -> Optional[Dict]:
        """Extract price from HTML."""
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try selector first
        if selector:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                return self._parse_price(text)
        
        # Common price patterns
        price_patterns = [
            r'€\s*([\d.,]+)',
            r'([\d.,]+)\s*€',
            r'\$\s*([\d.,]+)',
            r'([\d.,]+)\s*\$',
            r'price["\']?\s*[:=]\s*["\']?([\d.,]+)',
        ]
        
        text = soup.get_text()
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return {"price": self._clean_price(matches[0]), "currency": "EUR"}
        
        return None
    
    def _parse_price(self, text: str) -> Optional[Dict]:
        """Parse price text."""
        # Extract number from text
        numbers = re.findall(r'[\d.,]+', text.replace(',', '.'))
        if numbers:
            currency = "EUR" if "€" in text or "EUR" in text else "USD" if "$" in text else "EUR"
            return {"price": self._clean_price(numbers[0]), "currency": currency}
        return None
    
    def _clean_price(self, price_str: str) -> float:
        """Clean price string to float."""
        # Handle European format (1.234,56)
        if ',' in price_str and '.' in price_str:
            if price_str.index(',') > price_str.index('.'):
                # 1,234.56 format
                return float(price_str.replace(',', ''))
            else:
                # 1.234,56 format
                return float(price_str.replace('.', '').replace(',', '.'))
        elif ',' in price_str:
            # Could be 123,45 or 1,234
            if len(price_str.split(',')[1]) <= 2:
                return float(price_str.replace(',', '.'))
            else:
                return float(price_str.replace(',', ''))
        else:
            return float(price_str)

class TelegramNotifier:
    """Send Telegram notifications."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
    
    def send(self, message: str) -> bool:
        """Send Telegram message."""
        if not REQUESTS_AVAILABLE:
            print(f"📱 Would send Telegram: {message[:100]}...")
            return True
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram send failed: {e}")
            return False
    
    def send_change_alert(self, change: Change):
        """Send formatted change alert."""
        emoji_map = {
            "price": "💰",
            "homepage": "🏠",
            "news": "📰",
            "product": "📦"
        }
        
        emoji = emoji_map.get(change.change_type, "📝")
        
        message = f"""🕵️ <b>Competitor Alert: {change.competitor}</b>

{emoji} <b>{change.change_type.upper()} CHANGE</b>"""
        
        if change.product:
            message += f"\nProduct: {change.product}"
        
        if change.old_value:
            message += f"\nOld: {change.old_value}"
        
        message += f"\nNew: {change.new_value}"
        
        if change.change_percent:
            direction = "📉" if change.change_percent < 0 else "📈"
            message += f"\n{direction} Change: {change.change_percent:+.1f}%"
        
        if change.ai_insight:
            message += f"\n\n🤖 <b>AI Insight:</b>\n{change.ai_insight}"
        
        message += f"\n\n🔗 <a href='{change.url}'>View Page</a>"
        
        self.send(message)

class CompetitorMonitor:
    """Main competitor monitoring class."""
    
    def __init__(self):
        self.config = self._load_config()
        self.db = Database(DB_FILE)
        self.scraper = WebScraper(delay=1.0)
        self.notifier = None
        
        if self.config and self.config.get("alerts"):
            alerts = self.config["alerts"]
            if alerts.get("telegram_bot_token") and alerts.get("telegram_chat_id"):
                self.notifier = TelegramNotifier(
                    alerts["telegram_bot_token"],
                    alerts["telegram_chat_id"]
                )
    
    def _load_config(self) -> Optional[Dict]:
        """Load configuration file."""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return json.load(f)
        return None
    
    def _save_config(self, config: Dict):
        """Save configuration file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    
    def setup(self):
        """Interactive setup wizard."""
        print("🕵️ Competitor Intelligence Monitor - Setup")
        print("=" * 50)
        
        config = {
            "competitors": [],
            "alerts": {},
            "storage": {"retention_days": 90}
        }
        
        # Telegram setup
        print("\n📱 Telegram Alerts Configuration")
        print("-" * 50)
        bot_token = input("Bot Token (from @BotFather): ").strip()
        chat_id = input("Chat ID: ").strip()
        
        if bot_token and chat_id:
            config["alerts"] = {
                "telegram_bot_token": bot_token,
                "telegram_chat_id": chat_id,
                "price_change_threshold": 5.0,
                "digest_mode": "immediate"
            }
        
        # Competitor setup
        print("\n🏢 Add Your First Competitor")
        print("-" * 50)
        
        while True:
            name = input("\nCompetitor name (or press Enter to finish): ").strip()
            if not name:
                break
            
            website = input(f"Website URL for {name}: ").strip()
            
            monitor_pricing = input("Monitor pricing? (y/n): ").lower() == 'y'
            monitor_homepage = input("Monitor homepage changes? (y/n): ").lower() == 'y'
            
            product_pages = []
            if monitor_pricing:
                print("Enter product page URLs (one per line, empty to finish):")
                while True:
                    page = input("  Product page: ").strip()
                    if not page:
                        break
                    product_pages.append(page)
            
            competitor = {
                "name": name,
                "website": website,
                "monitor": {
                    "pricing": monitor_pricing,
                    "homepage": monitor_homepage,
                    "news": True
                },
                "product_pages": product_pages
            }
            
            config["competitors"].append(competitor)
            print(f"✅ Added {name}")
        
        self._save_config(config)
        print(f"\n✅ Configuration saved to {CONFIG_FILE}")
        print("🚀 Run 'python competitor_monitor.py --scan' to start monitoring")
    
    def scan(self, competitor_name: Optional[str] = None, force: bool = False):
        """Run monitoring scan."""
        if not self.config:
            print("❌ No configuration found. Run --setup first.")
            return
        
        competitors = self.config.get("competitors", [])
        if competitor_name:
            competitors = [c for c in competitors if c["name"] == competitor_name]
        
        if not competitors:
            print("❌ No competitors configured")
            return
        
        print(f"🕵️ Starting scan of {len(competitors)} competitor(s)...")
        print("-" * 50)
        
        all_changes = []
        
        for comp in competitors:
            changes = self._scan_competitor(comp, force)
            all_changes.extend(changes)
            time.sleep(2)  # Be polite between competitors
        
        # Send summary
        if all_changes and self.notifier:
            summary = f"""📊 <b>Scan Complete</b>

Total changes detected: {len(all_changes)}
"""
            for change in all_changes[:5]:
                all_changes.append(f"• {change.competitor}: {change.change_type}")
            
            if len(all_changes) > 5:
                all_changes.append(f"\n...and {len(all_changes) - 5} more")
            
            self.notifier.send(summary)
        
        print("\n" + "=" * 50)
        print(f"✅ Scan complete. {len(all_changes)} changes detected.")
    
    def _scan_competitor(self, competitor: Dict, force: bool) -> List[Change]:
        """Scan a single competitor."""
        name = competitor["name"]
        website = competitor["website"]
        monitor = competitor.get("monitor", {})
        changes = []
        
        print(f"\n🔍 Scanning {name}...")
        
        # Monitor homepage
        if monitor.get("homepage", False):
            homepage_change = self._check_homepage(name, website)
            if homepage_change:
                changes.append(homepage_change)
                print(f"  🏠 Homepage changed!")
        
        # Monitor pricing
        if monitor.get("pricing", False):
            for page in competitor.get("product_pages", []):
                price_change = self._check_price(name, page)
                if price_change:
                    changes.append(price_change)
                    print(f"  💰 Price change on {page}")
        
        # Save all changes
        for change in changes:
            self.db.save_change(change)
            if self.notifier and self.config["alerts"].get("digest_mode") == "immediate":
                self.notifier.send_change_alert(change)
        
        if not changes:
            print(f"  ✅ No changes detected")
        
        return changes
    
    def _check_homepage(self, competitor: str, url: str) -> Optional[Change]:
        """Check for homepage changes."""
        content = self.scraper.fetch(url)
        if not content:
            return None
        
        # Get last snapshot
        last = self.db.get_last_snapshot(competitor, "homepage", url)
        current_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Save new snapshot
        self.db.save_snapshot(competitor, "homepage", url, content)
        
        # Check if changed
        if last and last["hash"] != current_hash:
            return Change(
                competitor=competitor,
                change_type="homepage",
                product=None,
                old_value=f"Hash: {last['hash'][:8]}...",
                new_value=f"Hash: {current_hash[:8]}...",
                change_percent=None,
                url=url,
                timestamp=datetime.now(),
                ai_insight="Homepage content has changed. Review for messaging updates."
            )
        
        return None
    
    def _check_price(self, competitor: str, url: str) -> Optional[Change]:
        """Check for price changes."""
        content = self.scraper.fetch(url)
        if not content:
            return None
        
        # Extract product name from URL or content
        product = url.split('/')[-1] or "Unknown Product"
        
        # Extract price
        price_data = self.scraper.extract_price(content)
        if not price_data:
            return None
        
        # Get last price
        last_price = self.db.get_last_price(competitor, product)
        
        # Save new price
        self.db.save_price(
            competitor=competitor,
            product=product,
            price=price_data["price"],
            currency=price_data["currency"],
            url=url
        )
        
        # Check if changed
        if last_price:
            threshold = self.config.get("alerts", {}).get("price_change_threshold", 5.0)
            change_pct = ((price_data["price"] - last_price.price) / last_price.price) * 100
            
            if abs(change_pct) >= threshold:
                old_val = f"{last_price.price:.2f} {last_price.currency}"
                new_val = f"{price_data['price']:.2f} {price_data['currency']}"
                
                direction = "increased" if change_pct > 0 else "decreased"
                insight = f"Price {direction} by {abs(change_pct):.1f}%. "
                if change_pct < 0:
                    insight += "Competitor may be trying to gain market share."
                else:
                    insight += "Potential premium positioning or cost pressure."
                
                return Change(
                    competitor=competitor,
                    change_type="price",
                    product=product,
                    old_value=old_val,
                    new_value=new_val,
                    change_percent=change_pct,
                    url=url,
                    timestamp=datetime.now(),
                    ai_insight=insight
                )
        
        return None
    
    def report(self, weekly: bool = False, days: int = 7):
        """Generate monitoring report."""
        changes = self.db.get_changes(days=days)
        
        if not changes:
            print("📊 No changes in the last {} days".format(days))
            return
        
        print("\n" + "=" * 60)
        print(f"📊 COMPETITOR INTELLIGENCE REPORT")
        print(f"   Period: Last {days} days")
        print("=" * 60)
        
        # Group by competitor
        by_competitor = {}
        for change in changes:
            if change.competitor not in by_competitor:
                by_competitor[change.competitor] = []
            by_competitor[change.competitor].append(change)
        
        for comp_name, comp_changes in by_competitor.items():
            print(f"\n🏢 {comp_name}")
            print("-" * 40)
            
            for change in comp_changes[:5]:  # Show last 5
                emoji = {"price": "💰", "homepage": "🏠", "news": "📰"}.get(change.change_type, "📝")
                print(f"  {emoji} {change.change_type.upper()}: {change.new_value}")
                if change.change_percent:
                    print(f"     Change: {change.change_percent:+.1f}%")
            
            if len(comp_changes) > 5:
                print(f"  ... and {len(comp_changes) - 5} more changes")
        
        print("\n" + "=" * 60)
    
    def add_competitor(self, name: str, website: str):
        """Add a new competitor."""
        if not self.config:
            self.config = {"competitors": [], "alerts": {}}
        
        competitor = {
            "name": name,
            "website": website,
            "monitor": {"pricing": True, "homepage": True, "news": True},
            "product_pages": []
        }
        
        self.config["competitors"].append(competitor)
        self._save_config(self.config)
        print(f"✅ Added competitor: {name}")

def main():
    parser = argparse.ArgumentParser(
        description="Competitor Intelligence Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --setup                    # Initial configuration
  %(prog)s --scan                     # Scan all competitors
  %(prog)s --scan --competitor name   # Scan specific competitor
  %(prog)s --report --weekly          # Generate weekly report
        """
    )
    
    parser.add_argument("--setup", action="store_true",
                       help="Run interactive setup")
    parser.add_argument("--scan", action="store_true",
                       help="Run monitoring scan")
    parser.add_argument("--competitor", type=str,
                       help="Specific competitor to scan")
    parser.add_argument("--force", action="store_true",
                       help="Force scan (ignore cache)")
    parser.add_argument("--report", action="store_true",
                       help="Generate report")
    parser.add_argument("--weekly", action="store_true",
                       help="Weekly report format")
    parser.add_argument("--add-competitor", action="store_true",
                       help="Add new competitor")
    parser.add_argument("--name", type=str,
                       help="Competitor name")
    parser.add_argument("--website", type=str,
                       help="Competitor website")
    
    args = parser.parse_args()
    
    monitor = CompetitorMonitor()
    
    if args.setup:
        monitor.setup()
    elif args.scan:
        monitor.scan(args.competitor, args.force)
    elif args.report:
        monitor.report(args.weekly)
    elif args.add_competitor:
        if args.name and args.website:
            monitor.add_competitor(args.name, args.website)
        else:
            print("❌ --name and --website required")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
