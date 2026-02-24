# Meeting Notes to Tasks

Extract action items from meeting notes. Create structured task lists with assignees and deadlines.

## Quick Start

```bash
# Process meeting notes
python3 meeting_tasks.py process \
  --title "Team Meeting" \
  --notes "- Max wird Präsentation erstellen @max #2d"

# List all tasks
python3 meeting_tasks.py list

# List by assignee
python3 meeting_tasks.py list --assignee max

# Generate summary
python3 meeting_tasks.py summary

# Export to markdown
python3 meeting_tasks.py export
```

## Task Syntax

Tasks are automatically detected using these patterns:

```markdown
- Task description @assignee #deadline
* Task description @assignee #deadline
TODO: Task description @assignee #deadline
ACTION: Task description @assignee #deadline
```

## Deadlines

| Suffix | Meaning | Example |
|--------|---------|---------|
| `#2h` | 2 hours | `#4h` |
| `#3d` | 3 days | `#2d` |
| `#1w` | 1 week | `#2w` |
| `#1m` | 1 month | `#3m` |

## Examples

```bash
# From file
python3 meeting_tasks.py process --title "Sprint Planning" --file notes.txt

# Inline notes
python3 meeting_tasks.py process --title "Daily" --notes "- Review PRs @dev-team #4h"

# List open tasks
python3 meeting_tasks.py list --status open

# Show summary for Telegram
python3 meeting_tasks.py summary
```

## Output Format

```
⬜ Website Update
⬜ Landingpage erstellen @max (📅 2026-02-26)
⬜ Content erstellen @anna (📅 2026-03-03)
```

## Storage

- `tasks.json` - All tasks and meetings
- `tasks_export.md` - Markdown export

## Integration

- Works with `telegram_notes.py` for mobile note-taking
- Can trigger Telegram alerts for new tasks
- Export to project management tools

## Status Values

- ⬜ `open` - Not started
- 🔄 `in_progress` - Working on it
- ✅ `done` - Completed
