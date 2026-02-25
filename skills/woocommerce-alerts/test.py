#!/usr/bin/env python3
"""Test WooCommerce Order Alerts"""

import sys
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace/skills/woocommerce-alerts')

from woocommerce_alerts import WooCommerceWebhookHandler, TelegramNotifier

def run_tests():
    """Test WooCommerce webhook handling."""
    print("🧪 Testing WooCommerce Order Alerts...\n")
    
    # Test 1: Order parsing
    print("Test 1: Bestellung Parsen")
    handler = WooCommerceWebhookHandler()
    
    test_order = {
        "id": 1234,
        "number": "1234",
        "status": "processing",
        "currency": "EUR",
        "total": "149.99",
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
            {"name": "Hoodie Schwarz", "quantity": 1, "price": "59.99"}
        ],
        "shipping_lines": [
            {"method_title": "DHL Express"}
        ],
        "payment_method_title": "PayPal"
    }
    
    info = handler.extract_order_info(test_order)
    
    print(f"   Order ID: {info['order_id']}")
    print(f"   Customer: {info['customer_name']}")
    print(f"   Email: {info['customer_email']}")
    print(f"   Total: {info['total']} {info['currency']}")
    print(f"   Items: {info['item_count']}")
    print(f"   Priority: {info['priority']}")
    
    test1_pass = (
        info['order_id'] == '1234' and
        info['customer_name'] == 'Maria Schmidt' and
        info['total'] == '149.99' and
        info['item_count'] == 2 and
        'EXPRESS' in info['priority']
    )
    print(f"   Status: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print()
    
    # Test 2: Priority detection
    print("Test 2: Prioritäts-Erkennung")
    
    test_cases = [
        {
            'order': {'total': '50.00', 'shipping_lines': [{'method_title': 'Standard'}], 'customer_note': ''},
            'expected': 'NORMAL'
        },
        {
            'order': {'total': '600.00', 'shipping_lines': [{'method_title': 'Standard'}], 'customer_note': ''},
            'expected': 'GROSSBESTELLUNG'
        },
        {
            'order': {'total': '50.00', 'shipping_lines': [{'method_title': 'Express'}], 'customer_note': ''},
            'expected': 'EXPRESS'
        },
        {
            'order': {'total': '50.00', 'shipping_lines': [{'method_title': 'Standard'}], 'customer_note': 'B2B Kunde'},
            'expected': 'B2B'
        }
    ]
    
    priority_pass = True
    for test in test_cases:
        base_order = {
            "id": 1, "number": "1", "status": "processing", "currency": "EUR",
            "billing": {"first_name": "Test", "last_name": "User", "email": "test@test.de"},
            "shipping": {}, "line_items": [], "payment_method_title": "PayPal"
        }
        base_order.update(test['order'])
        info = handler.extract_order_info(base_order)
        
        result = test['expected'] in info['priority']
        status = "✅" if result else "❌"
        print(f"   {status} {test['expected']} in {info['priority']}")
        if not result:
            priority_pass = False
    print()
    
    # Test 3: Telegram message formatting
    print("Test 3: Telegram Formatierung")
    notifier = TelegramNotifier("fake-token", "fake-chat")
    
    test_info = {
        'order_id': '1234',
        'customer_name': 'Test Kunde',
        'customer_email': 'test@kunde.de',
        'customer_phone': '+49 123 456789',
        'total': '299.99',
        'currency': 'EUR',
        'item_count': 3,
        'items': ['• T-Shirt x2', '• Hoodie x1'],
        'shipping_method': 'DHL',
        'shipping_city': 'München',
        'payment_method': 'PayPal',
        'priority': '💰 GROSSBESTELLUNG',
        'customer_note': 'Bitte schnell'
    }
    
    msg = notifier.format_message(test_info)
    
    format_checks = [
        'BESTELLUNG #1234' in msg,
        'Test Kunde' in msg,
        '299.99' in msg,
        'T-Shirt' in msg,
        'DHL' in msg,
        'PayPal' in msg,
        '<b>' in msg  # HTML tags
    ]
    
    format_pass = all(format_checks)
    print(f"   Order ID: {'✅' if 'BESTELLUNG #1234' in msg else '❌'}")
    print(f"   Customer: {'✅' if 'Test Kunde' in msg else '❌'}")
    print(f"   Amount: {'✅' if '299.99' in msg else '❌'}")
    print(f"   HTML: {'✅' if '<b>' in msg else '❌'}")
    print(f"   Status: {'✅ PASS' if format_pass else '❌ FAIL'}")
    print()
    
    # Test 4: Guest order handling
    print("Test 4: Gast-Bestellung")
    guest_order = {
        "id": 999,
        "number": "999",
        "status": "processing",
        "currency": "EUR",
        "total": "29.99",
        "billing": {
            "first_name": "",
            "last_name": "",
            "email": "gast@gast.de",
            "phone": ""
        },
        "shipping": {"city": ""},
        "line_items": [{"name": "Artikel", "quantity": 1, "price": "29.99"}],
        "shipping_lines": [{"method_title": "Standard"}],
        "payment_method_title": "Banküberweisung"
    }
    
    guest_info = handler.extract_order_info(guest_order)
    
    guest_pass = (
        guest_info['customer_name'] == 'Gast' and
        guest_info['customer_email'] == 'gast@gast.de'
    )
    print(f"   Name: {guest_info['customer_name']} (Expected: Gast)")
    print(f"   Status: {'✅ PASS' if guest_pass else '❌ FAIL'}")
    print()
    
    # Summary
    results = [test1_pass, priority_pass, format_pass, guest_pass]
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Test Summary: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Skill is ready for production.")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
