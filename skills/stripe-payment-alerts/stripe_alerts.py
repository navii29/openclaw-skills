#!/usr/bin/env python3
"""
Stripe Payment Alerts
Receive Stripe webhooks and send instant notifications.
"""

import json
import hmac
import hashlib
import requests
from datetime import datetime
from typing import Dict, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler


class StripeWebhookHandler:
    """Handle Stripe webhook events."""
    
    IMPORTANT_EVENTS = [
        'checkout.session.completed',
        'invoice.payment_succeeded',
        'invoice.payment_failed',
        'customer.subscription.created',
        'customer.subscription.deleted',
        'charge.refunded',
        'charge.dispute.created'
    ]
    
    def __init__(self, webhook_secret: Optional[str] = None):
        self.webhook_secret = webhook_secret
    
    def verify_signature(self, payload: bytes, sig_header: str) -> bool:
        """Verify Stripe webhook signature."""
        if not self.webhook_secret:
            return True  # Skip verification if no secret provided
        
        try:
            timestamp, signature = sig_header.split(',')
            timestamp = timestamp.split('=')[1]
            signature = signature.split('=')[1]
            
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False
    
    def parse_event(self, payload: bytes) -> Optional[Dict]:
        """Parse webhook payload."""
        try:
            return json.loads(payload.decode('utf-8'))
        except Exception:
            return None
    
    def should_notify(self, event_type: str) -> bool:
        """Check if event type should trigger notification."""
        return event_type in self.IMPORTANT_EVENTS
    
    def extract_payment_info(self, event: Dict) -> Optional[Dict]:
        """Extract relevant payment information."""
        event_type = event.get('type', '')
        data = event.get('data', {}).get('object', {})
        
        info = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'stripe_id': data.get('id', ''),
        }
        
        if event_type == 'checkout.session.completed':
            info.update({
                'type': 'new_payment',
                'emoji': '💰',
                'title': 'Neue Zahlung!',
                'amount': data.get('amount_total', 0) / 100,
                'currency': data.get('currency', 'eur').upper(),
                'customer_email': data.get('customer_details', {}).get('email', 'N/A'),
                'customer_name': data.get('customer_details', {}).get('name', 'N/A'),
                'status': data.get('payment_status', 'unknown')
            })
        
        elif event_type == 'invoice.payment_succeeded':
            lines = data.get('lines', {}).get('data', [])
            description = lines[0].get('description', 'Abonnement') if lines else 'Abonnement'
            
            info.update({
                'type': 'subscription_payment',
                'emoji': '💵',
                'title': 'Abonnement-Zahlung!',
                'amount': data.get('amount_paid', 0) / 100,
                'currency': data.get('currency', 'eur').upper(),
                'customer_email': data.get('customer_email', 'N/A'),
                'description': description,
                'subscription_id': data.get('subscription', 'N/A')[:10]
            })
        
        elif event_type == 'invoice.payment_failed':
            info.update({
                'type': 'payment_failed',
                'emoji': '⚠️',
                'title': 'Zahlung fehlgeschlagen!',
                'amount': data.get('amount_due', 0) / 100,
                'currency': data.get('currency', 'eur').upper(),
                'customer_email': data.get('customer_email', 'N/A'),
                'attempt_count': data.get('attempt_count', 1),
                'next_payment_attempt': data.get('next_payment_attempt')
            })
        
        elif event_type == 'customer.subscription.created':
            info.update({
                'type': 'new_subscription',
                'emoji': '🎉',
                'title': 'Neues Abonnement!',
                'customer_id': data.get('customer', 'N/A')[:10],
                'plan': data.get('plan', {}).get('nickname', 'Unbekannt'),
                'amount': data.get('plan', {}).get('amount', 0) / 100,
                'interval': data.get('plan', {}).get('interval', 'month'),
                'status': data.get('status', 'unknown')
            })
        
        elif event_type == 'customer.subscription.deleted':
            info.update({
                'type': 'subscription_cancelled',
                'emoji': '💔',
                'title': 'Abonnement gekündigt',
                'customer_id': data.get('customer', 'N/A')[:10],
                'cancellation_reason': data.get('cancellation_reason', 'Nicht angegeben')
            })
        
        elif event_type == 'charge.refunded':
            info.update({
                'type': 'refund',
                'emoji': '↩️',
                'title': 'Rückerstattung!',
                'amount': data.get('amount_refunded', 0) / 100,
                'currency': data.get('currency', 'eur').upper(),
                'reason': data.get('reason', 'Nicht angegeben'),
                'receipt_url': data.get('receipt_url', '')
            })
        
        elif event_type == 'charge.dispute.created':
            info.update({
                'type': 'dispute',
                'emoji': '🚨',
                'title': 'CHARGEBACK!',
                'amount': data.get('amount', 0) / 100,
                'currency': data.get('currency', 'eur').upper(),
                'reason': data.get('reason', 'Nicht angegeben'),
                'status': data.get('status', 'unknown')
            })
        
        else:
            return None
        
        return info


class TelegramNotifier:
    """Send notifications via Telegram."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def format_message(self, info: Dict) -> str:
        """Format payment info for Telegram."""
        emoji = info.get('emoji', '💳')
        title = info.get('title', 'Stripe Event')
        
        message = f"{emoji} <b>{title}</b>\n\n"
        
        if 'customer_name' in info:
            message += f"👤 <b>Kunde:</b> {info['customer_name']}\n"
        if 'customer_email' in info:
            message += f"📧 <b>Email:</b> {info['customer_email']}\n"
        if 'customer_id' in info:
            message += f"🆔 <b>Kunde:</b> {info['customer_id']}\n"
        
        if 'amount' in info:
            amount = info['amount']
            currency = info.get('currency', 'EUR')
            message += f"💵 <b>Betrag:</b> {amount:.2f} {currency}\n"
        
        if 'description' in info:
            message += f"📝 <b>Produkt:</b> {info['description']}\n"
        if 'plan' in info:
            message += f"📋 <b>Plan:</b> {info['plan']}\n"
        
        if 'interval' in info:
            interval_map = {'month': 'Monatlich', 'year': 'Jährlich'}
            message += f"🔄 <b>Abrechnung:</b> {interval_map.get(info['interval'], info['interval'])}\n"
        
        if 'attempt_count' in info:
            message += f"🔄 <b>Versuch:</b> {info['attempt_count']}\n"
        
        if 'reason' in info:
            message += f"❓ <b>Grund:</b> {info['reason']}\n"
        
        if 'status' in info:
            message += f"📊 <b>Status:</b> {info['status']}\n"
        
        message += f"\n🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
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
            return response.status_code == 200 and response.json().get('ok')
        except Exception as e:
            print(f"Telegram error: {e}")
            return False


class SlackNotifier:
    """Send notifications via Slack."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send(self, info: Dict) -> bool:
        """Send notification to Slack."""
        emoji = info.get('emoji', '💳')
        title = info.get('title', 'Stripe Event')
        
        # Build fields
        fields = []
        
        if 'customer_name' in info:
            fields.append({"title": "Kunde", "value": info['customer_name'], "short": True})
        if 'customer_email' in info:
            fields.append({"title": "Email", "value": info['customer_email'], "short": True})
        if 'amount' in info:
            fields.append({"title": "Betrag", "value": f"{info['amount']:.2f} {info.get('currency', 'EUR')}", "short": True})
        if 'description' in info:
            fields.append({"title": "Produkt", "value": info['description'], "short": True})
        
        color_map = {
            'new_payment': 'good',
            'subscription_payment': 'good',
            'new_subscription': 'good',
            'payment_failed': 'warning',
            'subscription_cancelled': 'danger',
            'refund': 'warning',
            'dispute': 'danger'
        }
        
        payload = {
            "attachments": [{
                "fallback": f"{title}",
                "color": color_map.get(info.get('type'), '#cccccc'),
                "title": f"{emoji} {title}",
                "fields": fields,
                "footer": "Stripe Payments",
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Slack error: {e}")
            return False


class WebhookServer:
    """HTTP server to receive Stripe webhooks."""
    
    def __init__(self, stripe_handler: StripeWebhookHandler, 
                 telegram: Optional[TelegramNotifier] = None,
                 slack: Optional[SlackNotifier] = None,
                 port: int = 8000):
        self.stripe = stripe_handler
        self.telegram = telegram
        self.slack = slack
        self.port = port
    
    def start(self):
        """Start the webhook server."""
        handler = self._create_handler()
        server = HTTPServer(('', self.port), handler)
        
        print(f"🚀 Stripe webhook server starting on port {self.port}")
        print(f"📍 Webhook URL: http://your-domain:{self.port}/webhook/stripe")
        print("Press Ctrl+C to stop\n")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
    
    def _create_handler(self):
        """Create request handler class."""
        stripe_handler = self.stripe
        telegram = self.telegram
        slack = self.slack
        
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass
            
            def do_POST(self):
                if self.path == '/webhook/stripe':
                    content_length = int(self.headers.get('Content-Length', 0))
                    payload = self.rfile.read(content_length)
                    
                    # Verify signature
                    sig_header = self.headers.get('Stripe-Signature', '')
                    if not stripe_handler.verify_signature(payload, sig_header):
                        self.send_response(400)
                        self.end_headers()
                        return
                    
                    # Parse event
                    event = stripe_handler.parse_event(payload)
                    if not event:
                        self.send_response(400)
                        self.end_headers()
                        return
                    
                    event_type = event.get('type', '')
                    print(f"📨 Received: {event_type}")
                    
                    # Check if we should notify
                    if stripe_handler.should_notify(event_type):
                        info = stripe_handler.extract_payment_info(event)
                        if info:
                            print(f"   🔔 Notifying: {info.get('title')}")
                            
                            if telegram:
                                telegram.send(info)
                            if slack:
                                slack.send(info)
                    
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
                    self.wfile.write(json.dumps({"status": "ok"}).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
        
        return Handler


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stripe Payment Alerts')
    parser.add_argument('--webhook-secret', help='Stripe Webhook Secret')
    parser.add_argument('--telegram-token', help='Telegram Bot Token')
    parser.add_argument('--telegram-chat', help='Telegram Chat ID')
    parser.add_argument('--slack-webhook', help='Slack Webhook URL')
    parser.add_argument('--port', type=int, default=8000, help='Server port')
    parser.add_argument('--test', action='store_true', help='Send test notification')
    
    args = parser.parse_args()
    
    # Initialize notifiers
    telegram = None
    slack = None
    
    if args.telegram_token and args.telegram_chat:
        telegram = TelegramNotifier(args.telegram_token, args.telegram_chat)
    
    if args.slack_webhook:
        slack = SlackNotifier(args.slack_webhook)
    
    # Test mode
    if args.test:
        print("🧪 Sending test notification...")
        test_info = {
            'type': 'new_payment',
            'emoji': '💰',
            'title': 'Test Zahlung!',
            'amount': 99.99,
            'currency': 'EUR',
            'customer_name': 'Max Mustermann',
            'customer_email': 'max@example.de',
            'description': 'Pro Plan'
        }
        
        if telegram:
            success = telegram.send(test_info)
            print(f"   Telegram: {'✅' if success else '❌'}")
        
        if slack:
            success = slack.send(test_info)
            print(f"   Slack: {'✅' if success else '❌'}")
        
        return
    
    # Start server
    stripe_handler = StripeWebhookHandler(args.webhook_secret)
    server = WebhookServer(stripe_handler, telegram, slack, args.port)
    server.start()


if __name__ == "__main__":
    main()
