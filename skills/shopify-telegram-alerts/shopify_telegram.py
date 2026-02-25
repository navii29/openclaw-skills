#!/usr/bin/env python3
"""
Shopify Order-to-Telegram Alert System
Sends instant Telegram notifications for new Shopify orders.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class ShopifyTelegramAlerts:
    """Send Shopify order notifications to Telegram."""
    
    def __init__(self, telegram_token: str, telegram_chat_id: str):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.telegram_api = f"https://api.telegram.org/bot{telegram_token}"
    
    def format_order_message(self, order: Dict[str, Any]) -> str:
        """Format Shopify order for Telegram."""
        order_id = order.get('name', f"#{order.get('order_number', 'N/A')}")
        customer = order.get('customer') or {}
        customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "Gast"
        email = customer.get('email') or order.get('email', 'N/A')
        
        total = order.get('total_price', '0.00')
        currency = order.get('currency', 'EUR')
        line_items = order.get('line_items', [])
        item_count = len(line_items)
        
        shipping = order.get('shipping_address') or {}
        shipping_city = shipping.get('city', 'N/A')
        shipping_country = shipping.get('country', 'DE')
        
        # Calculate item summary
        item_summary = []
        for item in line_items[:3]:  # Show first 3 items
            title = item.get('title', 'Artikel')
            qty = item.get('quantity', 1)
            price = item.get('price', '0.00')
            item_summary.append(f"• {title} x{qty} ({price}{currency})")
        
        if len(line_items) > 3:
            item_summary.append(f"• ... und {len(line_items) - 3} weitere Artikel")
        
        items_text = "\n".join(item_summary)
        
        # Build message
        message = f"""🛒 <b>Neue Bestellung {order_id}</b>

👤 <b>Kunde:</b> {customer_name}
📧 {email}
📍 {shipping_city}, {shipping_country}

💰 <b>Gesamtsumme:</b> {total} {currency}
📦 <b>Artikel ({item_count}):</b>
{items_text}

🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
        
        # Add tags for priority
        tags = order.get('tags', '')
        if 'express' in tags.lower() or 'priority' in tags.lower():
            message = "⚡ <b>EXPRESS BESTELLUNG</b>\n\n" + message
        
        return message
    
    def send_telegram_message(self, message: str) -> bool:
        """Send message to Telegram."""
        url = f"{self.telegram_api}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                result = response.json()
                return result.get('ok', False)
            else:
                print(f"Telegram API Error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False
    
    def process_webhook(self, order_data: Dict[str, Any]) -> bool:
        """Process incoming Shopify webhook."""
        try:
            message = self.format_order_message(order_data)
            return self.send_telegram_message(message)
        except Exception as e:
            print(f"Error processing webhook: {e}")
            return False


class WebhookHandler(BaseHTTPRequestHandler):
    """HTTP Request handler for Shopify webhooks."""
    
    alerts = None
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/webhook/shopify':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                success = self.alerts.process_webhook(data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success" if success else "error"}).encode())
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()


class WebhookServer:
    """Simple webhook server for Shopify."""
    
    def __init__(self, telegram_token: str, telegram_chat_id: str, port: int = 8000):
        WebhookHandler.alerts = ShopifyTelegramAlerts(telegram_token, telegram_chat_id)
        self.port = port
        self.server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    
    def start(self):
        """Start the webhook server."""
        print(f"🚀 Webhook server starting on port {self.port}")
        print(f"📍 Webhook URL: http://your-domain:{self.port}/webhook/shopify")
        print(f"💡 Health check: http://localhost:{self.port}/health")
        print("Press Ctrl+C to stop\n")
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")


def create_shopify_webhook(store_url: str, api_key: str, api_secret: str, webhook_url: str):
    """Create Shopify webhook programmatically."""
    
    url = f"https://{api_key}:{api_secret}@{store_url}/admin/api/2024-01/webhooks.json"
    
    payload = {
        "webhook": {
            "topic": "orders/create",
            "address": webhook_url,
            "format": "json"
        }
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code in [200, 201]:
        print("✅ Shopify webhook created successfully")
        return response.json()
    else:
        print(f"❌ Failed to create webhook: {response.status_code}")
        print(response.text)
        return None


# CLI Usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Shopify Order Alerts to Telegram")
    parser.add_argument("--token", required=True, help="Telegram Bot Token")
    parser.add_argument("--chat-id", required=True, help="Telegram Chat ID")
    parser.add_argument("--port", type=int, default=8000, help="Webhook server port")
    parser.add_argument("--test", action="store_true", help="Send test message")
    
    args = parser.parse_args()
    
    alerts = ShopifyTelegramAlerts(args.token, args.chat_id)
    
    if args.test:
        # Send test order
        test_order = {
            "name": "#TEST-1001",
            "order_number": 1001,
            "total_price": "149.99",
            "currency": "EUR",
            "customer": {
                "first_name": "Max",
                "last_name": "Mustermann",
                "email": "max@example.de"
            },
            "email": "max@example.de",
            "shipping_address": {
                "city": "Berlin",
                "country": "DE"
            },
            "line_items": [
                {"title": "Premium T-Shirt", "quantity": 2, "price": "49.99"},
                {"title": "Sticker Pack", "quantity": 1, "price": "9.99"}
            ],
            "tags": ""
        }
        
        result = alerts.process_webhook(test_order)
        print(f"Test message sent: {'✅ Success' if result else '❌ Failed'}")
    else:
        # Start webhook server
        server = WebhookServer(args.token, args.chat_id, args.port)
        server.start()
