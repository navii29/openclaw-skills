#!/usr/bin/env python3
"""
WooCommerce Order Alerts
Receive WooCommerce webhooks and send instant notifications.
"""

import json
import requests
from datetime import datetime
from typing import Dict, Optional, List
from http.server import HTTPServer, BaseHTTPRequestHandler


class WooCommerceWebhookHandler:
    """Handle WooCommerce webhook events."""
    
    def parse_order(self, payload: bytes) -> Optional[Dict]:
        """Parse WooCommerce order webhook payload."""
        try:
            data = json.loads(payload.decode('utf-8'))
            return data
        except Exception as e:
            print(f"Error parsing webhook: {e}")
            return None
    
    def extract_order_info(self, order: Dict) -> Dict:
        """Extract relevant order information."""
        order_id = order.get('id', 'N/A')
        order_number = order.get('number', order_id)
        
        # Customer info
        billing = order.get('billing', {})
        customer_name = f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip()
        customer_email = billing.get('email', 'N/A')
        customer_phone = billing.get('phone', '')
        
        # Order totals
        total = order.get('total', '0.00')
        currency = order.get('currency', 'EUR')
        
        # Items
        line_items = order.get('line_items', [])
        item_count = len(line_items)
        item_summary = []
        
        for item in line_items[:3]:  # Show first 3 items
            name = item.get('name', 'Artikel')
            qty = item.get('quantity', 1)
            price = item.get('price', '0.00')
            item_summary.append(f"• {name} x{qty}")
        
        if len(line_items) > 3:
            item_summary.append(f"• ... und {len(line_items) - 3} weitere")
        
        # Shipping
        shipping = order.get('shipping', {})
        shipping_method = order.get('shipping_lines', [{}])[0].get('method_title', 'Standard')
        shipping_city = shipping.get('city', '')
        
        # Payment method
        payment_method = order.get('payment_method_title', 'Unbekannt')
        
        # Status and priority
        status = order.get('status', 'pending')
        
        # Determine priority
        priority = "📌 NORMAL"
        if 'express' in shipping_method.lower() or 'schnell' in shipping_method.lower():
            priority = "⚡ EXPRESS"
        if total and float(total) > 500:
            priority = "💰 GROSSBESTELLUNG"
        if 'b2b' in str(order.get('customer_note', '')).lower():
            priority = "🏢 B2B"
        
        return {
            'order_id': order_number,
            'customer_name': customer_name or 'Gast',
            'customer_email': customer_email,
            'customer_phone': customer_phone,
            'total': total,
            'currency': currency,
            'item_count': item_count,
            'items': item_summary,
            'shipping_method': shipping_method,
            'shipping_city': shipping_city,
            'payment_method': payment_method,
            'status': status,
            'priority': priority,
            'customer_note': order.get('customer_note', ''),
            'created_at': order.get('date_created', datetime.now().isoformat())
        }


class TelegramNotifier:
    """Send notifications via Telegram."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def format_message(self, info: Dict) -> str:
        """Format order info for Telegram."""
        items_text = "\n".join(info['items'])
        
        message = f"""🛒 <b>NEUE BESTELLUNG #{info['order_id']}</b>

{info['priority']}

👤 <b>Kunde:</b> {info['customer_name']}
📧 <b>Email:</b> {info['customer_email']}
📱 <b>Telefon:</b> {info['customer_phone'] or 'N/A'}
🏙 <b>Ort:</b> {info['shipping_city'] or 'N/A'}

💰 <b>Gesamtsumme:</b> {info['total']} {info['currency']}
📦 <b>Artikel ({info['item_count']}):</b>
{items_text}

🚚 <b>Versand:</b> {info['shipping_method']}
💳 <b>Zahlung:</b> {info['payment_method']}
"""
        
        if info['customer_note']:
            message += f"\n📝 <b>Notiz:</b> {info['customer_note'][:200]}"
        
        message += f"\n\n🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        return message
    
    def send(self, info: Dict) -> bool:
        """Send notification."""
        url = f"{self.api_url}/sendMessage"
        
        payload = {
            "chat_id": self.chat_id,
            "text": self.format_message(info),
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            success = response.status_code == 200 and response.json().get('ok')
            if success:
                print(f"   ✅ Telegram sent")
            else:
                print(f"   ❌ Telegram failed: {response.text}")
            return success
        except Exception as e:
            print(f"   ❌ Telegram error: {e}")
            return False


class WebhookServer:
    """HTTP server to receive WooCommerce webhooks."""
    
    def __init__(self, woocommerce_handler: WooCommerceWebhookHandler,
                 telegram: Optional[TelegramNotifier] = None,
                 port: int = 8000):
        self.wc = woocommerce_handler
        self.telegram = telegram
        self.port = port
    
    def start(self):
        """Start the webhook server."""
        handler = self._create_handler()
        server = HTTPServer(('', self.port), handler)
        
        print(f"🚀 WooCommerce webhook server starting on port {self.port}")
        print(f"📍 Webhook URL: http://your-domain:{self.port}/webhook/woocommerce")
        print("\n⚙️  WooCommerce Setup:")
        print("   1. Go to WooCommerce → Settings → Advanced → Webhooks")
        print("   2. Add new webhook:")
        print("      - Topic: Order created")
        print(f"     - Delivery URL: http://your-domain:{self.port}/webhook/woocommerce")
        print("      - API Version: WP REST API Integration v3")
        print("\nPress Ctrl+C to stop\n")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
    
    def _create_handler(self):
        """Create request handler class."""
        wc_handler = self.wc
        telegram = self.telegram
        
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass
            
            def do_POST(self):
                if self.path == '/webhook/woocommerce':
                    content_length = int(self.headers.get('Content-Length', 0))
                    payload = self.rfile.read(content_length)
                    
                    # Parse order
                    order = wc_handler.parse_order(payload)
                    if not order:
                        self.send_response(400)
                        self.end_headers()
                        return
                    
                    # Extract info
                    info = wc_handler.extract_order_info(order)
                    
                    print(f"🛒 Order #{info['order_id']}: {info['customer_name']} - {info['total']} {info['currency']}")
                    
                    # Send notification
                    if telegram:
                        telegram.send(info)
                    
                    self.send_response(200)
                    self.end_headers()
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok", "service": "woocommerce-alerts"}).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
        
        return Handler


def create_test_order() -> Dict:
    """Create a test order for testing."""
    return {
        "id": 1234,
        "number": "1234",
        "status": "processing",
        "currency": "EUR",
        "total": "149.99",
        "date_created": datetime.now().isoformat(),
        "billing": {
            "first_name": "Maria",
            "last_name": "Schmidt",
            "email": "maria@web.de",
            "phone": "+49 170 12345678"
        },
        "shipping": {
            "city": "Berlin"
        },
        "line_items": [
            {"name": "Premium T-Shirt", "quantity": 2, "price": "29.99"},
            {"name": "Hoodie Schwarz", "quantity": 1, "price": "59.99"},
            {"name": "Sticker Pack", "quantity": 3, "price": "9.99"}
        ],
        "shipping_lines": [
            {"method_title": "DHL Express"}
        ],
        "payment_method_title": "PayPal",
        "customer_note": "Bitte Geschenkverpackung"
    }


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='WooCommerce Order Alerts')
    parser.add_argument('--telegram-token', help='Telegram Bot Token')
    parser.add_argument('--telegram-chat', help='Telegram Chat ID')
    parser.add_argument('--port', type=int, default=8000, help='Server port')
    parser.add_argument('--test', action='store_true', help='Send test notification')
    
    args = parser.parse_args()
    
    # Initialize
    telegram = None
    if args.telegram_token and args.telegram_chat:
        telegram = TelegramNotifier(args.telegram_token, args.telegram_chat)
    
    # Test mode
    if args.test:
        print("🧪 Sending test notification...")
        
        if not telegram:
            print("❌ Telegram not configured")
            return
        
        test_order = create_test_order()
        handler = WooCommerceWebhookHandler()
        info = handler.extract_order_info(test_order)
        
        success = telegram.send(info)
        print(f"\nTest: {'✅ Success' if success else '❌ Failed'}")
        return
    
    # Start server
    wc_handler = WooCommerceWebhookHandler()
    server = WebhookServer(wc_handler, telegram, args.port)
    server.start()


if __name__ == "__main__":
    main()
