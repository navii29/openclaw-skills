#!/usr/bin/env python3
"""
Telegram Quick Notes
Create notes via Telegram messages.
Supports categories, tags, and markdown export.
"""

import json
import os
from datetime import datetime

NOTES_DIR = os.path.expanduser("~/.openclaw/workspace/skills/stream2/2025-02-24-1833-telegram-notes/notes")
STATE_FILE = os.path.expanduser("~/.openclaw/workspace/skills/stream2/2025-02-24-1833-telegram-notes/notes_state.json")

def ensure_dirs():
    """Create note directories"""
    if not os.path.exists(NOTES_DIR):
        os.makedirs(NOTES_DIR)
    
    # Create category subdirs
    for cat in ['inbox', 'ideas', 'tasks', 'meeting', 'personal']:
        cat_dir = os.path.join(NOTES_DIR, cat)
        if not os.path.exists(cat_dir):
            os.makedirs(cat_dir)

def load_state():
    """Load notes state"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"notes": [], "total_count": 0}

def save_state(state):
    """Save notes state"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def parse_note(text):
    """Parse note text for category and tags"""
    category = 'inbox'
    tags = []
    content = text
    
    # Check for category prefix
    prefixes = {
        '#idea': 'ideas',
        '#task': 'tasks',
        '#meeting': 'meeting',
        '#personal': 'personal',
        '#inbox': 'inbox'
    }
    
    for prefix, cat in prefixes.items():
        if text.lower().startswith(prefix):
            category = cat
            content = text[len(prefix):].strip()
            break
    
    # Extract tags
    words = content.split()
    for word in words[:]:
        if word.startswith('#') and word[1:].isalnum():
            tags.append(word[1:])
            words.remove(word)
    
    content = ' '.join(words)
    
    return {
        'category': category,
        'tags': tags,
        'content': content,
        'raw': text
    }

def create_note(text, source="telegram"):
    """Create a new note"""
    ensure_dirs()
    
    parsed = parse_note(text)
    
    note = {
        'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': datetime.now().strftime('%H:%M'),
        'category': parsed['category'],
        'tags': parsed['tags'],
        'content': parsed['content'],
        'raw_text': parsed['raw'],
        'source': source
    }
    
    # Save as individual markdown file
    filename = f"{note['id']}.md"
    filepath = os.path.join(NOTES_DIR, parsed['category'], filename)
    
    with open(filepath, 'w') as f:
        f.write(f"---\n")
        f.write(f"id: {note['id']}\n")
        f.write(f"date: {note['date']}\n")
        f.write(f"time: {note['time']}\n")
        f.write(f"category: {note['category']}\n")
        f.write(f"tags: {', '.join(note['tags'])}\n")
        f.write(f"source: {note['source']}\n")
        f.write(f"---\n\n")
        f.write(f"{note['content']}\n")
    
    # Update state
    state = load_state()
    state['notes'].append(note)
    state['total_count'] += 1
    save_state(state)
    
    return note

def list_notes(category=None, limit=10):
    """List recent notes"""
    state = load_state()
    notes = state['notes']
    
    if category:
        notes = [n for n in notes if n['category'] == category]
    
    return notes[-limit:]

def search_notes(query):
    """Search notes"""
    state = load_state()
    results = []
    
    query_lower = query.lower()
    for note in state['notes']:
        if (query_lower in note['content'].lower() or 
            query_lower in ' '.join(note['tags']).lower() or
            query_lower in note['category']):
            results.append(note)
    
    return results

def generate_daily_summary():
    """Generate daily note summary"""
    today = datetime.now().strftime('%Y-%m-%d')
    state = load_state()
    
    today_notes = [n for n in state['notes'] if n['date'] == today]
    
    if not today_notes:
        return "📭 No notes today"
    
    by_category = {}
    for note in today_notes:
        cat = note['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(note['content'][:50])
    
    summary = f"📝 *TODAY'S NOTES ({len(today_notes)} total)*\n\n"
    for cat, items in by_category.items():
        emoji = {'ideas': '💡', 'tasks': '✅', 'meeting': '📅', 
                 'personal': '👤', 'inbox': '📥'}.get(cat, '📝')
        summary += f"{emoji} *{cat.upper()}* ({len(items)})\n"
        for item in items:
            summary += f"  • {item}\n"
        summary += "\n"
    
    return summary

def format_note_for_telegram(note):
    """Format note for Telegram display"""
    emoji = {'ideas': '💡', 'tasks': '✅', 'meeting': '📅', 
             'personal': '👤', 'inbox': '📥'}.get(note['category'], '📝')
    
    tags_str = ' '.join([f'#{t}' for t in note['tags']]) if note['tags'] else ''
    
    return f"""{emoji} *{note['category'].upper()}*
⏰ {note['time']}

{note['content']}

{tags_str}"""

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Telegram Notes Manager')
    parser.add_argument('action', choices=['create', 'list', 'search', 'summary'], 
                       help='Action to perform')
    parser.add_argument('text', nargs='?', help='Note text or search query')
    parser.add_argument('-c', '--category', help='Filter by category')
    parser.add_argument('-n', '--number', type=int, default=10, help='Number of notes to show')
    
    args = parser.parse_args()
    
    if args.action == 'create' and args.text:
        note = create_note(args.text)
        print(f"✅ Note created!")
        print(f"   ID: {note['id']}")
        print(f"   Category: {note['category']}")
        print(f"   File: {NOTES_DIR}/{note['category']}/{note['id']}.md")
        
    elif args.action == 'list':
        notes = list_notes(args.category, args.number)
        print(f"\n📝 Recent Notes ({len(notes)} total)\n")
        for note in notes:
            print(format_note_for_telegram(note))
            print("-" * 40)
            
    elif args.action == 'search' and args.text:
        results = search_notes(args.text)
        print(f"\n🔍 Search: '{args.text}' ({len(results)} results)\n")
        for note in results:
            print(format_note_for_telegram(note))
            print("-" * 40)
            
    elif args.action == 'summary':
        print(generate_daily_summary())
        
    else:
        print("📝 Telegram Quick Notes")
        print("=" * 40)
        print("\nUsage:")
        print("  python3 telegram_notes.py create 'My note text #idea'")
        print("  python3 telegram_notes.py list -n 5")
        print("  python3 telegram_notes.py search 'keyword'")
        print("  python3 telegram_notes.py summary")
        print("\nCategories: #idea #task #meeting #personal #inbox")
        print("Tags: Use #tag anywhere in the note")
