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
ids = msgs[0].split()
print(f"TOTAL UNREAD: {len(ids)}")

# Sample last 50
ids = ids[-50:]
high = []
med = []
low = []
spam = 0

spam_keywords = ['newsletter', 'unsubscribe', 'noreply', 'marketing', 'promotions']
urgent_keywords = ['urgent', 'asap', 'deadline', 'due', 'action required', 'meeting']

for eid in reversed(ids):
    try:
        _, data = m.fetch(eid, '(RFC822)')
        raw = data[0][1]
        msg = email.message_from_bytes(raw)
        
        subj = decode_hdr(msg['Subject']) or "(No Subject)"
        sender = decode_hdr(msg['From']) or "Unknown"
        sender_clean = re.sub(r'<[^>]+>', '', sender).strip()[:30]
        
        s_low = subj.lower()
        snd_low = sender.lower()
        
        is_spam = any(k in snd_low or k in s_low for k in spam_keywords)
        is_urgent = any(k in s_low for k in urgent_keywords)
        
        if is_spam:
            spam += 1
            m.store(eid, '+FLAGS', '\\Seen')
        elif is_urgent or 're:' in s_low or 'fw:' in s_low:
            high.append({'sender': sender_clean, 'subj': subj[:45]})
            m.store(eid, '+FLAGS', '\\Seen')
        elif any(k in s_low for k in ['invitation', 'calendar', 'project', 'proposal']):
            med.append({'sender': sender_clean, 'subj': subj[:45]})
            m.store(eid, '+FLAGS', '\\Seen')
        else:
            low.append({'sender': sender_clean, 'subj': subj[:45]})
            m.store(eid, '+FLAGS', '\\Seen')
    except:
        pass

m.close()
m.logout()

print(f"HIGH: {len(high)}")
print(f"MEDIUM: {len(med)}")
print(f"LOW: {len(low)}")
print(f"SPAM: {spam}")
print("\nTOP HIGH PRIORITY:")
for h in high[:5]:
    print(f"  - {h['sender']}: {h['subj']}")
