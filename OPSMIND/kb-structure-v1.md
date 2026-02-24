# KB STRUCTURE v1 - Operations Knowledge Base

**Root:** `/Users/fridolin/.openclaw/workspace/`

---

## 📁 Folder Hierarchy

```
workspace/
├── 📊 STRATEGY/          # Business Strategy
│   ├── ceo-dashboard.md
│   ├── outreach-templates-READY.md
│   ├── case-study-*.md
│   ├── lead-queue-*.md
│   ├── sent-emails-log.md
│   └── email-*.txt
│
├── 🛠️ TOOLS.md           # Credentials & Config
│
├── 🤖 n8n-workflows/     # Automation Blueprints
│   ├── 01-*.json
│   ├── 02-*.json
│   └── README.md
│
├── 💾 notion/             # Notion Import/Export
│   └── *.csv, *.md
│
├── 🎯 DELIVERY/          # Delivery Blueprints (WIP)
│   ├── blueprint-starter-v1.md
│   └── blueprint-growth-v1.md
│
├── 📱 OPSMIND/           # Operations & Memory
│   ├── memory-v1.md      # ← 12 Bullets, updated daily
│   ├── backlog-v1.md     # Parked initiatives
│   ├── kb-structure-v1.md # This file
│   └── crm-stages-v1.md  # Stage definitions
│
└── 📄 AGENTS.md          # System Instructions
```

---

## 📝 Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Templates | `*-templates-*.md` | `outreach-templates-READY.md` |
| Lead Lists | `lead-queue-*.md` | `lead-queue-hackernews.md` |
| Emails | `email-*.txt` | `email-tiangolo.txt` |
| Blueprints | `blueprint-*-v*.md` | `blueprint-starter-v1.md` |
| Memory | `memory-v*.md` | `memory-v1.md` |

---

## 🔄 Update Cadence

| Document | Update Frequency | Owner |
|----------|------------------|-------|
| memory-v1.md | Every 24h or on major change | OPSMIND |
| lead-queue-*.md | Real-time as leads found | VOX/ATLAS |
| sent-emails-log.md | Per email sent | VOX |
| ceo-dashboard.md | Every cycle (30-60min) | NAVI |
| kb-structure-v1.md | On structural changes | OPSMIND |

---

## 🔍 Quick Access

**Start here:**
1. Check `memory-v1.md` for context
2. Check `STRATEGY/lead-queue-*.md` for leads
3. Check `STRATEGY/sent-emails-log.md` for outreach status
4. Update `memory-v1.md` after each cycle
