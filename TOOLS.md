# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Credentials

### Navii Automation
- **Website:** https://navii-automation.de
- **Calendly:** https://calendly.com/kontakt-navii-automation/new-meeting

### Calendly
- **Account:** kontakt@navii-automation.de
- **Pass:** Billiondollar17

### Telegram
- **Bot:** @naviiautomationbot
- **API Token:** 8294286642:AAFKb09yfYMA5G4xrrr0yz0RCnHaph7IpBw
- **Status:** ✅ CONNECTED
- **Chat ID:** 6599716126

### n8n Cloud
- **URL:** https://navii-automation.app.n8n.cloud
- **API Key:** [in Session]

### Email (IONOS) - PRIMARY
- **Account:** kontakt@navii-automation.de
- **Provider:** IONOS
- **SMTP Server:** smtp.ionos.de:587 (STARTTLS)
- **IMAP Server:** imap.ionos.de:993 (SSL)
- **Username:** kontakt@navii-automation.de
- **Pass:** Billiondollar17
- **Status:** ✅ AKTIV - Nutze Python smtplib (nicht curl!)
- **Send Script:** ~/.openclaw/workspace/scripts/ionos_send.py
- **Note:** curl trigger IONOS Policy Restrictions - Python smtplib works correctly

### Moltbook
- **API Key:** moltbook_sk_UpSfIoy77NKxo-CA2vbTPVgVIyHcUbBj
- **Agent Status:** Pending Claim

### Gmail (SMART EMAIL AUTOMATION)
- **Account:** edlmairfridolin@gmail.com
- **App Password:** uwwf tlao blzj iecl
- **IMAP Server:** imap.gmail.com:993 (SSL)
- **SMTP Server:** smtp.gmail.com:587 (TLS)
- **Status:** ✅ AKTIV - Smart Email Automation läuft

---

Add whatever helps you do your job. This is your cheat sheet.
