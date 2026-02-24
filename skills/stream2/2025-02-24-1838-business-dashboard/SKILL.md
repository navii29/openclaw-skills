# Business Dashboard

Unified dashboard combining all Stream 2 skills. View leads, tasks, invoices, and metrics at a glance.

## Quick Start

```bash
# Show dashboard
python3 dashboard.py show

# Save to file
python3 dashboard.py save

# Send to Telegram
python3 dashboard.py telegram
```

## Features

- 📊 Real-time metrics from all skills
- 🔥 Lead tracking
- ✅ Task overview
- 🧾 Financial summary
- 💰 Revenue pipeline
- 📈 Productivity metrics

## Data Sources

| Skill | Data |
|-------|------|
| 1 - Lead Detector | Total leads, hot leads |
| 8 - Meeting Tasks | Open/done tasks |
| 9 - Invoice Generator | Revenue, outstanding |
| 5 - Telegram Notes | Today's notes |

## Dashboard Sections

### Leads
- Total leads found
- Hot leads (score 8-10)
- Emails processed

### Tasks
- Open tasks
- Completed tasks
- Overdue tasks

### Invoices
- Total invoices
- Paid amount
- Outstanding amount
- Draft amount

### Financial Health
- Revenue (paid)
- Outstanding (sent)
- Pipeline (drafts + outstanding)

## Telegram Summary

Compact format for mobile:
```
📊 DASHBOARD - 24.02.18:34

🔥 Leads: 3 hot / 12 total
✅ Tasks: 4 open / 2 done
🧾 Revenue: 15000€ / 3500€ open

🎯 Skills: 10/10 active ✅
```

## Automation

```bash
# Send daily dashboard at 9 AM
crontab -e
0 9 * * * /usr/bin/python3 ~/.openclaw/workspace/skills/stream2/2025-02-24-1838-business-dashboard/dashboard.py telegram
```

## Future Enhancements

- [ ] Web-based dashboard
- [ ] Historical trends
- [ ] Goal tracking
- [ ] Team member stats
- [ ] Export to PDF
