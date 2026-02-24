# Daily Standup Generator

Automatically generates daily standup reports from email activity, leads, and system metrics.

## Quick Start

```bash
# Generate and send standup
python3 ~/.openclaw/workspace/skills/stream2/2025-02-24-1829-daily-standup/standup.py

# Add to crontab (daily at 9 AM)
0 9 * * * /usr/bin/python3 ~/.openclaw/workspace/skills/stream2/2025-02-24-1829-daily-standup/standup.py
```

## Features

- 📧 Email stats (sent/received)
- 🔥 Lead count from detector
- 📊 Key activities summary
- 🎯 Daily focus areas
- ⚠️ Blocker tracking

## Report Format

```
📋 DAILY STANDUP - Tuesday, 24.02.2026

📧 EMAILS
├─ Received: 20
├─ Sent: 5
└─ Leads: 3

📊 KEY ACTIVITIES
• Project A completed
• Meeting with client X
• Deployed feature Y

🎯 TODAY'S FOCUS
• Goal 1
• Goal 2

⚠️ BLOCKERS
• None
```

## Integration

- Reads from Email Lead Detector state
- Sends to Telegram
- Saves local copy

## Files

- `standup.py` - Main script
- `standup_YYYYMMDD.txt` - Saved reports

## Customization

Edit the `generate_standup()` function to add:
- Calendar events
- Task completions
- Git commits
- Custom metrics
