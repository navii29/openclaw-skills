#!/usr/bin/env python3
"""
Competitor Monitor
Track competitor websites for changes in pricing, features, or content.
Sends Telegram alerts when changes detected.
"""

import urllib.request
import urllib.parse
import hashlib
import json
import os
from datetime import datetime

MONITOR_DIR = os.path.expanduser("~/.openclaw/workspace/skills/stream2/2025-02-24-1830-competitor-monitor")
STATE_FILE = os.path.join(MONITOR_DIR, "monitor_state.json")
SITES_FILE = os.path.join(MONITOR_DIR, "sites.json")

def ensure_dir():
    """Create monitor directory"""
    if not os.path.exists(MONITOR_DIR):
        os.makedirs(MONITOR_DIR)

def load_sites():
    """Load monitored sites"""
    if os.path.exists(SITES_FILE):
        with open(SITES_FILE) as f:
            return json.load(f)
    return {
        "sites": [
            {
                "name": "Example Competitor",
                "url": "https://example.com/pricing",
                "selector": None,
                "enabled": False
            }
        ]
    }

def save_sites(sites):
    """Save sites config"""
    with open(SITES_FILE, 'w') as f:
        json.dump(sites, f, indent=2)

def load_state():
    """Load monitor state"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"snapshots": {}}

def save_state(state):
    """Save monitor state"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def fetch_url(url):
    """Fetch URL content"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  ❌ Error fetching {url}: {e}")
        return None

def hash_content(content):
    """Create hash of content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def check_site(site):
    """Check a single site for changes"""
    url = site['url']
    name = site['name']
    
    print(f"\n🔍 Checking: {name}")
    print(f"   URL: {url}")
    
    # Fetch content
    content = fetch_url(url)
    if not content:
        return None
    
    # Create hash
    current_hash = hash_content(content)
    
    # Load previous state
    state = load_state()
    previous = state['snapshots'].get(url, {})
    previous_hash = previous.get('hash')
    
    result = {
        'name': name,
        'url': url,
        'changed': False,
        'first_check': previous_hash is None,
        'timestamp': datetime.now().isoformat()
    }
    
    if previous_hash is None:
        print(f"   📸 First snapshot taken")
        result['status'] = 'new'
    elif previous_hash != current_hash:
        print(f"   🚨 CHANGE DETECTED!")
        result['changed'] = True
        result['status'] = 'changed'
        result['old_hash'] = previous_hash
        result['new_hash'] = current_hash
    else:
        print(f"   ✅ No changes")
        result['status'] = 'unchanged'
    
    # Save snapshot
    state['snapshots'][url] = {
        'hash': current_hash,
        'checked_at': datetime.now().isoformat(),
        'content_preview': content[:500] if content else ''
    }
    save_state(state)
    
    return result

def send_change_alert(results):
    """Send Telegram alert for changes"""
    changes = [r for r in results if r.get('changed')]
    
    if not changes:
        return
    
    try:
        import urllib.request
        import urllib.parse
        
        token = "8294286642:AAFKb09yfYMA5G4xrrr0yz0RCnHaph7IpBw"
        chat_id = "6599716126"
        
        message = "🚨 *COMPETITOR CHANGES DETECTED!*\n\n"
        
        for change in changes:
            message += f"📊 *{change['name']}*\n"
            message += f"🔗 {change['url'][:60]}...\n"
            message += f"⏰ {datetime.now().strftime('%H:%M %d.%m')}\n\n"
        
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
        print(f"   ❌ Telegram error: {e}")
        return False

def add_site(name, url):
    """Add new site to monitor"""
    sites = load_sites()
    
    sites['sites'].append({
        'name': name,
        'url': url,
        'selector': None,
        'enabled': True,
        'added_at': datetime.now().isoformat()
    })
    
    save_sites(sites)
    print(f"✅ Added: {name} ({url})")

def list_sites():
    """List all monitored sites"""
    sites = load_sites()
    
    print(f"\n📊 Monitored Sites ({len(sites['sites'])})\n")
    
    for site in sites['sites']:
        status = "✅" if site.get('enabled') else "❌"
        print(f"{status} {site['name']}")
        print(f"   URL: {site['url']}")
        print()

def run_check():
    """Run full monitoring check"""
    ensure_dir()
    sites = load_sites()
    
    print("🕵️  Competitor Monitor")
    print("=" * 50)
    
    results = []
    enabled_sites = [s for s in sites['sites'] if s.get('enabled')]
    
    for site in enabled_sites:
        result = check_site(site)
        if result:
            results.append(result)
    
    # Send alerts
    changes = [r for r in results if r.get('changed')]
    if changes:
        print(f"\n🚨 {len(changes)} changes detected - sending alert...")
        send_change_alert(results)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"   Total: {len(results)}")
    print(f"   Changed: {len(changes)}")
    print(f"   New: {sum(1 for r in results if r.get('first_check'))}")
    print(f"   Unchanged: {sum(1 for r in results if r.get('status') == 'unchanged')}")
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Competitor Monitor')
    parser.add_argument('action', choices=['check', 'add', 'list'], 
                       help='Action to perform')
    parser.add_argument('--name', help='Site name')
    parser.add_argument('--url', help='Site URL')
    
    args = parser.parse_args()
    
    if args.action == 'check':
        run_check()
    elif args.action == 'add':
        if args.name and args.url:
            add_site(args.name, args.url)
        else:
            print("Usage: python3 competitor_monitor.py add --name 'Competitor' --url 'https://...'")
    elif args.action == 'list':
        list_sites()
