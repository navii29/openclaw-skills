# Inbox AI Cloud v3.1
## Universal Email Automation for GitHub Actions

Cloud-native email automation supporting **all major providers**: Gmail, Outlook/365, IONOS, iCloud, Yahoo, Zoho, GMX, Fastmail, and custom IMAP.

---

## ✨ Features

- ✅ **Multi-Account** — Unlimited email accounts (Support, Sales, Info, etc.)
- ✅ **Universal Providers** — Auto-detection for 9 major email services
- ✅ **Cloud-Native** — Runs on GitHub Actions (free 2,000 min/month)
- ✅ **Smart Categorization** — AI-powered email sorting
- ✅ **Auto-Reply** — Contextual responses based on email type
- ✅ **Rate Limiting** — Prevents blacklisting
- ✅ **Circuit Breaker** — Survives provider outages
- ✅ **Deduplication** — SQLite state management
- ✅ **Escalation** — Flags urgent/complex emails

---

## 🚀 Quick Start

### Step 1: Fork & Configure

1. Fork this repository
2. Go to **Settings → Secrets and variables → Actions**
3. Add your email account(s):

| Secret | Description | Example |
|--------|-------------|---------|
| `ACCOUNT_1_EMAIL` | Email address | `kontakt@navii-automation.de` |
| `ACCOUNT_1_PASSWORD` | App password (not regular password!) | `xxxx-xxxx-xxxx-xxxx` |
| `ACCOUNT_1_PROVIDER` | Provider (or `auto`) | `ionos`, `gmail`, `outlook` |
| `ACCOUNT_1_FROM_NAME` | Display name | `Navii Automation` |
| `ACCOUNT_1_AUTO_REPLY` | Enable auto-replies | `true` or `false` |
| `ACCOUNT_1_CALENDLY_LINK` | Optional: Meeting link | `https://calendly.com/...` |

### Step 2: Enable Workflow

1. Go to **Actions** tab
2. Click "I understand my workflows..."
3. The workflow runs automatically every 10 min (Mon-Fri, 6am-8pm UTC)

### Step 3: Monitor

Check the Actions tab for real-time logs.

---

## 📧 Supported Providers

| Provider | Auto-Detect | App Password Required | Setup Guide |
|----------|-------------|----------------------|-------------|
| **Gmail** | ✅ | ✅ Yes | [Create App Password](https://myaccount.google.com/apppasswords) |
| **Outlook/365** | ✅ | ❌ No | [Enable IMAP](https://outlook.live.com/mail/0/options/mail/accounts/popImap) |
| **IONOS** | ✅ | ❌ No | Use regular password |
| **iCloud** | ✅ | ✅ Yes | [Generate App Password](https://appleid.apple.com/account/manage) |
| **Yahoo** | ✅ | ✅ Yes | [Account Security](https://login.yahoo.com/account/security) |
| **Zoho** | ✅ | ❌ No | [IMAP Settings](https://mail.zoho.com/zm/#settings/accounts/imap) |
| **GMX** | ✅ | ❌ No | Use regular password |
| **Fastmail** | ✅ | ✅ Yes | [App Passwords](https://www.fastmail.com/settings/security/apps) |
| **Custom** | ❌ | Varies | Set `IMAP_SERVER` and `SMTP_SERVER` |

---

## ⚙️ Processing Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `monitor` | Read-only, no replies | Testing, auditing |
| `hybrid` | Processes, drafts replies (no sending) | Review before enabling |
| `auto` | Full automation | Production |

Change mode in GitHub Actions → Run workflow → Select mode.

---

## 🏷️ Email Categories

Emails are automatically categorized:

| Category | Keywords | Auto-Reply? |
|----------|----------|-------------|
| `booking` | meeting, termin, calendly, appointment | ✅ Yes |
| `support` | help, problem, error, issue | ✅ Yes |
| `inquiry` | quote, pricing, angebot | ✅ Yes |
| `billing` | invoice, payment, rechnung | ✅ Yes |
| `legal` | gdpr, complaint, lawyer | ⚠️ Escalated |
| `spam` | newsletter, unsubscribe | 🗑️ Archived |
| `general` | (everything else) | ✅ Yes |

---

## 🔐 Security

- Passwords stored in **GitHub Secrets** (encrypted)
- **App Passwords** required for Gmail, iCloud, Yahoo, Fastmail
- Never commit credentials to repository
- State persisted via GitHub cache (30 days)

---

## 📊 Multi-Account Setup

Add more accounts by creating additional secrets:

```
ACCOUNT_2_EMAIL=kontakt@navii-automation.de
ACCOUNT_2_PASSWORD=...
ACCOUNT_2_NAME=support
...
```

Up to 5 accounts supported out of the box. For more, edit `.github/workflows/inbox-ai-cloud.yml`.

---

## 🛠️ Local Testing

```bash
# Clone
gh repo clone yourusername/inbox-ai-cloud
cd inbox-ai-cloud

# Install Python 3.11+
python3 --version

# Create config
cp accounts.json.example accounts.json
# Edit with your credentials

# Test connection
python3 inbox_processor_cloud.py --test --config=accounts.json

# Run in monitor mode
python3 inbox_processor_cloud.py --mode=monitor --config=accounts.json

# Full automation
python3 inbox_processor_cloud.py --mode=auto --config=accounts.json
```

---

## 📈 Monitoring

View 24h statistics in GitHub Actions logs:

```json
{
  "timestamp": "2026-02-27T12:00:00",
  "mode": "auto",
  "stats_24h": {
    "total": 45,
    "escalations": 3,
    "by_category": {
      "booking": 12,
      "support": 8,
      "inquiry": 15,
      "billing": 5,
      "general": 5
    }
  }
}
```

---

## 🚨 Troubleshooting

### "Authentication failed"
- Gmail/iCloud/Yahoo: Use **App Password**, not regular password
- Check IMAP is enabled in provider settings

### "Connection refused"
- Verify provider settings
- Disable VPN if active
- IONOS: Wait 10 min after enabling IMAP

### "Rate limit exceeded"
- Reduce `max_replies_per_hour` in config
- Emails still processed, just not auto-replied

---

## 📝 License

MIT — Free to use, modify, and deploy.

Built with ❤️ for the OpenClaw community.
