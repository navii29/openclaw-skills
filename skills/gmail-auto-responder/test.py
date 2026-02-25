#!/usr/bin/env python3
"""Test Gmail Auto-Responder"""

import sys
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace/skills/gmail-auto-responder')

from gmail_responder import GmailAutoResponder

def run_tests():
    """Test classification without real email connection."""
    print("🧪 Testing Gmail Auto-Responder...\n")
    
    # Create instance (won't connect yet)
    responder = GmailAutoResponder("test@test.de", "fake-password")
    
    # Test classifications
    test_cases = [
        {
            'name': 'Rechnungserkennung',
            'subject': 'Rechnung für Bestellung #12345',
            'body': 'Sehr geehrte Damen und Herren, anbei finden Sie die Rechnung für Ihre Zahlung. Bitte überweisen Sie den Betrag innerhalb von 14 Tagen.',
            'expected': 'rechnung'
        },
        {
            'name': 'Angebotsanfrage',
            'subject': 'Angebot für Webdesign-Projekt',
            'body': 'Hallo, wir benötigen ein Kostenvoranschlag für unsere neue Website. Was würde das kosten?',
            'expected': 'angebot'
        },
        {
            'name': 'Support-Anfrage',
            'subject': 'Problem mit Login',
            'body': 'Hilfe! Ich kann mich nicht mehr einloggen. Es erscheint immer ein Fehler.',
            'expected': 'support'
        },
        {
            'name': 'Terminvereinbarung',
            'subject': 'Besprechung nächste Woche',
            'body': 'Können wir einen Call für Donnerstag vereinbaren? Oder ein Zoom Meeting?',
            'expected': 'termin'
        },
        {
            'name': 'Bewerbung',
            'subject': 'Bewerbung als Marketing Manager',
            'body': 'Sehr geehrte Damen und Herren, hiermit bewerbe ich mich um die ausgeschriebene Stelle. Anbei finden Sie meinen Lebenslauf.',
            'expected': 'bewerbung'
        },
        {
            'name': 'Marketing/Spam',
            'subject': 'Super Rabatt Aktion! 50% OFF',
            'body': 'Melden Sie sich für unseren Newsletter an und erhalten Sie tolle Angebote! Unsubscribe hier.',
            'expected': 'marketing'
        }
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        category, confidence = responder.classify_email(
            test['subject'],
            test['body'],
            'test@sender.de'
        )
        
        success = category == test['expected']
        status = "✅" if success else "❌"
        
        print(f"{status} {test['name']}")
        print(f"   Expected: {test['expected']}")
        print(f"   Got: {category} (confidence: {confidence})")
        print()
        
        if success:
            passed += 1
        else:
            failed += 1
    
    # Test templates exist
    print("📝 Testing reply templates...")
    for category in ['rechnung', 'angebot', 'support', 'termin', 'bewerbung']:
        has_template = category in responder.TEMPLATES
        status = "✅" if has_template else "❌"
        print(f"  {status} Template for {category}: {'Found' if has_template else 'Missing'}")
        if has_template:
            passed += 1
        else:
            failed += 1
    
    print()
    print(f"📊 Test Summary: {passed}/{passed+failed} passed")
    
    if failed == 0:
        print("🎉 All tests passed! Skill is ready for production.")
        return True
    else:
        print(f"⚠️ {failed} tests failed.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
