# Telegram Quick Notes

Create and manage notes via Telegram or CLI. Organized by categories with markdown export.

## Quick Start

```bash
# Create a note
python3 telegram_notes.py create "My idea for a new product #idea #urgent"

# Create task
python3 telegram_notes.py create "#task Call client about project"

# List recent notes
python3 telegram_notes.py list -n 10

# Search notes
python3 telegram_notes.py search "project"

# Daily summary
python3 telegram_notes.py summary
```

## Categories

Use prefixes to categorize notes:

| Prefix | Category | Emoji |
|--------|----------|-------|
| `#idea` | Ideas | 💡 |
| `#task` | Tasks | ✅ |
| `#meeting` | Meetings | 📅 |
| `#personal` | Personal | 👤 |
| `#inbox` | Inbox (default) | 📥 |

## Tags

Add tags anywhere in the note with `#`:
```
Meeting with client about automation #meeting #urgent #client-name
```

## Storage

Notes saved as markdown files:
```
notes/
├── inbox/
├── ideas/
├── tasks/
├── meeting/
└── personal/
```

Each note includes YAML frontmatter:
```markdown
---
id: 20260224_182915
date: 2026-02-24
time: 18:29
category: ideas
tags: automation, marketing
source: cli
---

Note content here...
```

## Integration

Can be hooked up to Telegram bot for instant note creation:
- Send message → Auto-saved as note
- Reply with confirmation
- Daily summary on request

## Use Cases

- 💡 Capture ideas on the go
- ✅ Quick task logging
- 📅 Meeting notes
- 🔍 Searchable knowledge base
