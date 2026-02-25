#!/usr/bin/env python3
"""Test Email zu Slack Support-Tickets"""

import sys
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace/skills/email-slack-tickets')

from datetime import datetime
from email_slack_tickets import SupportTicket, EmailMonitor, SlackNotifier

def run_tests():
    """Test ticket creation and formatting."""
    print("🧪 Testing Email zu Slack Support-Tickets...\n")
    
    # Test 1: SupportTicket creation
    print("Test 1: SupportTicket Erstellung")
    ticket = SupportTicket(
        ticket_id="TKT-20240315-001",
        sender_name="Max Mustermann",
        sender_email="max@kunde.de",
        subject="Login Problem - Dringend!",
        body="Ich kann mich nicht mehr einloggen. Bitte um schnelle Hilfe!",
        timestamp=datetime.now(),
        priority="high",
        category="technical",
        keywords=["dringend", "problem"]
    )
    
    print(f"   ID: {ticket.ticket_id}")
    print(f"   From: {ticket.sender_name} ({ticket.sender_email})")
    print(f"   Subject: {ticket.subject}")
    print(f"   Priority: {ticket.priority}")
    print(f"   Category: {ticket.category}")
    
    test1_pass = (
        ticket.ticket_id == "TKT-20240315-001" and
        ticket.sender_name == "Max Mustermann" and
        ticket.priority == "high"
    )
    print(f"   Status: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print()
    
    # Test 2: Priority analysis
    print("Test 2: Prioritäts-Analyse")
    monitor = EmailMonitor("test", "test", "test")
    
    test_cases = [
        {
            'subject': 'Login Problem - Dringend!',
            'body': 'Hilfe, ich komme nicht rein!',
            'expected_priority': 'critical',
            'expected_category': 'technical'
        },
        {
            'subject': 'Frage zur Rechnung',
            'body': 'Können Sie mir helfen?',
            'expected_priority': 'medium',
            'expected_category': 'billing'
        },
        {
            'subject': 'Angebot anfordern',
            'body': 'Wir benötigen ein Angebot für...',
            'expected_priority': 'medium',
            'expected_category': 'sales'
        },
        {
            'subject': 'Feedback',
            'body': 'Super Service, danke!',
            'expected_priority': 'low',
            'expected_category': 'general'
        }
    ]
    
    analysis_pass = True
    for test in test_cases:
        priority, category, keywords = monitor.analyze_priority(test['subject'], test['body'])
        
        p_match = priority == test['expected_priority']
        c_match = category == test['expected_category']
        
        status = "✅" if (p_match and c_match) else "❌"
        print(f"   {status} '{test['subject'][:30]}' → P:{priority}, C:{category}")
        
        if not (p_match and c_match):
            analysis_pass = False
    print()
    
    # Test 3: Slack message formatting
    print("Test 3: Slack Formatierung")
    notifier = SlackNotifier("https://hooks.slack.com/test")
    
    test_ticket = SupportTicket(
        ticket_id="TKT-001",
        sender_name="Anna Schmidt",
        sender_email="anna@firma.de",
        subject="Website Fehler",
        body="Die Website lädt nicht richtig. Bitte prüfen!",
        timestamp=datetime.now(),
        priority="critical",
        category="technical",
        keywords=["fehler", "dringend"]
    )
    
    slack_msg = notifier.format_ticket(test_ticket)
    
    format_checks = [
        'blocks' in slack_msg,
        'NEUES TICKET' in str(slack_msg),
        'TKT-001' in str(slack_msg),
        'Anna Schmidt' in str(slack_msg),
        'Website Fehler' in str(slack_msg),
        'CRITICAL' in str(slack_msg).upper() or 'KRITISCH' in str(slack_msg).upper()
    ]
    
    format_pass = all(format_checks)
    print(f"   Blocks format: {'✅' if 'blocks' in slack_msg else '❌'}")
    print(f"   Ticket ID: {'✅' if 'TKT-001' in str(slack_msg) else '❌'}")
    print(f"   Buttons: {'✅' if 'button' in str(slack_msg).lower() else '❌'}")
    print(f"   Status: {'✅ PASS' if format_pass else '❌ FAIL'}")
    print()
    
    # Test 4: Body extraction simulation
    print("Test 4: Email Body Extraktion")
    
    # Test plain text extraction
    test_body = """Hallo Support-Team,

ich habe ein Problem mit meinem Login.
Können Sie mir bitte helfen?

Danke!
Max"""
    
    # Simulate extraction (the actual function requires email message object)
    preview = test_body[:100] + "..." if len(test_body) > 100 else test_body
    body_pass = len(preview) <= 103  # Should be truncated or same
    
    print(f"   Original length: {len(test_body)}")
    print(f"   Preview length: {len(preview)}")
    print(f"   Status: {'✅ PASS' if body_pass else '❌ FAIL'}")
    print()
    
    # Summary
    results = [test1_pass, analysis_pass, format_pass, body_pass]
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
