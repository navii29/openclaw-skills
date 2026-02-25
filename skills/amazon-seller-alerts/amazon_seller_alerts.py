#!/usr/bin/env python3
"""
Amazon Seller Central Alerts
Monitors Amazon SP-API for orders, reviews, inventory alerts and sends notifications.
"""

import os
import sys
import json
import time
import hmac
import hashlib
import base64
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import quote
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AmazonOrder:
    """Represents an Amazon order."""
    order_id: str
    purchase_date: str
    status: str
    fulfillment_channel: str
    sales_channel: str
    order_total: str
    currency: str
    buyer_name: str
    buyer_email: str
    shipping_address: Dict[str, str]
    number_of_items: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AmazonReview:
    """Represents an Amazon review."""
    asin: str
    rating: int
    title: str
    content: str
    reviewer_name: str
    review_date: str
    verified_purchase: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InventoryAlert:
    """Represents an inventory alert."""
    asin: str
    sku: str
    title: str
    quantity: int
    alert_type: str  # 'low_stock', 'out_of_stock'
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SPAPIAuth:
    """Handles Amazon Selling Partner API authentication."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        aws_access_key: str,
        aws_secret_key: str,
        region: str = "eu-west-1"
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.region = region
        self.access_token = None
        self.token_expires_at = None
    
    def get_access_token(self) -> str:
        """Get valid access token (refresh if needed)."""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
        
        # Refresh token
        url = "https://api.amazon.com/auth/o2/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(url, data=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            self.access_token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 5min buffer
            
            logger.info("✅ Access token refreshed successfully")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to refresh token: {e}")
            raise
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for SP-API requests."""
        return {
            "x-amz-access-token": self.get_access_token(),
            "Content-Type": "application/json"
        }


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
            logger.error(f"❌ Failed to send Telegram message: {e}")
            return False
    
    def format_order_message(self, order: AmazonOrder) -> str:
        """Format order for Telegram."""
        emoji_channel = "🚀" if order.fulfillment_channel == "AFN" else "📦"
        
        return f"""🛒 <b>Neue Amazon Bestellung</b>

📦 Order-ID: <code>{order.order_id}</code>
👤 Kunde: {order.buyer_name or 'N/A'}
💰 Betrag: {order.order_total} {order.currency}
📊 Menge: {order.number_of_items} Artikel
{emoji_channel} Versand: {'FBA' if order.fulfillment_channel == 'AFN' else 'FBM'}
📍 Channel: {order.sales_channel}

🕐 {self._format_datetime(order.purchase_date)}
"""
    
    def format_review_message(self, review: AmazonReview) -> str:
        """Format review for Telegram."""
        stars = "⭐" * review.rating + "⚫" * (5 - review.rating)
        verified = "✅ Verified" if review.verified_purchase else ""
        
        # Add warning for bad reviews
        warning = ""
        if review.rating <= 2:
            warning = "🚨 <b>NEGATIVE BEWERTUNG!</b>\n\n"
        elif review.rating == 3:
            warning = "⚠️ <b>Neutrale Bewertung</b>\n\n"
        
        return f"""{warning}⭐ <b>Neue Amazon Bewertung</b>

{stars} ({review.rating}/5)
📦 ASIN: <code>{review.asin}</code>
📝 <b>{review.title}</b>
💬 "{review.content[:200]}{'...' if len(review.content) > 200 else ''}"
👤 {review.reviewer_name} {verified}

🕐 {self._format_datetime(review.review_date)}
"""
    
    def format_inventory_alert(self, alert: InventoryAlert) -> str:
        """Format inventory alert for Telegram."""
        emoji = "🔴" if alert.alert_type == "out_of_stock" else "🟡"
        
        return f"""{emoji} <b>Lagerbestands-Warnung</b>

📦 ASIN: <code>{alert.asin}</code>
🏷️ SKU: <code>{alert.sku}</code>
📋 {alert.title}
📊 Bestand: {alert.quantity} Stück

⚠️ Sofort nachbestellen!
"""
    
    def _format_datetime(self, dt_str: str) -> str:
        """Format datetime string."""
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime('%d.%m.%Y %H:%M')
        except:
            return dt_str


class SlackNotifier:
    """Sends notifications via Slack webhook."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_message(self, text: str, blocks: Optional[List[Dict]] = None) -> bool:
        """Send message to Slack."""
        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Failed to send Slack message: {e}")
            return False
    
    def send_order_notification(self, order: AmazonOrder) -> bool:
        """Send order notification to Slack."""
        color = "#36a64f" if order.fulfillment_channel == "AFN" else "#2196F3"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🛒 Neue Amazon Bestellung"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Order ID:*\n`{order.order_id}`"},
                    {"type": "mrkdwn", "text": f"*Kunde:*\n{order.buyer_name or 'N/A'}"},
                    {"type": "mrkdwn", "text": f"*Betrag:*\n{order.order_total} {order.currency}"},
                    {"type": "mrkdwn", "text": f"*Artikel:*\n{order.number_of_items}"},
                    {"type": "mrkdwn", "text": f"*Versand:*\n{'FBA' if order.fulfillment_channel == 'AFN' else 'FBM'}"},
                    {"type": "mrkdwn", "text": f"*Channel:*\n{order.sales_channel}"}
                ]
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"🕐 {order.purchase_date}"}
                ]
            }
        ]
        
        return self.send_message("Neue Amazon Bestellung", blocks)


class AmazonSellerAlerts:
    """Main class for Amazon Seller Central monitoring."""
    
    def __init__(self):
        self.auth = self._init_auth()
        self.notifiers = self._init_notifiers()
        self.marketplace_id = os.getenv("AMAZON_MARKETPLACE_ID", "A1PA6795UKMFR9")  # DE
        self.endpoint = "https://sellingpartnerapi-eu.amazon.com"
        
        # State tracking files
        self.state_dir = os.path.expanduser("~/.amazon_seller_alerts")
        os.makedirs(self.state_dir, exist_ok=True)
    
    def _init_auth(self) -> SPAPIAuth:
        """Initialize SP-API authentication."""
        required_vars = [
            "AMAZON_LWA_CLIENT_ID",
            "AMAZON_LWA_CLIENT_SECRET", 
            "AMAZON_REFRESH_TOKEN",
            "AMAZON_AWS_ACCESS_KEY",
            "AMAZON_AWS_SECRET_KEY"
        ]
        
        missing = [v for v in required_vars if not os.getenv(v)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return SPAPIAuth(
            client_id=os.getenv("AMAZON_LWA_CLIENT_ID"),
            client_secret=os.getenv("AMAZON_LWA_CLIENT_SECRET"),
            refresh_token=os.getenv("AMAZON_REFRESH_TOKEN"),
            aws_access_key=os.getenv("AMAZON_AWS_ACCESS_KEY"),
            aws_secret_key=os.getenv("AMAZON_AWS_SECRET_KEY")
        )
    
    def _init_notifiers(self) -> List[Any]:
        """Initialize notification channels."""
        notifiers = []
        
        # Telegram
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
        if telegram_token and telegram_chat:
            notifiers.append(TelegramNotifier(telegram_token, telegram_chat))
            logger.info("✅ Telegram notifier initialized")
        
        # Slack
        slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        if slack_webhook:
            notifiers.append(SlackNotifier(slack_webhook))
            logger.info("✅ Slack notifier initialized")
        
        if not notifiers:
            logger.warning("⚠️ No notification channels configured!")
        
        return notifiers
    
    def _get_last_check_time(self, check_type: str) -> Optional[datetime]:
        """Get last check time from state file."""
        state_file = os.path.join(self.state_dir, f"{check_type}_last_check.json")
        try:
            with open(state_file, 'r') as f:
                data = json.load(f)
                return datetime.fromisoformat(data['last_check'])
        except (FileNotFoundError, KeyError, ValueError):
            return None
    
    def _save_last_check_time(self, check_type: str, dt: datetime):
        """Save last check time to state file."""
        state_file = os.path.join(self.state_dir, f"{check_type}_last_check.json")
        with open(state_file, 'w') as f:
            json.dump({'last_check': dt.isoformat()}, f)
    
    def _make_api_request(self, method: str, path: str, params: Optional[Dict] = None) -> Dict:
        """Make authenticated API request to SP-API."""
        url = f"{self.endpoint}{path}"
        headers = self.auth.get_headers()
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=params, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                logger.error("❌ Access denied. Check your SP-API permissions.")
            elif response.status_code == 429:
                logger.error("❌ Rate limit exceeded. Waiting...")
                time.sleep(60)
            raise
    
    def check_orders(self, hours_back: int = 24) -> List[AmazonOrder]:
        """Check for new orders."""
        logger.info(f"🔍 Checking orders (last {hours_back}h)...")
        
        # Calculate time range
        last_check = self._get_last_check_time("orders")
        if last_check:
            created_after = last_check.isoformat()
        else:
            created_after = (datetime.utcnow() - timedelta(hours=hours_back)).isoformat()
        
        try:
            params = {
                "MarketplaceIds": self.marketplace_id,
                "CreatedAfter": created_after,
                "OrderStatuses": "Unshipped,PartiallyShipped,Shipped",
                "MaxResultsPerPage": 100
            }
            
            response = self._make_api_request("GET", "/orders/v0/orders", params)
            orders_data = response.get("Orders", [])
            
            orders = []
            for order_data in orders_data:
                order = AmazonOrder(
                    order_id=order_data.get("AmazonOrderId", ""),
                    purchase_date=order_data.get("PurchaseDate", ""),
                    status=order_data.get("OrderStatus", ""),
                    fulfillment_channel=order_data.get("FulfillmentChannel", ""),
                    sales_channel=order_data.get("SalesChannel", "Amazon.de"),
                    order_total=order_data.get("OrderTotal", {}).get("Amount", "0.00"),
                    currency=order_data.get("OrderTotal", {}).get("CurrencyCode", "EUR"),
                    buyer_name=order_data.get("BuyerInfo", {}).get("BuyerName", ""),
                    buyer_email=order_data.get("BuyerInfo", {}).get("BuyerEmail", ""),
                    shipping_address=order_data.get("ShippingAddress", {}),
                    number_of_items=order_data.get("NumberOfItemsShipped", 0) + order_data.get("NumberOfItemsUnshipped", 0)
                )
                orders.append(order)
            
            # Save check time
            self._save_last_check_time("orders", datetime.utcnow())
            
            logger.info(f"✅ Found {len(orders)} new orders")
            
            # Send notifications
            for order in orders:
                self._notify_order(order)
            
            return orders
            
        except Exception as e:
            logger.error(f"❌ Error checking orders: {e}")
            return []
    
    def check_reviews(self) -> List[AmazonReview]:
        """Check for new reviews (via Reports API or Notification API)."""
        logger.info("🔍 Checking for new reviews...")
        
        # Note: Reviews require special SP-API permissions
        # This is a simplified implementation
        
        reviews = []  # Would be populated from API
        logger.info(f"✅ Found {len(reviews)} new reviews")
        
        for review in reviews:
            self._notify_review(review)
        
        return reviews
    
    def check_inventory(self) -> List[InventoryAlert]:
        """Check inventory levels for alerts."""
        logger.info("🔍 Checking inventory...")
        
        try:
            params = {
                "marketplaceId": self.marketplace_id,
                "details": "true"
            }
            
            # This uses the FBA Inventory API
            response = self._make_api_request(
                "GET", 
                "/fba/inventory/v1/summaries",
                params
            )
            
            alerts = []
            inventory_items = response.get("inventorySummaries", [])
            
            for item in inventory_items:
                quantity = item.get("totalQuantity", 0)
                
                # Check thresholds
                if quantity == 0:
                    alert_type = "out_of_stock"
                elif quantity < 10:
                    alert_type = "low_stock"
                else:
                    continue
                
                alert = InventoryAlert(
                    asin=item.get("asin", ""),
                    sku=item.get("sellerSku", ""),
                    title=item.get("productName", "Unknown"),
                    quantity=quantity,
                    alert_type=alert_type
                )
                alerts.append(alert)
            
            logger.info(f"✅ Found {len(alerts)} inventory alerts")
            
            for alert in alerts:
                self._notify_inventory(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error checking inventory: {e}")
            return []
    
    def _notify_order(self, order: AmazonOrder):
        """Send order notification to all channels."""
        for notifier in self.notifiers:
            try:
                if isinstance(notifier, TelegramNotifier):
                    message = notifier.format_order_message(order)
                    notifier.send_message(message)
                elif isinstance(notifier, SlackNotifier):
                    notifier.send_order_notification(order)
            except Exception as e:
                logger.error(f"❌ Failed to notify: {e}")
    
    def _notify_review(self, review: AmazonReview):
        """Send review notification to all channels."""
        for notifier in self.notifiers:
            try:
                if isinstance(notifier, TelegramNotifier):
                    message = notifier.format_review_message(review)
                    notifier.send_message(message)
            except Exception as e:
                logger.error(f"❌ Failed to notify: {e}")
    
    def _notify_inventory(self, alert: InventoryAlert):
        """Send inventory alert to all channels."""
        for notifier in self.notifiers:
            try:
                if isinstance(notifier, TelegramNotifier):
                    message = notifier.format_inventory_alert(alert)
                    notifier.send_message(message)
            except Exception as e:
                logger.error(f"❌ Failed to notify: {e}")
    
    def send_test_notification(self):
        """Send test notification to verify setup."""
        logger.info("🧪 Sending test notification...")
        
        test_order = AmazonOrder(
            order_id="TEST-123-4567890",
            purchase_date=datetime.utcnow().isoformat(),
            status="Unshipped",
            fulfillment_channel="AFN",
            sales_channel="Amazon.de",
            order_total="99.99",
            currency="EUR",
            buyer_name="Max Mustermann",
            buyer_email="max@example.de",
            shipping_address={"City": "Berlin", "CountryCode": "DE"},
            number_of_items=2
        )
        
        self._notify_order(test_order)
        logger.info("✅ Test notification sent")
    
    def run_daemon(self, interval: int = 300):
        """Run as daemon with polling loop."""
        logger.info(f"🚀 Starting daemon (interval: {interval}s)...")
        
        while True:
            try:
                self.check_all()
                logger.info(f"⏳ Sleeping for {interval}s...")
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("🛑 Daemon stopped")
                break
            except Exception as e:
                logger.error(f"❌ Error in daemon loop: {e}")
                time.sleep(60)  # Wait 1 min on error
    
    def check_all(self):
        """Run all checks."""
        logger.info("🔍 Running all checks...")
        self.check_orders()
        self.check_inventory()
        # self.check_reviews()  # Requires special permissions


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Amazon Seller Central Alerts"
    )
    parser.add_argument("--orders", action="store_true", help="Check orders only")
    parser.add_argument("--inventory", action="store_true", help="Check inventory only")
    parser.add_argument("--reviews", action="store_true", help="Check reviews only")
    parser.add_argument("--check-all", action="store_true", help="Run all checks")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--interval", type=int, default=300, help="Daemon interval (seconds)")
    parser.add_argument("--test", action="store_true", help="Send test notification")
    parser.add_argument("--hours", type=int, default=24, help="Hours back for orders")
    
    args = parser.parse_args()
    
    try:
        alerts = AmazonSellerAlerts()
        
        if args.test:
            alerts.send_test_notification()
        elif args.daemon:
            alerts.run_daemon(args.interval)
        elif args.orders:
            alerts.check_orders(args.hours)
        elif args.inventory:
            alerts.check_inventory()
        elif args.reviews:
            alerts.check_reviews()
        elif args.check_all:
            alerts.check_all()
        else:
            # Default: check all
            alerts.check_all()
            
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
