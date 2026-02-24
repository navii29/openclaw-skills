# Smart Email Lead Detector

Automatically monitors Gmail inbox, scores incoming emails for lead potential (1-10), and sends Telegram alerts for high-value leads (score >= 7).

## Quick Start

```bash
# Run manually
python3 ~/.openclaw/workspace/skills/stream2/2025-02-24-1827-email-lead-detector/lead_detector.py

# Add to crontab (run every 15 minutes)
*/15 * * * * /usr/bin/python3 ~/.openclaw/workspace/skills/stream2/2025-02-24-1827-email-lead-detector/lead_detector.py >> ~/.openclaw/logs/lead-detector.log 2>&1
```

## How It Works

1. **Connects to Gmail** via IMAP
2. **Checks unread emails** from last 24h
3. **Scores each email** based on:
   - Keywords (Angebot, Termin, Budget, Automation, etc.)
   - Direct questions
   - Business email domains
   - Negative keywords (newsletter, spam, etc.)
4. **Sends Telegram alert** for leads with score >= 7
5. **Tracks processed emails** to avoid duplicates

## Scoring System

| Score | Rating | Action |
|-------|--------|--------|
| 8-10 | 🔥 Hot Lead | Telegram alert + manual follow-up |
| 6-7 | ⭐ Warm Lead | Telegram alert |
| 4-5 | 📧 Cold Lead | Logged only |
| 1-3 | 💤 Ignore | No action |

## Keywords

**High-value:** interesse, angebot, preis, budget, termin, demo, beratung, automation, dringend, zusammenarbeit, implementierung, ki, ai

**Negative:** newsletter, unsubscribe, abmelden, werbung, spam, noreply

## Files

- `lead_detector.py` - Main script
- `lead_state.json` - Tracks processed emails
- `SKILL.md` - This file

## Integration

Uses credentials from TOOLS.md:
- Gmail: edlmairfridolin@gmail.com
- Telegram: @naviiautomationbot

## Future Enhancements

- [ ] CRM integration (HubSpot, Pipedrive)
- [ ] Auto-reply with Calendly link
- [ ] Lead source tracking
- [ ] Weekly lead reports
