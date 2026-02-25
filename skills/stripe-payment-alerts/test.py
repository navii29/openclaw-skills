#!/usr/bin/env python3
"""Test Stripe Payment Alerts"""

import sys
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace/skills/stripe-payment-alerts')

from stripe_alerts import StripeWebhookHandler, TelegramNotifier

def run_tests():
    """Test Stripe webhook handling and notifications."""
    print("🧪 Testing Stripe Payment Alerts...\n")
    
    # Test 1: Event filtering
    print("Test 1: Event-Filterung")
    handler = StripeWebhookHandler()
    
    important_events = [
        'checkout.session.completed',
        'invoice.payment_succeeded',
        'invoice.payment_failed'
    ]
    
    unimportant_events = [
        'customer.updated',
        'invoice.created',
        'charge.pending'
    ]
    
    filter_pass = True
    for event in important_events:
        result = handler.should_notify(event)
        status = "✅" if result else "❌"
        print(f"   {status} {event}: {'NOTIFY' if result else 'SKIP'}")
        if not result:
            filter_pass = False
    
    for event in unimportant_events:
        result = handler.should_notify(event)
        status = "✅" if not result else "❌"
        print(f"   {status} {event}: {'NOTIFY' if result else 'SKIP'}")
        if result:
            filter_pass = False
    print()
    
    # Test 2: Payment info extraction
    print("Test 2: Payment Info Extraktion")
    
    # Simulate checkout.session.completed
    checkout_event = {
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'id': 'cs_test_123',
                'amount_total': 9999,
                'currency': 'eur',
                'payment_status': 'paid',
                'customer_details': {
                    'name': 'Anna Schmidt',
                    'email': 'anna@firma.de'
                }
            }
        }
    }
    
    info = handler.extract_payment_info(checkout_event)
    
    print(f"   Type: {info.get('type')}")
    print(f"   Amount: {info.get('amount')} (Expected: 99.99)")
    print(f"   Customer: {info.get('customer_name')}")
    print(f"   Email: {info.get('customer_email')}")
    
    extract_pass = (
        info.get('type') == 'new_payment' and
        abs(info.get('amount', 0) - 99.99) < 0.01 and
        info.get('customer_name') == 'Anna Schmidt'
    )
    print(f"   Status: {'✅ PASS' if extract_pass else '❌ FAIL'}")
    print()
    
    # Test 3: Failed payment extraction
    print("Test 3: Failed Payment Extraktion")
    
    failed_event = {
        'type': 'invoice.payment_failed',
        'data': {
            'object': {
                'id': 'in_123',
                'amount_due': 4999,
                'currency': 'eur',
                'customer_email': 'failed@customer.de',
                'attempt_count': 2
            }
        }
    }
    
    info2 = handler.extract_payment_info(failed_event)
    
    print(f"   Type: {info2.get('type')}")
    print(f"   Amount: {info2.get('amount')} (Expected: 49.99)")
    print(f"   Attempts: {info2.get('attempt_count')}")
    
    failed_pass = (
        info2.get('type') == 'payment_failed' and
        info2.get('attempt_count') == 2
    )
    print(f"   Status: {'✅ PASS' if failed_pass else '❌ FAIL'}")
    print()
    
    # Test 4: Telegram message formatting
    print("Test 4: Telegram Formatierung")
    notifier = TelegramNotifier("fake-token", "fake-chat")
    
    test_info = {
        'emoji': '💰',
        'title': 'Neue Zahlung!',
        'amount': 99.99,
        'currency': 'EUR',
        'customer_name': 'Max Mustermann',
        'customer_email': 'max@test.de',
        'description': 'Pro Plan'
    }
    
    msg = notifier.format_message(test_info)
    
    format_checks = [
        'Neue Zahlung' in msg,
        '99.99' in msg,
        'Max Mustermann' in msg,
        'max@test.de' in msg,
        'Pro Plan' in msg,
        '<b>' in msg  # HTML tags
    ]
    
    format_pass = all(format_checks)
    print(f"   HTML Tags: {'✅' if '<b>' in msg else '❌'}")
    print(f"   Amount: {'✅' if '99.99' in msg else '❌'}")
    print(f"   Customer: {'✅' if 'Max Mustermann' in msg else '❌'}")
    print(f"   Status: {'✅ PASS' if format_pass else '❌ FAIL'}")
    print()
    
    # Summary
    results = [filter_pass, extract_pass, failed_pass, format_pass]
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
