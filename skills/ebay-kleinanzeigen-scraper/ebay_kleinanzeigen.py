#!/usr/bin/env python3
"""
eBay Kleinanzeigen Scraper
Monitors eBay Kleinanzeigen for new listings matching your criteria.
"""

import os
import sys
import json
import re
import hashlib
import time
import random
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from urllib.parse import urlencode, quote_plus
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
]


@dataclass
class KleinanzeigenAd:
    """Represents a Kleinanzeigen listing."""
    id: str
    title: str
    description: str
    price: str
    price_value: Optional[float]
    location: str
    distance: Optional[str]
    date_posted: str
    seller_name: str
    seller_type: str  # 'private' or 'commercial'
    image_url: Optional[str]
    url: str
    category: str
    is_top_ad: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def get_hash(self) -> str:
        """Generate unique hash for deduplication."""
        content = f"{self.id}:{self.title}:{self.price}"
        return hashlib.md5(content.encode()).hexdigest()


class TelegramNotifier:
    """Sends notifications via Telegram."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram."""
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if result.get("ok"):
                logger.info("✅ Telegram message sent")
                return True
            else:
                logger.error(f"❌ Telegram error: {result.get('description')}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram: {e}")
            return False
    
    def format_ad_message(self, ad: KleinanzeigenAd) -> str:
        """Format ad for Telegram."""
        # Truncate description
        desc = ad.description[:250] + "..." if len(ad.description) > 250 else ad.description
        
        # Top ad badge
        top_badge = "🔥 <b>TOP ANZEIGE</b>\n" if ad.is_top_ad else ""
        
        # Commercial badge
        seller_badge = "🏪 Gewerblich" if ad.seller_type == "commercial" else "👤 Privat"
        
        message = f"""{top_badge}🔍 <b>Neues eBay Kleinanzeigen Angebot</b>

📱 <b>{ad.title}</b>
💰 <b>{ad.price}</b>
📍 {ad.location}{f' ({ad.distance})' if ad.distance else ''}
{seller_badge}

📝 {desc}

🔗 <a href="{ad.url}">Zum Angebot</a>
"""
        return message


class SlackNotifier:
    """Sends notifications via Slack webhook."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_ad_notification(self, ad: KleinanzeigenAd) -> bool:
        """Send ad notification to Slack."""
        color = "#ff5a5f" if ad.is_top_ad else "#36a64f"
        
        payload = {
            "attachments": [{
                "color": color,
                "title": ad.title,
                "title_link": ad.url,
                "fields": [
                    {"title": "Preis", "value": ad.price, "short": True},
                    {"title": "Ort", "value": ad.location, "short": True},
                    {"title": "Verkäufer", "value": ad.seller_name, "short": True},
                    {"title": "Typ", "value": "TOP Anzeige" if ad.is_top_ad else "Standard", "short": True}
                ],
                "footer": f"eBay Kleinanzeigen • {ad.date_posted}"
            }]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Failed to send Slack: {e}")
            return False


class KleinanzeigenScraper:
    """Main scraper for eBay Kleinanzeigen."""
    
    BASE_URL = "https://www.kleinanzeigen.de"
    
    # Category mapping
    CATEGORIES = {
        "elektronik": 161,
        "handys": 176,
        "computer": 245,
        "moebel": 80,
        "motorraeder": 305,
        "autos": 210,
        "immobilien": 297,
        "spielzeug": 231,
        "sport": 320,
        "mode": 153,
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.seen_ads: set = set()
        self.state_file = Path.home() / ".ebay_kleinanzeigen_seen.json"
        self.notifiers = self._init_notifiers()
        self.delay = int(os.getenv("KLEINANZEIGEN_DELAY", "3"))
        self.max_pages = int(os.getenv("KLEINANZEIGEN_MAX_PAGES", "5"))
        
        # Load seen ads
        self._load_seen_ads()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get random headers."""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
        }
    
    def _init_notifiers(self) -> List[Any]:
        """Initialize notification channels."""
        notifiers = []
        
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
        if telegram_token and telegram_chat:
            notifiers.append(TelegramNotifier(telegram_token, telegram_chat))
            logger.info("✅ Telegram notifier initialized")
        
        slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        if slack_webhook:
            notifiers.append(SlackNotifier(slack_webhook))
            logger.info("✅ Slack notifier initialized")
        
        return notifiers
    
    def _load_seen_ads(self):
        """Load previously seen ads."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.seen_ads = set(data.get('seen', []))
                    logger.info(f"📂 Loaded {len(self.seen_ads)} previously seen ads")
        except Exception as e:
            logger.warning(f"⚠️ Could not load seen ads: {e}")
            self.seen_ads = set()
    
    def _save_seen_ads(self):
        """Save seen ads to file."""
        try:
            # Keep only last 10000 to prevent file bloat
            seen_list = list(self.seen_ads)[-10000:]
            with open(self.state_file, 'w') as f:
                json.dump({'seen': seen_list, 'updated': datetime.now().isoformat()}, f)
        except Exception as e:
            logger.warning(f"⚠️ Could not save seen ads: {e}")
    
    def _parse_price(self, price_text: str) -> tuple:
        """Parse price from text."""
        if not price_text or price_text.strip() in ["VB", "Zu verschenken", ""]:
            return price_text, None
        
        # Extract numbers
        match = re.search(r'[\d.,]+', price_text.replace('.', '').replace(',', '.'))
        if match:
            try:
                value = float(match.group().replace(',', '.'))
                return price_text, value
            except ValueError:
                pass
        
        return price_text, None
    
    def _extract_ad(self, article) -> Optional[KleinanzeigenAd]:
        """Extract ad data from article element."""
        try:
            # Check if it's a top ad
            is_top_ad = "topad" in article.get("class", []) or article.select_one(".badge-topad") is not None
            
            # Title and link
            title_elem = article.select_one("h2 a") or article.select_one(".ellipsis")
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")
            if url and not url.startswith("http"):
                url = self.BASE_URL + url
            
            # Ad ID from URL
            ad_id = ""
            id_match = re.search(r'/s-anzeige/[^/]+/(\d+)', url)
            if id_match:
                ad_id = id_match.group(1)
            else:
                ad_id = hashlib.md5(title.encode()).hexdigest()[:12]
            
            # Price
            price_elem = article.select_one(".adprice") or article.select_one(".ad-price")
            price_text = price_elem.get_text(strip=True) if price_elem else "VB"
            price, price_value = self._parse_price(price_text)
            
            # Description
            desc_elem = article.select_one("p")
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            # Location
            loc_elem = article.select_one(".aditem-main--middle--bottom span") or article.select_one(".ad-location")
            location = ""
            distance = None
            if loc_elem:
                loc_text = loc_elem.get_text(strip=True)
                # Parse "Berlin (5 km)" format
                loc_match = re.match(r'(.+?)\s*\((\d+)\s*km\)', loc_text)
                if loc_match:
                    location = loc_match.group(1).strip()
                    distance = f"{loc_match.group(2)} km"
                else:
                    location = loc_text
            
            # Image
            img_elem = article.select_one("img")
            image_url = img_elem.get("src") if img_elem else None
            
            # Seller info (limited in list view)
            seller_name = "Unbekannt"
            seller_type = "private"
            
            # Date (usually not available in list view)
            date_posted = datetime.now().strftime("%d.%m.%Y")
            
            return KleinanzeigenAd(
                id=ad_id,
                title=title,
                description=description,
                price=price,
                price_value=price_value,
                location=location,
                distance=distance,
                date_posted=date_posted,
                seller_name=seller_name,
                seller_type=seller_type,
                image_url=image_url,
                url=url,
                category="",
                is_top_ad=is_top_ad
            )
            
        except Exception as e:
            logger.debug(f"Error parsing ad: {e}")
            return None
    
    def search(
        self,
        query: str,
        category: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        city: Optional[str] = None,
        radius: int = 0,
        sort_type: str = "DATE",  # DATE, PRICE_ASC, PRICE_DESC
        pages: int = 1
    ) -> List[KleinanzeigenAd]:
        """Search for ads on Kleinanzeigen."""
        logger.info(f"🔍 Searching for: '{query}' (pages: {pages})")
        
        all_ads = []
        
        for page in range(1, pages + 1):
            # Build URL
            params = {
                "keywords": query,
                "sortingField": sort_type,
            }
            
            if category:
                params["categoryId"] = category
            
            if min_price:
                params["priceFrom"] = min_price
            
            if max_price:
                params["priceTo"] = max_price
            
            if radius > 0 and city:
                params["locationStr"] = city
                params["radius"] = radius
            
            if page > 1:
                params["pageNum"] = page
            
            url = f"{self.BASE_URL}/s-suchanfrage.html?{urlencode(params, quote_via=quote_plus)}"
            
            try:
                logger.debug(f"Fetching: {url}")
                response = self.session.get(url, headers=self._get_headers(), timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all ad articles
                articles = soup.select("article.aditem") or soup.select(".aditem")
                
                logger.debug(f"Found {len(articles)} ads on page {page}")
                
                for article in articles:
                    ad = self._extract_ad(article)
                    if ad:
                        all_ads.append(ad)
                
                # Delay between requests
                if page < pages:
                    time.sleep(self.delay + random.uniform(0.5, 1.5))
                
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Error fetching page {page}: {e}")
                break
            except Exception as e:
                logger.error(f"❌ Error parsing page {page}: {e}")
                continue
        
        logger.info(f"✅ Found {len(all_ads)} ads total")
        return all_ads
    
    def check_for_new_ads(
        self,
        query: str,
        category: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        city: Optional[str] = None,
        radius: int = 0,
        notify: bool = True
    ) -> List[KleinanzeigenAd]:
        """Check for new ads and optionally notify."""
        ads = self.search(
            query=query,
            category=category,
            min_price=min_price,
            max_price=max_price,
            city=city,
            radius=radius,
            pages=self.max_pages
        )
        
        new_ads = []
        
        for ad in ads:
            ad_hash = ad.get_hash()
            
            if ad_hash not in self.seen_ads:
                new_ads.append(ad)
                self.seen_ads.add(ad_hash)
                
                if notify:
                    self._notify_new_ad(ad)
        
        # Save updated seen ads
        self._save_seen_ads()
        
        logger.info(f"🆕 Found {len(new_ads)} new ads")
        return new_ads
    
    def _notify_new_ad(self, ad: KleinanzeigenAd):
        """Send notification for new ad."""
        for notifier in self.notifiers:
            try:
                if isinstance(notifier, TelegramNotifier):
                    message = notifier.format_ad_message(ad)
                    notifier.send_message(message)
                elif isinstance(notifier, SlackNotifier):
                    notifier.send_ad_notification(ad)
            except Exception as e:
                logger.error(f"❌ Failed to notify: {e}")
    
    def monitor_from_config(self, config_path: str):
        """Monitor searches from config file."""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        searches = config.get("searches", [])
        interval = config.get("check_interval", 300)
        
        logger.info(f"🚀 Starting monitoring with {len(searches)} searches (interval: {interval}s)")
        
        while True:
            try:
                for search_config in searches:
                    self.check_for_new_ads(
                        query=search_config["query"],
                        category=search_config.get("category"),
                        min_price=search_config.get("min_price"),
                        max_price=search_config.get("max_price"),
                        city=search_config.get("city"),
                        radius=search_config.get("radius", 0),
                        notify=True
                    )
                    # Small delay between searches
                    time.sleep(self.delay)
                
                logger.info(f"⏳ Sleeping for {interval}s...")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitoring stopped")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                time.sleep(60)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="eBay Kleinanzeigen Scraper")
    parser.add_argument("--search", "-s", help="Search query")
    parser.add_argument("--category", "-c", type=int, help="Category ID")
    parser.add_argument("--min-price", type=int, help="Minimum price")
    parser.add_argument("--max-price", type=int, help="Maximum price")
    parser.add_argument("--city", help="City for location filter")
    parser.add_argument("--radius", "-r", type=int, default=0, help="Search radius in km")
    parser.add_argument("--pages", "-p", type=int, default=1, help="Number of pages to scrape")
    parser.add_argument("--monitor", "-m", action="store_true", help="Monitor mode")
    parser.add_argument("--config", help="Config file for monitoring")
    parser.add_argument("--interval", type=int, default=300, help="Monitor interval (seconds)")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--notify", "-n", action="store_true", help="Send notifications")
    
    args = parser.parse_args()
    
    scraper = KleinanzeigenScraper()
    
    if args.config:
        if args.monitor:
            scraper.monitor_from_config(args.config)
        else:
            # Single run with config
            with open(args.config, 'r') as f:
                config = json.load(f)
            
            all_results = []
            for search_config in config.get("searches", []):
                results = scraper.check_for_new_ads(
                    query=search_config["query"],
                    category=search_config.get("category"),
                    min_price=search_config.get("min_price"),
                    max_price=search_config.get("max_price"),
                    city=search_config.get("city"),
                    radius=search_config.get("radius", 0),
                    notify=args.notify
                )
                all_results.extend(results)
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump([ad.to_dict() for ad in all_results], f, indent=2)
                logger.info(f"💾 Saved {len(all_results)} results to {args.output}")
    
    elif args.search:
        results = scraper.search(
            query=args.search,
            category=args.category,
            min_price=args.min_price,
            max_price=args.max_price,
            city=args.city,
            radius=args.radius,
            pages=args.pages
        )
        
        # Print results
        print(f"\n📝 Gefundene Anzeigen ({len(results)}):\n")
        for ad in results:
            print(f"📱 {ad.title}")
            print(f"💰 {ad.price}")
            print(f"📍 {ad.location}{f' ({ad.distance})' if ad.distance else ''}")
            print(f"🔗 {ad.url}")
            print("-" * 50)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump([ad.to_dict() for ad in results], f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved to {args.output}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
