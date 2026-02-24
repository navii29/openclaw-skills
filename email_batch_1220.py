#!/usr/bin/env python3
import imaplib
import ssl
import email
from email.header import decode_header
import re

EMAIL = 'edlmairfridolin@gmail.com'
APP_PASSWORD = 'uwwf tlao blzj iecl'

def decode_hdr(h):
    if not h: return ""
    try:
        d, c = decode_header(h)[0]
        return d.decode(c or 'utf-8', errors='ignore') if isinstance(d, bytes) else d
    except: return str(h)

ctx = ssl.create_default_context()
m = imaplib.IMAP4_SSL('imap.gmail.com', ssl_context=ctx)
m.login(EMAIL, APP_PASSWORD)
m.select('inbox')

_, msgs = m.search(None, 'UNSEEN')
all_ids = msgs[0].split()
total_remaining = len(all_ids)
print(f"TOTAL UNREAD: {total_remaining}")

# Process next 300 emails
ids = all_ids[-300:] if len(all_ids) >= 300 else all_ids
high = []
med = []
low = []
spam = 0

spam_keywords = ['newsletter', 'unsubscribe', 'noreply', 'no-reply', 'marketing', 'promotions', 'notifications@', 'info@', 'team@']
urgent_keywords = ['urgent', 'asap', 'immediately', 'deadline', 'due', 'action required', 'response needed', 'please reply', 'payment failed', 'verify']
action_keywords = ['please review', 'need your input', 'confirm', 'approve', 'respond by', 'meeting', 'zoom', 'calendar', 'invitation']
business_keywords = ['project', 'proposal', 'collaboration', 'inquiry', 'quote', 'invoice', 'payment', 'subscription']

for eid in reversed(ids):
    try:
        _, data = m.fetch(eid, '(RFC822)')
        raw = data[0][1]
        msg = email.message_from_bytes(raw)
        
        subj = decode_hdr(msg['Subject']) or "(No Subject)"
        sender = decode_hdr(msg['From']) or "Unknown"
        sender_clean = re.sub(r'<[^>]+>', '', sender).strip()[:35]
        
        s_low = subj.lower()
        snd_low = sender.lower()
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')[:400].lower()
                        break
                    except: pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')[:400].lower()
            except: pass
        
        combined = s_low + " " + body
        
        is_spam = any(k in snd_low or k in s_low for k in spam_keywords)
        is_urgent = any(k in combined for k in urgent_keywords)
        is_action = any(k in combined for k in action_keywords)
        is_business = any(k in combined for k in business_keywords)
        
        if is_spam:
            spam += 1
            m.store(eid, '+FLAGS', '\\Seen')
        elif is_urgent:
            tldr = subj[:50]
            action = "⚠️ URGENT: " + ("Payment issue" if "payment" in combined else "Action required")
            high.append({'sender': sender_clean, 'subj': tldr, 'action': action})
            m.store(eid, '+FLAGS', '\\Seen')
        elif is_action:
            tldr = subj[:50]
            action = "📅 Meeting/Response needed"
            high.append({'sender': sender_clean, 'subj': tldr, 'action': action})
            m.store(eid, '+FLAGS', '\\Seen')
        elif is_business:
            med.append({'sender': sender_clean, 'subj': subj[:45]})
            m.store(eid, '+FLAGS', '\\Seen')
        else:
            low.append({'sender': sender_clean, 'subj': subj[:40]})
            m.store(eid, '+FLAGS', '\\Seen')
    except Exception as e:
        pass

m.close()
m.logout()

print(f"\nBATCH PROCESSED: {len(ids)} emails")
print(f"HIGH: {len(high)}")
print(f"MEDIUM: {len(med)}")
print(f"LOW: {len(low)}")
print(f"SPAM: {spam}")

if high:
    print("\n=== HIGH PRIORITY ===")
    for i, h in enumerate(high[:10], 1):
        print(f"{i}. {h['sender']}: {h['subj']}")
        print(f"   → {h['action']}")

if med:
    print("\n=== MEDIUM ===")
    for m in med[:5]:
        print(f"  {m['sender']}: {m['subj']}")

remaining = total_remaining - len(ids)
print(f"\n=== REMAINING: {remaining} emails ===")

# Output for parsing
import json
print("\n" + "="*50)
print(json.dumps({
    'total_remaining': total_remaining,
    'processed': len(ids),
    'high_count': len(high),
    'med_count': len(med),
    'low_count': len(low),
    'spam_count': spam,
    'remaining': remaining,
    'high_items': high[:10],
    'med_items': med[:5]
}))
