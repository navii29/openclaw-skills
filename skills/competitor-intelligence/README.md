# 🕵️ Competitor Intelligence Monitor

> Automated competitor monitoring with AI-powered insights. Never miss a competitor move again.

## What is it?

A powerful monitoring system that tracks your competitors automatically:

- 💰 **Price Monitoring** - Get alerted when competitors change prices
- 🏠 **Homepage Tracking** - Detect messaging and positioning changes  
- 📰 **News Mentions** - Know when competitors are in the news
- 🤖 **AI Insights** - Get strategic analysis of competitor moves
- 📱 **Telegram Alerts** - Instant notifications on your phone

## Perfect For

- **E-Commerce Shops** - Never get undercut without knowing
- **SaaS Companies** - Track competitor features and pricing
- **Agencies** - Intelligence for pitches and strategy
- **Consultants** - Stay ahead of market changes

## Quick Start

```bash
# 1. Setup
python scripts/competitor_monitor.py --setup

# 2. Run first scan
python scripts/competitor_monitor.py --scan

# 3. Set up daily monitoring (cron)
openclaw cron add \
  --name "competitor-check" \
  --schedule "0 9 * * *" \
  --session isolated \
  --message "Run: python3 competitor_monitor.py --scan"
```

## Example Alert

```
🕵️ Competitor Alert: CompetitorX

💰 PRICE CHANGE
Product: Premium Plan
Old: €99/month
New: €79/month (-20%)

🤖 AI Insight:
"Aggressive pricing move. Likely trying to capture 
market share before Q4. Consider matching or 
emphasizing premium features."

🔗 https://competitorx.de/pricing
```

## Pricing

- **Setup Fee:** €299 (one-time)
- **Monthly:** €149/month
- **Includes:** Up to 5 competitors, daily scans, Telegram alerts

## Files

- `SKILL.md` - Full documentation
- `scripts/competitor_monitor.py` - Main monitoring script
- `assets/` - Marketing materials

## Requirements

- Python 3.8+
- Tavily API key (for AI insights)
- Telegram Bot (for alerts)

## Status

✅ **Production Ready** - Version 1.0.0
