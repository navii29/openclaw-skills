#!/usr/bin/env python3
import imaplib
import ssl
import email
from email.header import decode_header
import re
from datetime import datetime

EMAIL = 'edlmairfridolin@gmail.com'
APP_PASSWORD = 'uwwf tlao blzj iecl'

def decode_hdr(h):
    if not h: return ''
    try:
        d, c = decode_header(h)[0]
        return d.decode(c or 'utf-8', errors='ignore') if isinstance(d, bytes) else d
    except: return str(h)

def extract_deadline(subject, body):
    """Extract deadline from subject/body"""
    text = (subject + ' ' + body).lower()
    
    # Date patterns
    date_patterns = [
        r'\b(\d{1,2}[./]\d{1,2}[./]\d{2,4})\b',
        r'\b(by|until|before|due)\s+(\w+\s+\d{1,2})\b',
        r'\b(deadline|frist)\s*:?\s*(\w+[^\n,]{0,20})',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)[:30]
    return None

# Connect
ctx = ssl.create_default_context()
m = imaplib.IMAP4_SSL('imap.gmail.com', ssl_context=ctx)
m.login(EMAIL, APP_PASSWORD)
m.select('inbox')

# Get unread
_, msgs = m.search(None, 'UNSEEN')
all_ids = msgs[0].split()
total_unread = len(all_ids)

print(f'TOTAL UNREAD: {total_unread}')

if total_unread == 0:
    print('✅ No new emails')
    m.logout()
    exit(0)

# Process max 100 newest
ids = all_ids[-100:] if len(all_ids) >= 100 else all_ids

action_required = []
review = []
read_later = []
spam_count = 0
sender_stats = {}
deadlines = []

# Keywords
payment_keywords = ['payment', 'zahlung', 'failed', 'declined', 'expired', 'invoice', 'rechnung', 'billing']
urgent_keywords = ['urgent', 'asap', 'deadline', 'frist', 'action required', 'sofort', 'dringend']
business_keywords = ['meeting', 'project', 'proposal', 'collaboration', 'inquiry', 'angebot', 'zoom', 'calendar']
spam_keywords = ['newsletter', 'unsubscribe', 'noreply', 'no-reply', 'marketing', 'promotions', 'notifications@']

for eid in reversed(ids):
    try:
        # Fetch headers first (fast)
        _, data = m.fetch(eid, '(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])')
        raw = data[0][1]
        msg = email.message_from_bytes(raw)
        
        subj = decode_hdr(msg['Subject']) or '(No Subject)'
        sender = decode_hdr(msg['From']) or 'Unknown'
        date = decode_hdr(msg['Date']) or ''
        
        # Clean sender
        sender_clean = re.sub(r'<[^>]+>', '', sender).strip()[:30]
        sender_email = re.search(r'<([^>]+)>', sender)
        sender_domain = sender_email.group(1).split('@')[1] if sender_email else sender_clean[:20]
        
        # Update sender stats
        sender_key = sender_clean[:25]
        sender_stats[sender_key] = sender_stats.get(sender_key, 0) + 1
        
        s_low = subj.lower()
        snd_low = sender.lower()
        
        # Quick spam check (no body needed)
        is_spam = any(k in snd_low or k in s_low for k in spam_keywords)
        if is_spam:
            spam_count += 1
            m.store(eid, '+FLAGS', '\\Seen')
            continue
        
        # Fetch body only if potentially important
        needs_body = any(k in s_low for k in payment_keywords + urgent_keywords + business_keywords)
        
        body = ''
        if needs_body:
            _, body_data = m.fetch(eid, '(BODY.PEEK[TEXT])')
            if body_data[0]:
                try:
                    body = body_data[0][1].decode('utf-8', errors='ignore')[:500].lower()
                except: pass
        
        combined = s_low + ' ' + body
        
        # Check for payment issues (HIGHEST priority)
        is_payment = any(k in combined for k in payment_keywords)
        is_urgent = any(k in combined for k in urgent_keywords)
        is_business = any(k in combined for k in business_keywords)
        
        # Extract deadline if present
        deadline = extract_deadline(subj, body) if (is_urgent or is_payment) else None
        
        if is_payment or is_urgent:
            action_type = '💳 Payment' if is_payment else '⚠️ Urgent'
            action_required.append({
                'sender': sender_key,
                'subj': subj[:40],
                'type': action_type,
                'deadline': deadline
            })
            if deadline:
                deadlines.append({
                    'sender': sender_key,
                    'subj': subj[:35],
                    'deadline': deadline
                })
            # Label: Action-Required (mark seen for now)
            m.store(eid, '+FLAGS', '\\Seen')
            
        elif is_business:
            review.append({
                'sender': sender_key,
                'subj': subj[:40]
            })
            # Label: Review
            m.store(eid, '+FLAGS', '\\Seen')
            
        else:
            read_later.append({
                'sender': sender_key,
                'subj': subj[:35]
            })
            # Label: Read-Later
            m.store(eid, '+FLAGS', '\\Seen')
            
    except Exception as e:
        print(f'Error processing email: {e}')

m.close()
m.logout()

# Output results
print(f'\n=== PROCESSED: {len(ids)} emails ===')
print(f'🔴 Action-Required: {len(action_required)}')
print(f'🟡 Review: {len(review)}')
print(f'🟢 Read-Later: {len(read_later)}')
print(f'🗑️ Spam: {spam_count}')
print(f'📥 Remaining: {total_unread - len(ids)}')

if deadlines:
    print('\n⏰ DEADLINES FOUND:')
    for d in deadlines[:5]:
        print(f"  • {d['sender']}: {d['subj']} ({d['deadline']})")

if action_required:
    print('\n🔴 ACTION REQUIRED:')
    for i, a in enumerate(action_required[:10], 1):
        dl = f" [{a['deadline']}]" if a['deadline'] else ''
        print(f"{i}. {a['type']} | {a['sender']}: {a['subj']}{dl}")

if review:
    print('\n🟡 REVIEW (Business):')
    for r in review[:5]:
        print(f"  • {r['sender']}: {r['subj']}")

# Top 5 senders
print('\n📊 TOP SENDERS:')
sorted_senders = sorted(sender_stats.items(), key=lambda x: x[1], reverse=True)[:5]
for sender, count in sorted_senders:
    print(f"  • {sender}: {count} ungelesen")

print('\n=== SUMMARY ===')
print(f'Total: {len(ids)} | Action: {len(action_required)} | Review: {len(review)} | Later: {len(read_later)} | Spam: {spam_count}')
print(f'Remaining in queue: {total_unread - len(ids)}')
