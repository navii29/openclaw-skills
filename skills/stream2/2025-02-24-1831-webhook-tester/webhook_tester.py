#!/usr/bin/env python3
"""
Webhook Tester
Test webhook endpoints with various payloads.
Supports n8n, Make, Zapier, and custom webhooks.
"""

import urllib.request
import urllib.parse
import json
import sys
from datetime import datetime

# Common webhook test payloads
PAYLOADS = {
    'lead': {
        "event": "new_lead",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "name": "Test Lead",
            "email": "test@example.com",
            "source": "website",
            "score": 8
        }
    },
    'contact': {
        "event": "contact_form",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "name": "Max Mustermann",
            "email": "max@firma.de",
            "message": "Ich interessiere mich für Automation",
            "phone": "+49 123 456789"
        }
    },
    'order': {
        "event": "new_order",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "order_id": "ORD-12345",
            "customer": "test@example.com",
            "amount": 99.99,
            "currency": "EUR"
        }
    },
    'simple': {
        "test": True,
        "timestamp": datetime.now().isoformat()
    }
}

def test_webhook(url, payload_name='simple', custom_payload=None, headers=None):
    """Test a webhook endpoint"""
    
    # Get payload
    if custom_payload:
        payload = custom_payload
    else:
        payload = PAYLOADS.get(payload_name, PAYLOADS['simple'])
    
    # Prepare request
    data = json.dumps(payload).encode('utf-8')
    
    # Default headers
    req_headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'WebhookTester/1.0'
    }
    
    # Add custom headers
    if headers:
        req_headers.update(headers)
    
    print(f"\n🌐 Testing Webhook")
    print(f"   URL: {url}")
    print(f"   Payload: {payload_name}")
    print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)
    
    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers=req_headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            status = response.status
            response_body = response.read().decode('utf-8')
            
            print(f"✅ Status: {status}")
            print(f"📄 Response: {response_body[:200]}")
            
            if status in [200, 201, 202, 204]:
                print("\n🎉 Webhook test PASSED!")
                return True
            else:
                print(f"\n⚠️ Unexpected status: {status}")
                return False
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        print(f"   Response: {e.read().decode('utf-8')[:200]}")
        return False
    except urllib.error.URLError as e:
        print(f"❌ URL Error: {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_multiple(urls, payload_name='simple'):
    """Test multiple webhooks"""
    print(f"\n🔄 Batch Webhook Test")
    print(f"   Payload: {payload_name}")
    print("=" * 60)
    
    results = []
    for url in urls:
        success = test_webhook(url, payload_name)
        results.append((url, success))
    
    print("\n" + "=" * 60)
    print("📊 BATCH RESULTS:")
    passed = sum(1 for _, s in results if s)
    for url, success in results:
        status = "✅" if success else "❌"
        print(f"   {status} {url[:50]}...")
    print(f"\nPassed: {passed}/{len(results)}")
    
    return results

def n8n_test():
    """Test n8n webhook"""
    # n8n cloud webhook format
    n8n_url = input("Enter n8n webhook URL: ").strip()
    if n8n_url:
        test_webhook(n8n_url, 'lead')

def show_payloads():
    """Show available payloads"""
    print("\n📦 Available Payloads:")
    for name, payload in PAYLOADS.items():
        print(f"\n   {name}:")
        print(f"   {json.dumps(payload, indent=4)[:200]}...")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Webhook Tester')
    parser.add_argument('url', nargs='?', help='Webhook URL to test')
    parser.add_argument('-p', '--payload', default='simple', 
                       choices=list(PAYLOADS.keys()),
                       help='Payload type')
    parser.add_argument('-l', '--list', action='store_true',
                       help='List available payloads')
    
    args = parser.parse_args()
    
    if args.list:
        show_payloads()
    elif args.url:
        test_webhook(args.url, args.payload)
    else:
        print("🌐 Webhook Tester")
        print("=" * 50)
        print("\nUsage:")
        print("  python3 webhook_tester.py https://hook.example.com -p lead")
        print("  python3 webhook_tester.py -l")
        print("\nPayloads:", ', '.join(PAYLOADS.keys()))
        print("\nInteractive mode:")
        n8n_test()
