# n8n Bridge Skill

**Status:** ✅ Ready for testing  
**Category:** Integration  
**Complexity:** Medium

## Overview

Enables bidirectional communication between OpenClaw agents and n8n workflows. Agents can trigger external actions (CRM updates, Slack messages, emails, calendar events) through a unified API.

## Installation

1. Set environment variables:
```bash
export N8N_BASE_URL="https://navii-automation.app.n8n.cloud"
export N8N_BRIDGE_API_KEY="your_api_key_here"
```

2. Import n8n workflow:
```bash
# In n8n: Settings → Workflows → Import
# Select: n8n-workflows/06-openclaw-command-router.json
```

3. Configure n8n environment variable:
```
BRIDGE_API_KEY=your_api_key_here
```

## Quick Start

```python
from skills.n8n_bridge import (
    ping,
    send_slack,
    create_hubspot_deal,
    block_calendar,
    send_email
)

# Test connectivity
ping()

# Send Slack notification
send_slack("#sales", "🔥 New lead qualified: Acme Corp")

# Create HubSpot deal
create_hubspot_deal("Acme Corp Project", amount=25000)

# Block calendar time
block_calendar("Prep: Acme Call", "2024-02-28T14:00:00Z", 30)

# Send email
send_email("client@example.com", "Proposal Ready", "Hi, your proposal is ready...")
```

## Available Commands

| Function | Command | Description |
|----------|---------|-------------|
| `ping()` | `ping` | Test connectivity |
| `update_hubspot_record()` | `crm_update` | Update existing CRM record |
| `create_hubspot_deal()` | `crm_create` | Create new HubSpot deal |
| `send_slack()` | `slack_notify` | Send Slack message |
| `send_email()` | `email_send` | Send email via n8n |
| `block_calendar()` | `calendar_block` | Create calendar event |
| `create_notion_page()` | `notion_create` | Create Notion page |
| `send_command()` | Custom | Send any command |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `N8N_BASE_URL` | `https://navii-automation.app.n8n.cloud` | n8n instance URL |
| `N8N_WEBHOOK_PATH` | `/webhook/openclaw-command` | Webhook endpoint path |
| `N8N_BRIDGE_API_KEY` | (required) | API key for authentication |
| `N8N_BRIDGE_TIMEOUT` | `30` | Default request timeout |

## Error Handling

All functions return a dict with at least:
- `status`: "success", "error", "timeout"
- `command`: The command that was sent
- Additional fields depending on status

## Testing

```python
from skills.n8n_bridge import test_bridge
test_bridge()
```

## See Also

- `INTEGRATION-AGENT-COMMAND-CENTER.md` - Full documentation
- `n8n-workflows/06-openclaw-command-router.json` - n8n workflow
