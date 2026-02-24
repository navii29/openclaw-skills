# Competitor Monitor

Track competitor websites for changes. Get Telegram alerts when pricing, features, or content updates.

## Quick Start

```bash
# List monitored sites
python3 competitor_monitor.py list

# Add competitor
python3 competitor_monitor.py add --name "Competitor X" --url "https://competitor.com/pricing"

# Run check
python3 competitor_monitor.py check
```

## How It Works

1. **Fetches** each monitored URL
2. **Hashes** the content for comparison
3. **Detects** changes between checks
4. **Alerts** via Telegram when changes found

## Features

- 🕵️  SHA-256 content hashing
- 📊 Site status tracking
- 🚨 Telegram change alerts
- 📸 Content snapshots
- ⚡ Fast diff detection

## Configuration

Sites stored in `sites.json`:
```json
{
  "sites": [
    {
      "name": "Competitor X",
      "url": "https://competitor.com/pricing",
      "enabled": true
    }
  ]
}
```

## Automation

```bash
# Check every hour
crontab -e
0 * * * * /usr/bin/python3 ~/.openclaw/workspace/skills/stream2/2025-02-24-1830-competitor-monitor/competitor_monitor.py check
```

## Use Cases

- 💰 Pricing page monitoring
- 📝 Feature comparison tracking
- 📰 News/blog updates
- 🎯 Landing page changes

## Future Enhancements

- [ ] CSS Selector targeting
- [ ] Visual diff screenshots
- [ ] Price extraction & tracking
- [ ] RSS feed integration
- [ ] Slack/Discord webhooks
