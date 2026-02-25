#!/usr/bin/env python3
"""Test Shopify Telegram Alerts"""

import sys
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace/skills/shopify-telegram-alerts')

from shopify_telegram import ShopifyTelegramAlerts

# Telegram Config (from TOOLS.md)
TELEGRAM_TOKEN = "8294286642:AAFKb09yfYMA5G4xrrr0yz0RCnHaph7IpBw"
TELEGRAM_CHAT_ID = "6599716126"

def run_tests():
    """Run all tests."""
    print("🧪 Testing Shopify Telegram Alerts...\n")
    
    alerts = ShopifyTelegramAlerts(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    
    # Test 1: Standard Order
    print("Test 1: Standard Bestellung")
    order1 = {
        "name": "#1001",
        "order_number": 1001,
        "total_price": "89.99",
        "currency": "EUR",
        "customer": {
            "first_name": "Anna",
            "last_name": "Schmidt",
            "email": "anna.schmidt@web.de"
        },
        "email": "anna.schmidt@web.de",
        "shipping_address": {
            "city": "München",
            "country": "DE"
        },
        "line_items": [
            {"title": "Bio-Kaffee 500g", "quantity": 2, "price": "29.99"},
            {"title": "Tasse Keramik", "quantity": 1, "price": "19.99"}
        ],
        "tags": ""
    }
    
    result1 = alerts.process_webhook(order1)
    print(f"   Result: {'✅ Sent' if result1 else '❌ Failed'}\n")
    
    # Test 2: Express Order
    print("Test 2: Express Bestellung (mit Priority Tag)")
    order2 = {
        "name": "#1002",
        "order_number": 1002,
        "total_price": "249.50",
        "currency": "EUR",
        "customer": {
            "first_name": "Klaus",
            "last_name": "Weber",
            "email": "klaus.weber@firma.de"
        },
        "email": "klaus.weber@firma.de",
        "shipping_address": {
            "city": "Hamburg",
            "country": "DE"
        },
        "line_items": [
            {"title": "Premium Laptopständer", "quantity": 5, "price": "49.90"}
        ],
        "tags": "express, b2b"
    }
    
    result2 = alerts.process_webhook(order2)
    print(f"   Result: {'✅ Sent' if result2 else '❌ Failed'}\n")
    
    # Test 3: Guest Order
    print("Test 3: Gast-Bestellung (ohne Kundenkonto)")
    order3 = {
        "name": "#1003",
        "order_number": 1003,
        "total_price": "12.99",
        "currency": "EUR",
        "customer": None,
        "email": "gast@email.de",
        "shipping_address": {
            "city": "Köln",
            "country": "DE"
        },
        "line_items": [
            {"title": "Sticker Set", "quantity": 1, "price": "12.99"}
        ],
        "tags": ""
    }
    
    result3 = alerts.process_webhook(order3)
    print(f"   Result: {'✅ Sent' if result3 else '❌ Failed'}\n")
    
    # Summary
    total = 3
    passed = sum([result1, result2, result3])
    print(f"📊 Test Summary: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Skill is ready for production.")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
