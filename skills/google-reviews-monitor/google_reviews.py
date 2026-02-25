#!/usr/bin/env python3
"""
Google Reviews Monitor
Monitors Google Business reviews with sentiment analysis and alerts.
"""

import os
import sys
import json
import time
import re
import logging
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import Counter

import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class GoogleReview:
    """Represents a Google review."""
    review_id: str
    place_id: str
    place_name: str
    author_name: str
    author_url: Optional[str]
    profile_photo_url: Optional[str]
    rating: int
    text: str
    time: datetime
    relative_time: str
    language: str
    translated_text: Optional[str] = None
    response_text: Optional[str] = None
    response_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['time'] = self.time.isoformat() if self.time else None
        data['response_time'] = self.response_time.isoformat() if self.response_time else None
        return data
    
    @property
    def is_negative(self) -> bool:
        return self.rating <= 2
    
    @property
    def is_neutral(self) -> bool:
        return self.rating == 3
    
    @property
    def is_positive(self) -> bool:
        return self.rating >= 4
    
    @property
    def has_response(self) -> bool:
        return bool(self.response_text)


@dataclass
class SentimentAnalysis:
    """Sentiment analysis results."""
    total_reviews: int
    positive_count: int
    neutral_count: int
    negative_count: int
    positive_percent: float
    neutral_percent: float
    negative_percent: float
    average_rating: float
    common_phrases: List[tuple]
    trend: str  # 'improving', 'stable', 'declining'


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
            "disable_web_page_preview": True
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
    
    def format_review_message(self, review: GoogleReview) -> str:
        """Format review for Telegram."""
        stars = "⭐" * review.rating + "⚫" * (5 - review.rating)
        
        # Emoji based on sentiment
        if review.is_negative:
            header = "🚨"
            sentiment_text = f"⚠️ <b>{review.rating} ⭐ Bewertung</b>"
        elif review.is_neutral:
            header = "⚠️"
            sentiment_text = f"<b>{review.rating} ⭐ Bewertung</b>"
        else:
            header = "✅"
            sentiment_text = f"<b>{review.rating} ⭐ Bewertung</b>"
        
        # Truncate text
        text = review.text[:400] + "..." if len(review.text) > 400 else review.text
        
        # Response status
        response_status = "✅ Beantwortet" if review.has_response else "⏳ Unbeantwortet"
        
        message = f"""{header} <b>Neue Google Bewertung</b>

{sentiment_text}
🏪 {review.place_name}

📝 "{text}"
👤 {review.author_name} • {review.relative_time}

{response_status}
🔗 <a href="https://search.google.com/local/writereview?placeid={review.place_id}">Auf Google antworten</a>
"""
        return message
    
    def format_weekly_report(self, place_name: str, analysis: SentimentAnalysis) -> str:
        """Format weekly report for Telegram."""
        trend_emoji = "📈" if analysis.trend == "improving" else "📉" if analysis.trend == "declining" else "➡️"
        
        phrases_text = ""
        if analysis.common_phrases:
            phrases_text = "\n\n<b>Top Keywords:</b>\n"
            for phrase, count in analysis.common_phrases[:5]:
                phrases_text += f"• \"{phrase}\" ({count}x)\n"
        
        message = f"""📊 <b>Weekly Review Report</b>
🏪 {place_name}

⭐ Durchschnitt: {analysis.average_rating:.1f}/5
📝 Neue Reviews: {analysis.total_reviews}
😊 Positiv: {analysis.positive_count} ({analysis.positive_percent:.0f}%)
😐 Neutral: {analysis.neutral_count} ({analysis.neutral_percent:.0f}%)
😠 Negativ: {analysis.negative_count} ({analysis.negative_percent:.0f}%)

{trend_emoji} Trend: {analysis.trend.capitalize()}{phrases_text}
"""
        return message


class SlackNotifier:
    """Sends notifications via Slack webhook."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_review_notification(self, review: GoogleReview) -> bool:
        """Send review notification to Slack."""
        color = "#ff0000" if review.is_negative else "#ffff00" if review.is_neutral else "#36a64f"
        
        fields = [
            {"title": "Bewertung", "value": f"{review.rating} / 5 ⭐", "short": True},
            {"title": "Ort", "value": review.place_name, "short": True},
            {"title": "Autor", "value": review.author_name, "short": True},
            {"title": "Status", "value": "Beantwortet" if review.has_response else "Unbeantwortet", "short": True}
        ]
        
        payload = {
            "attachments": [{
                "color": color,
                "title": f"Neue Google Bewertung für {review.place_name}",
                "title_link": f"https://search.google.com/local/writereview?placeid={review.place_id}",
                "text": review.text[:500] if review.text else "Kein Text",
                "fields": fields,
                "footer": f"Google Reviews • {review.relative_time}"
            }]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Failed to send Slack: {e}")
            return False


class GoogleReviewsMonitor:
    """Main monitor for Google Reviews."""
    
    BASE_URL = "https://maps.googleapis.com/maps/api/place"
    
    # German positive/negative keywords for basic sentiment
    POSITIVE_KEYWORDS = [
        "gut", "super", "toll", "ausgezeichnet", "perfekt", "empfehlen",
        "freundlich", "schnell", "lecker", "schön", "sauber", "top",
        "klasse", "wunderbar", "fantastisch", "zufrieden", " spitze"
    ]
    
    NEGATIVE_KEYWORDS = [
        "schlecht", "enttäuschend", "schrecklich", "furchtbar", "nervig",
        "langsam", "unfreundlich", "dreckig", "ekelhaft", "mies",
        "problem", "ärger", "beschwerde", "nie wieder", "abzocke"
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")
        if not self.api_key:
            raise ValueError("Google Places API key required. Set GOOGLE_PLACES_API_KEY env var.")
        
        self.notifiers = self._init_notifiers()
        self.seen_reviews: Dict[str, set] = {}  # place_id -> set of review_ids
        self.state_file = Path.home() / ".google_reviews_state.json"
        
        self._load_state()
    
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
    
    def _load_state(self):
        """Load seen reviews state."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.seen_reviews = {k: set(v) for k, v in data.get('seen', {}).items()}
                    logger.info(f"📂 Loaded state for {len(self.seen_reviews)} places")
        except Exception as e:
            logger.warning(f"⚠️ Could not load state: {e}")
            self.seen_reviews = {}
    
    def _save_state(self):
        """Save seen reviews state."""
        try:
            data = {
                'seen': {k: list(v) for k, v in self.seen_reviews.items()},
                'updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"⚠️ Could not save state: {e}")
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make API request to Google Places."""
        url = f"{self.BASE_URL}/{endpoint}/json"
        params['key'] = self.api_key
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'OK':
                error_msg = data.get('error_message', data.get('status', 'Unknown error'))
                raise Exception(f"API Error: {error_msg}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API request failed: {e}")
            raise
    
    def find_place(self, query: str) -> List[Dict[str, str]]:
        """Find place by name/address."""
        logger.info(f"🔍 Searching for: '{query}'")
        
        params = {
            "input": query,
            "inputtype": "textquery",
            "fields": "place_id,name,formatted_address,rating,user_ratings_total"
        }
        
        data = self._make_request("findplacefromtext", params)
        
        candidates = data.get('candidates', [])
        logger.info(f"✅ Found {len(candidates)} places")
        
        return candidates
    
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get place details including reviews."""
        params = {
            "place_id": place_id,
            "fields": "name,rating,user_ratings_total,reviews,formatted_address,place_id"
        }
        
        data = self._make_request("details", params)
        return data.get('result', {})
    
    def get_reviews(
        self,
        place_id: str,
        max_results: int = 5
    ) -> List[GoogleReview]:
        """Get reviews for a place."""
        logger.info(f"📥 Fetching reviews for place: {place_id[:20]}...")
        
        details = self.get_place_details(place_id)
        
        if not details:
            logger.warning("⚠️ No details found")
            return []
        
        place_name = details.get('name', 'Unknown')
        raw_reviews = details.get('reviews', [])
        
        reviews = []
        for raw in raw_reviews[:max_results]:
            review = GoogleReview(
                review_id=raw.get('author_url', ''),  # Use author_url as ID
                place_id=place_id,
                place_name=place_name,
                author_name=raw.get('author_name', 'Anonymous'),
                author_url=raw.get('author_url'),
                profile_photo_url=raw.get('profile_photo_url'),
                rating=raw.get('rating', 0),
                text=raw.get('text', ''),
                time=datetime.fromtimestamp(raw.get('time', 0)),
                relative_time=raw.get('relative_time_description', ''),
                language=raw.get('language', ''),
                translated_text=None,
                response_text=None,
                response_time=None
            )
            reviews.append(review)
        
        logger.info(f"✅ Fetched {len(reviews)} reviews")
        return reviews
    
    def check_for_new_reviews(
        self,
        place_id: str,
        min_stars: Optional[int] = None,
        max_stars: Optional[int] = None,
        notify: bool = True
    ) -> List[GoogleReview]:
        """Check for new reviews matching criteria."""
        if place_id not in self.seen_reviews:
            self.seen_reviews[place_id] = set()
        
        reviews = self.get_reviews(place_id)
        new_reviews = []
        
        for review in reviews:
            # Check if we've seen this review
            if review.review_id in self.seen_reviews[place_id]:
                continue
            
            # Mark as seen
            self.seen_reviews[place_id].add(review.review_id)
            
            # Check star rating criteria
            if min_stars and review.rating < min_stars:
                continue
            if max_stars and review.rating > max_stars:
                continue
            
            new_reviews.append(review)
            
            if notify:
                self._notify_new_review(review)
        
        self._save_state()
        logger.info(f"🆕 Found {len(new_reviews)} new reviews")
        return new_reviews
    
    def _notify_new_review(self, review: GoogleReview):
        """Send notification for new review."""
        for notifier in self.notifiers:
            try:
                if isinstance(notifier, TelegramNotifier):
                    message = notifier.format_review_message(review)
                    notifier.send_message(message)
                elif isinstance(notifier, SlackNotifier):
                    notifier.send_review_notification(review)
            except Exception as e:
                logger.error(f"❌ Failed to notify: {e}")
    
    def analyze_sentiment(self, reviews: List[GoogleReview]) -> SentimentAnalysis:
        """Analyze sentiment of reviews."""
        if not reviews:
            return SentimentAnalysis(0, 0, 0, 0, 0, 0, 0, 0, [], "stable")
        
        total = len(reviews)
        positive = sum(1 for r in reviews if r.is_positive)
        neutral = sum(1 for r in reviews if r.is_neutral)
        negative = sum(1 for r in reviews if r.is_negative)
        
        avg_rating = sum(r.rating for r in reviews) / total
        
        # Extract common phrases (simple word frequency)
        all_text = " ".join(r.text.lower() for r in reviews if r.text)
        words = re.findall(r'\b[a-zäöüß]{4,}\b', all_text)
        word_freq = Counter(words)
        
        # Filter out common words
        stop_words = {'sehr', 'waren', 'eine', 'einer', 'eines', 'dieser', 'dieses', 'alles', 'schon'}
        common_phrases = [(w, c) for w, c in word_freq.most_common(20) if w not in stop_words][:10]
        
        # Determine trend (would need historical data for real trend)
        trend = "stable"
        if avg_rating >= 4.5:
            trend = "improving"
        elif avg_rating <= 2.5:
            trend = "declining"
        
        return SentimentAnalysis(
            total_reviews=total,
            positive_count=positive,
            neutral_count=neutral,
            negative_count=negative,
            positive_percent=(positive / total) * 100,
            neutral_percent=(neutral / total) * 100,
            negative_percent=(negative / total) * 100,
            average_rating=avg_rating,
            common_phrases=common_phrases,
            trend=trend
        )
    
    def monitor_from_config(self, config_path: str):
        """Monitor places from config file."""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        places = config.get("places", [])
        interval = config.get("check_interval", 3600)
        
        logger.info(f"🚀 Starting monitoring for {len(places)} places (interval: {interval}s)")
        
        while True:
            try:
                for place_config in places:
                    self.check_for_new_reviews(
                        place_id=place_config["place_id"],
                        min_stars=place_config.get("alert_stars_min"),
                        max_stars=place_config.get("alert_stars_max"),
                        notify=True
                    )
                    time.sleep(2)  # Small delay between places
                
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
    parser = argparse.ArgumentParser(description="Google Reviews Monitor")
    parser.add_argument("--place-id", help="Google Place ID")
    parser.add_argument("--search", "-s", help="Search query for place")
    parser.add_argument("--max-results", "-n", type=int, default=5, help="Max reviews to fetch")
    parser.add_argument("--min-stars", type=int, help="Minimum star rating")
    parser.add_argument("--max-stars", type=int, help="Maximum star rating")
    parser.add_argument("--monitor", "-m", action="store_true", help="Monitor mode")
    parser.add_argument("--config", help="Config file for monitoring")
    parser.add_argument("--analyze", "-a", action="store_true", help="Analyze sentiment")
    parser.add_argument("--interval", type=int, default=3600, help="Monitor interval")
    parser.add_argument("--output", "-o", help="Output JSON file")
    
    args = parser.parse_args()
    
    try:
        monitor = GoogleReviewsMonitor()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    if args.config and args.monitor:
        # Config-based monitoring
        monitor.monitor_from_config(args.config)
    
    elif args.search:
        # Search for place
        results = monitor.find_place(args.search)
        
        print(f"\n🔍 Gefundene Orte ({len(results)}):\n")
        for i, place in enumerate(results, 1):
            print(f"{i}. {place.get('name')}")
            print(f"   📍 {place.get('formatted_address')}")
            print(f"   ⭐ {place.get('rating', 'N/A')} ({place.get('user_ratings_total', 0)} Reviews)")
            print(f"   🆔 Place ID: {place.get('place_id')}")
            print()
    
    elif args.place_id:
        # Get reviews for place
        reviews = monitor.get_reviews(args.place_id, max_results=args.max_results)
        
        if args.analyze:
            analysis = monitor.analyze_sentiment(reviews)
            
            print(f"\n📊 Sentiment-Analyse ({analysis.total_reviews} Reviews):\n")
            print(f"⭐ Durchschnitt: {analysis.average_rating:.1f}/5")
            print(f"😊 Positiv: {analysis.positive_count} ({analysis.positive_percent:.0f}%)")
            print(f"😐 Neutral: {analysis.neutral_count} ({analysis.neutral_percent:.0f}%)")
            print(f"😠 Negativ: {analysis.negative_count} ({analysis.negative_percent:.0f}%)")
            print(f"\n📈 Trend: {analysis.trend}")
            
            if analysis.common_phrases:
                print(f"\n🔤 Häufige Wörter:")
                for word, count in analysis.common_phrases[:5]:
                    print(f"  • {word} ({count}x)")
        
        else:
            # Print reviews
            print(f"\n📝 Reviews ({len(reviews)}):\n")
            for review in reviews:
                stars = "⭐" * review.rating + "⚫" * (5 - review.rating)
                status = "✅ Beantwortet" if review.has_response else "⏳ Unbeantwortet"
                
                print(f"{stars} ({review.rating}/5) - {review.author_name}")
                print(f"🕐 {review.relative_time}")
                print(f"📝 {review.text[:200]}{'...' if len(review.text) > 200 else ''}")
                print(f"📊 {status}")
                print("-" * 50)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump([r.to_dict() for r in reviews], f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Saved to {args.output}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
