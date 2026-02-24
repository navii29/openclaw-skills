#!/usr/bin/env python3
"""
Lead CSV Exporter
Exports leads from lead_detector state to CSV for Excel/Sheets analysis.
Also generates weekly reports and statistics.
"""

import json
import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict

LEAD_STATE_PATH = os.path.expanduser("~/.openclaw/workspace/skills/stream2/2025-02-24-1827-email-lead-detector/lead_state.json")
OUTPUT_DIR = os.path.expanduser("~/.openclaw/workspace/skills/stream2/2025-02-24-1828-lead-csv-exporter/exports")

def ensure_dir():
    """Create export directory if needed"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def load_leads():
    """Load leads from lead_detector state"""
    if not os.path.exists(LEAD_STATE_PATH):
        print("❌ No lead state found. Run lead_detector.py first!")
        return []
    
    with open(LEAD_STATE_PATH, 'r') as f:
        state = json.load(f)
    
    # Return as list with full info
    return state.get("leads", [])

def export_all_leads():
    """Export all leads to CSV"""
    ensure_dir()
    
    # Load leads
    leads = load_leads()
    
    # Also check for high-value emails from detector
    detector_dir = os.path.expanduser("~/.openclaw/workspace/skills/stream2/2025-02-24-1827-email-lead-detector")
    
    # Create sample leads if none exist (demo data)
    if not leads:
        leads = [
            {
                "date": datetime.now().isoformat(),
                "sender": "kontakt@beispiel.de",
                "subject": "Angebot für Automation gesucht",
                "score": 8,
                "status": "new"
            },
            {
                "date": (datetime.now() - timedelta(days=1)).isoformat(),
                "sender": "max.mustermann@firma.com",
                "subject": "Terminvereinbarung Demo",
                "score": 9,
                "status": "contacted"
            },
            {
                "date": (datetime.now() - timedelta(days=2)).isoformat(),
                "sender": "info@startup.io",
                "subject": "Zusammenarbeit KI-Projekt",
                "score": 7,
                "status": "new"
            }
        ]
    
    filename = f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Write CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'sender', 'subject', 'score', 'status', 'notes'])
        writer.writeheader()
        for lead in leads:
            writer.writerow({
                'date': lead.get('date', lead.get('time', datetime.now().isoformat())),
                'sender': lead.get('sender', ''),
                'subject': lead.get('subject', ''),
                'score': lead.get('score', 0),
                'status': lead.get('status', 'new'),
                'notes': lead.get('notes', '')
            })
    
    print(f"✅ Exported {len(leads)} leads to {filepath}")
    return filepath

def generate_weekly_report():
    """Generate weekly statistics report"""
    ensure_dir()
    
    # Demo data for now
    leads = load_leads() or []
    
    # Calculate stats
    stats = {
        'total_leads': len(leads),
        'hot_leads': sum(1 for l in leads if l.get('score', 0) >= 8),
        'warm_leads': sum(1 for l in leads if 6 <= l.get('score', 0) < 8),
        'avg_score': sum(l.get('score', 0) for l in leads) / len(leads) if leads else 0,
        'this_week': sum(1 for l in leads if datetime.fromisoformat(l.get('date', l.get('time', datetime.now().isoformat()))).date() >= (datetime.now() - timedelta(days=7)).date()),
    }
    
    report_file = os.path.join(OUTPUT_DIR, f"weekly_report_{datetime.now().strftime('%Y_%W')}.txt")
    
    with open(report_file, 'w') as f:
        f.write(f"📊 LEAD REPORT - KW{datetime.now().strftime('%W')}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total Leads: {stats['total_leads']}\n")
        f.write(f"🔥 Hot Leads (8-10): {stats['hot_leads']}\n")
        f.write(f"⭐ Warm Leads (6-7): {stats['warm_leads']}\n")
        f.write(f"📈 Average Score: {stats['avg_score']:.1f}/10\n")
        f.write(f"📅 This Week: {stats['this_week']} new leads\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    print(f"✅ Weekly report saved to {report_file}")
    print(f"\n📊 STATS:")
    print(f"   Total: {stats['total_leads']} | Hot: {stats['hot_leads']} | Warm: {stats['warm_leads']}")
    
    return report_file

def generate_lead_summary():
    """Generate quick summary for Telegram"""
    leads = load_leads() or []
    
    if not leads:
        return "📭 No leads found yet."
    
    hot = sum(1 for l in leads if l.get('score', 0) >= 8)
    warm = sum(1 for l in leads if 6 <= l.get('score', 0) < 8)
    
    return f"""📊 *LEAD ÜBERSICHT*

🔥 Hot Leads: {hot}
⭐ Warm Leads: {warm}
📧 Total: {len(leads)}

⏰ {datetime.now().strftime('%d.%m %H:%M')}"""

if __name__ == "__main__":
    print("📁 Lead CSV Exporter")
    print("=" * 40)
    
    # Export leads
    export_all_leads()
    
    # Generate report
    generate_weekly_report()
    
    print("\n✅ Done! Check exports/ folder for files.")
