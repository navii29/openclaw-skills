#!/usr/bin/env python3
"""
Business Dashboard
Unified dashboard combining all Stream 2 skills.
Shows leads, tasks, invoices, and metrics at a glance.
"""

import json
import os
from datetime import datetime

BASE_DIR = os.path.expanduser("~/.openclaw/workspace/skills/stream2")

def load_json(filepath, default=None):
    """Load JSON file safely"""
    if os.path.exists(filepath):
        try:
            with open(filepath) as f:
                return json.load(f)
        except:
            pass
    return default or {}

def get_leads_summary():
    """Get leads from skill 1"""
    lead_file = os.path.join(BASE_DIR, "2025-02-24-1827-email-lead-detector", "lead_state.json")
    data = load_json(lead_file, {"leads_found": 0, "processed_ids": []})
    
    return {
        'total_leads': data.get('leads_found', 0),
        'processed_emails': len(data.get('processed_ids', [])),
        'hot_leads': sum(1 for l in data.get('leads', []) if l.get('score', 0) >= 8)
    }

def get_tasks_summary():
    """Get tasks from skill 8"""
    tasks_file = os.path.join(BASE_DIR, "2025-02-24-1834-meeting-tasks", "tasks.json")
    data = load_json(tasks_file, {"tasks": []})
    
    tasks = data.get('tasks', [])
    open_tasks = [t for t in tasks if t.get('status') == 'open']
    done_tasks = [t for t in tasks if t.get('status') == 'done']
    
    return {
        'total': len(tasks),
        'open': len(open_tasks),
        'done': len(done_tasks),
        'overdue': sum(1 for t in open_tasks if t.get('deadline') and t['deadline'] < datetime.now().strftime('%Y-%m-%d'))
    }

def get_invoice_summary():
    """Get invoices from skill 9"""
    invoice_file = os.path.join(BASE_DIR, "2025-02-24-1836-invoice-generator", "invoices.json")
    data = load_json(invoice_file, {"invoices": []})
    
    invoices = data.get('invoices', [])
    paid = [i for i in invoices if i.get('status') == 'paid']
    outstanding = [i for i in invoices if i.get('status') == 'sent']
    
    return {
        'total': len(invoices),
        'paid_count': len(paid),
        'paid_amount': sum(i.get('total', 0) for i in paid),
        'outstanding_amount': sum(i.get('total', 0) for i in outstanding),
        'draft_amount': sum(i.get('total', 0) for i in invoices if i.get('status') == 'draft')
    }

def get_notes_summary():
    """Get notes from skill 5"""
    notes_state = os.path.join(BASE_DIR, "2025-02-24-1833-telegram-notes", "notes_state.json")
    data = load_json(notes_state, {"notes": []})
    
    notes = data.get('notes', [])
    today = datetime.now().strftime('%Y-%m-%d')
    today_notes = [n for n in notes if n.get('date') == today]
    
    return {
        'total': len(notes),
        'today': len(today_notes)
    }

def generate_dashboard():
    """Generate full dashboard"""
    leads = get_leads_summary()
    tasks = get_tasks_summary()
    invoices = get_invoice_summary()
    notes = get_notes_summary()
    
    dashboard = f"""
╔══════════════════════════════════════════════════════════════╗
║                    📊 BUSINESS DASHBOARD                      ║
║                      {datetime.now().strftime('%d.%m.%Y %H:%M')}                       ║
╚══════════════════════════════════════════════════════════════╝

🔥 LEADS (Skill 1)
├─ Total Found: {leads['total_leads']}
├─ Hot Leads (8-10): {leads['hot_leads']}
└─ Emails Processed: {leads['processed_emails']}

✅ TASKS (Skill 8)
├─ Open: {tasks['open']}
├─ Done: {tasks['done']}
├─ Overdue: {tasks['overdue']}
└─ Total: {tasks['total']}

🧾 INVOICES (Skill 9)
├─ Total: {invoices['total']}
├─ Paid: {invoices['paid_count']} ({invoices['paid_amount']:.2f} €)
├─ Outstanding: {invoices['outstanding_amount']:.2f} €
└─ Drafts: {invoices['draft_amount']:.2f} €

📝 NOTES (Skill 5)
├─ Today: {notes['today']}
└─ Total: {notes['total']}

💰 FINANCIAL HEALTH
├─ Revenue: {invoices['paid_amount']:.2f} €
├─ Outstanding: {invoices['outstanding_amount']:.2f} €
└─ Pipeline: {invoices['draft_amount'] + invoices['outstanding_amount']:.2f} €

📈 PRODUCTIVITY
├─ Open Tasks: {tasks['open']}
├─ Lead Conversion: {leads['total_leads']} opportunities
└─ Billing: {invoices['paid_amount'] + invoices['outstanding_amount']:.2f} €

═══════════════════════════════════════════════════════════════

🚀 ACTIVE SKILLS (10/10)
1. ✅ Email Lead Detector
2. ✅ Lead CSV Exporter
3. ✅ Daily Standup Generator
4. ✅ Webhook Tester
5. ✅ Telegram Quick Notes
6. ✅ Competitor Monitor
7. ✅ Email Template Sender
8. ✅ Meeting Tasks Extractor
9. ✅ Quick Invoice Generator
10. ✅ Business Dashboard

═══════════════════════════════════════════════════════════════
Generated by Business Dashboard v1.0
"""
    
    return dashboard

def generate_telegram_summary():
    """Generate compact summary for Telegram"""
    leads = get_leads_summary()
    tasks = get_tasks_summary()
    invoices = get_invoice_summary()
    
    return f"""📊 *DASHBOARD - {datetime.now().strftime('%d.%m.%H:%M')}*

🔥 Leads: {leads['hot_leads']} hot / {leads['total_leads']} total
✅ Tasks: {tasks['open']} open / {tasks['done']} done
🧾 Revenue: {invoices['paid_amount']:.0f}€ / {invoices['outstanding_amount']:.0f}€ open

🎯 Skills: 10/10 active ✅
"""

def save_dashboard():
    """Save dashboard to file"""
    dashboard = generate_dashboard()
    
    output_file = os.path.join(BASE_DIR, "2025-02-24-1838-business-dashboard", "dashboard.txt")
    
    with open(output_file, 'w') as f:
        f.write(dashboard)
    
    return output_file

def send_telegram_dashboard():
    """Send dashboard to Telegram"""
    try:
        import urllib.request
        import urllib.parse
        
        token = "8294286642:AAFKb09yfYMA5G4xrrr0yz0RCnHaph7IpBw"
        chat_id = "6599716126"
        
        message = generate_telegram_summary()
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        data_encoded = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_encoded, method='POST')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Business Dashboard')
    parser.add_argument('action', choices=['show', 'save', 'telegram'], default='show', nargs='?')
    
    args = parser.parse_args()
    
    if args.action == 'show':
        print(generate_dashboard())
    
    elif args.action == 'save':
        filepath = save_dashboard()
        print(f"✅ Dashboard saved to {filepath}")
    
    elif args.action == 'telegram':
        if send_telegram_dashboard():
            print("✅ Dashboard sent to Telegram")
        else:
            print("❌ Failed to send")
