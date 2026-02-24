#!/usr/bin/env python3
"""
Email Template Sender
Quick email templates with placeholders for follow-ups, offers, and responses.
Uses Gmail SMTP.
"""

import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

TEMPLATES_DIR = os.path.expanduser("~/.openclaw/workspace/skills/stream2/2025-02-24-1832-email-templates")
TEMPLATES_FILE = os.path.join(TEMPLATES_DIR, "templates.json")
HISTORY_FILE = os.path.join(TEMPLATES_DIR, "send_history.json")

# Gmail config
GMAIL_USER = "edlmairfridolin@gmail.com"
GMAIL_APP_PASSWORD = "uwwf tlao blzj iecl"

def ensure_dir():
    """Create templates directory"""
    if not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR)

def load_templates():
    """Load email templates"""
    if os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE) as f:
            return json.load(f)
    
    # Default templates
    return {
        "followup": {
            "name": "Follow-up",
            "subject": "Nachfass: {{topic}}",
            "body": """Hallo {{name}},

ich wollte noch einmal nachfragen, ob Sie bereits Zeit hatten, sich {{topic}} anzuschauen.

Bei Fragen stehe ich Ihnen gerne zur Verfügung.

Beste Grüße
Fridolin
"""
        },
        "angebot": {
            "name": "Angebot",
            "subject": "Ihr individuelles Angebot: {{service}}",
            "body": """Hallo {{name}},

vielen Dank für Ihr Interesse an {{service}}.

Gerne unterbreite ich Ihnen folgendes Angebot:

{{angebot_details}}

Laufzeit: {{laufzeit}}
Investition: {{preis}} EUR

Bei Fragen melden Sie sich gerne.

Mit freundlichen Grüßen
Fridolin
--
Navii Automation
"""
        },
        "danke": {
            "name": "Dankeschön",
            "subject": "Danke für das Gespräch",
            "body": """Hallo {{name}},

vielen Dank für das nette Gespräch heute.

Wie besprochen sende ich Ihnen {{zusammenfassung}}.

Ich freue mich auf die Zusammenarbeit!

Beste Grüße
Fridolin
"""
        },
        "termin": {
            "name": "Terminbestätigung",
            "subject": "Terminbestätigung: {{termin_datum}}",
            "body": """Hallo {{name}},

ich bestätige hiermit unseren Termin:

Datum: {{termin_datum}}
Uhrzeit: {{termin_zeit}}
Thema: {{thema}}

Link: {{call_link}}

Bis bald!

Fridolin
"""
        },
        "cold": {
            "name": "Cold Outreach",
            "subject": "Automation für {{company}}?",
            "body": """Hallo {{name}},

ich schreibe Ihnen, weil ich gesehen habe, dass {{company}} {{trigger}}.

Vielleicht können wir Ihnen helfen, {{benefit}}.

Haben Sie 15 Minuten für ein kurzes Gespräch?

Beste Grüße
Fridolin
Navii Automation
"""
        }
    }

def save_templates(templates):
    """Save templates"""
    with open(TEMPLATES_FILE, 'w') as f:
        json.dump(templates, f, indent=2)

def load_history():
    """Load send history"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return {"sends": []}

def save_history(history):
    """Save send history"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def fill_template(template_text, **kwargs):
    """Fill template placeholders"""
    result = template_text
    for key, value in kwargs.items():
        placeholder = "{{" + key + "}}"
        result = result.replace(placeholder, str(value))
    return result

def send_email(to_email, subject, body, template_name="custom"):
    """Send email via Gmail SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        
        server.send_message(msg)
        server.quit()
        
        # Log to history
        history = load_history()
        history['sends'].append({
            'to': to_email,
            'subject': subject,
            'template': template_name,
            'sent_at': datetime.now().isoformat()
        })
        save_history(history)
        
        return True
        
    except Exception as e:
        print(f"❌ Send error: {e}")
        return False

def list_templates():
    """List available templates"""
    templates = load_templates()
    
    print("\n📧 Email Templates\n")
    for key, template in templates.items():
        print(f"  {key}: {template['name']}")
        print(f"       Subject: {template['subject']}")
        print()

def show_template(name):
    """Show template details"""
    templates = load_templates()
    
    if name not in templates:
        print(f"❌ Template '{name}' not found")
        return
    
    template = templates[name]
    print(f"\n📧 {template['name']}\n")
    print(f"Subject: {template['subject']}")
    print(f"\nBody:\n{template['body']}")
    
    # Extract placeholders
    import re
    placeholders = re.findall(r'\{\{(\w+)\}\}', template['subject'] + template['body'])
    if placeholders:
        print(f"\nPlaceholders: {', '.join(set(placeholders))}")

def send_template(template_name, to_email, **kwargs):
    """Send using template"""
    templates = load_templates()
    
    if template_name not in templates:
        print(f"❌ Template '{template_name}' not found")
        return False
    
    template = templates[template_name]
    
    # Fill placeholders
    subject = fill_template(template['subject'], **kwargs)
    body = fill_template(template['body'], **kwargs)
    
    print(f"\n📧 Sending: {template['name']}")
    print(f"   To: {to_email}")
    print(f"   Subject: {subject}")
    
    if send_email(to_email, subject, body, template_name):
        print(f"✅ Sent!")
        return True
    return False

def interactive_send():
    """Interactive template sender"""
    templates = load_templates()
    
    print("\n📧 Email Template Sender\n")
    
    # List templates
    print("Templates:")
    for key, template in templates.items():
        print(f"  - {key}: {template['name']}")
    
    # Select template
    template_key = input("\nTemplate: ").strip()
    if template_key not in templates:
        print("❌ Invalid template")
        return
    
    # Get email
    to_email = input("To email: ").strip()
    
    # Get placeholders
    template = templates[template_key]
    import re
    placeholders = re.findall(r'\{\{(\w+)\}\}', template['subject'] + template['body'])
    
    print(f"\nFill placeholders:")
    values = {}
    for ph in set(placeholders):
        values[ph] = input(f"  {ph}: ").strip()
    
    # Confirm
    subject = fill_template(template['subject'], **values)
    print(f"\nSubject: {subject}")
    print(f"Send? (y/n): ", end="")
    
    if input().lower() == 'y':
        send_template(template_key, to_email, **values)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Email Template Sender')
    parser.add_argument('action', choices=['list', 'show', 'send', 'interactive'],
                       help='Action')
    parser.add_argument('--template', '-t', help='Template name')
    parser.add_argument('--to', help='Recipient email')
    parser.add_argument('--vars', '-v', help='Variables as JSON', default='{}')
    
    args = parser.parse_args()
    
    ensure_dir()
    
    if args.action == 'list':
        list_templates()
    elif args.action == 'show':
        if args.template:
            show_template(args.template)
        else:
            print("Usage: email_templates.py show --template followup")
    elif args.action == 'send':
        if args.template and args.to:
            vars_dict = json.loads(args.vars)
            send_template(args.template, args.to, **vars_dict)
        else:
            print("Usage: email_templates.py send --template followup --to email@example.com --vars '{\"name\":\"Max\"}'")
    elif args.action == 'interactive':
        interactive_send()
    else:
        print("🚀 Email Template Sender")
        print("\nUsage:")
        print("  list        - List templates")
        print("  show        - Show template details")
        print("  send        - Send using template")
        print("  interactive - Interactive mode")
