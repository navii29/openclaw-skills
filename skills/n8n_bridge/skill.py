#!/usr/bin/env python3
"""
n8n Bridge Skill for OpenClaw
Enables bidirectional communication between OpenClaw agents and n8n workflows

Usage:
    from skills.n8n_bridge import send_command, update_hubspot, send_slack
    
    result = send_command("slack_notify", {
        "channel": "#sales",
        "text": "New lead qualified!"
    })
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "https://navii-automation.app.n8n.cloud")
N8N_WEBHOOK_PATH = os.getenv("N8N_WEBHOOK_PATH", "/webhook/openclaw-command")
N8N_API_KEY = os.getenv("N8N_BRIDGE_API_KEY", "")
DEFAULT_TIMEOUT = int(os.getenv("N8N_BRIDGE_TIMEOUT", "30"))

N8N_WEBHOOK_URL = f"{N8N_BASE_URL}{N8N_WEBHOOK_PATH}"


class N8NBridgeError(Exception):
    """Custom exception for n8n bridge errors"""
    pass


def send_command(
    command: str,
    payload: Dict[str, Any],
    wait_for_response: bool = True,
    timeout: int = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """
    Send a command to n8n orchestrator.
    
    Args:
        command: Type of command (crm_update, slack_notify, email_send, etc.)
        payload: Command-specific data
        wait_for_response: Whether to wait for n8n response
        timeout: Timeout in seconds
    
    Returns:
        n8n response dict with status and result data
    
    Raises:
        N8NBridgeError: If API key not configured or request fails
    
    Example:
        >>> send_command("slack_notify", {
        ...     "channel": "#test",
        ...     "text": "Hello from OpenClaw!"
        ... })
        {'status': 'success', 'command': 'slack_notify', 'processed_at': '2024-...'}
    """
    
    if not N8N_API_KEY:
        raise N8NBridgeError("N8N_BRIDGE_API_KEY not configured. Set environment variable.")
    
    data = {
        "source": "openclaw",
        "timestamp": datetime.utcnow().isoformat(),
        "command": command,
        "payload": payload
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": N8N_API_KEY
    }
    
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=data,
            headers=headers,
            timeout=timeout if wait_for_response else 5
        )
        response.raise_for_status()
        
        if wait_for_response:
            return response.json()
        else:
            return {"status": "sent", "command": command, "async": True}
            
    except requests.Timeout:
        return {
            "status": "timeout",
            "command": command,
            "message": f"Request timed out after {timeout}s",
            "fallback": "queued_for_retry"
        }
    except requests.HTTPError as e:
        return {
            "status": "error",
            "command": command,
            "http_status": e.response.status_code,
            "message": str(e)
        }
    except requests.RequestException as e:
        return {
            "status": "error",
            "command": command,
            "message": f"Request failed: {str(e)}"
        }


# ============== Convenience Functions ==============

def ping() -> Dict[str, Any]:
    """Test connectivity to n8n bridge"""
    return send_command("ping", {"test": True}, timeout=10)


def update_hubspot_record(
    object_type: str,
    object_id: str,
    properties: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update a HubSpot record (deal, contact, company, ticket).
    
    Args:
        object_type: Type of object (deal, contact, company, ticket)
        object_id: HubSpot object ID
        properties: Dict of properties to update
    
    Example:
        >>> update_hubspot_record("deal", "12345", {
        ...     "dealstage": "qualified",
        ...     "amount": 50000
        ... })
    """
    return send_command("crm_update", {
        "system": "hubspot",
        "object_type": object_type,
        "object_id": object_id,
        "properties": properties
    })


def create_hubspot_deal(
    deal_name: str,
    amount: Optional[float] = None,
    pipeline: str = "default",
    stage: str = "appointmentscheduled",
    **extra_properties
) -> Dict[str, Any]:
    """
    Create a new HubSpot deal.
    
    Args:
        deal_name: Name of the deal
        amount: Deal value in EUR
        pipeline: Pipeline ID
        stage: Deal stage
        **extra_properties: Additional HubSpot properties
    
    Example:
        >>> create_hubspot_deal("Acme Corp Project", amount=25000)
    """
    properties = {
        "dealname": deal_name,
        "pipeline": pipeline,
        "dealstage": stage,
        **extra_properties
    }
    if amount is not None:
        properties["amount"] = amount
    
    return send_command("crm_create", {
        "system": "hubspot",
        "properties": properties
    })


def send_slack(
    channel: str,
    text: str,
    blocks: Optional[list] = None
) -> Dict[str, Any]:
    """
    Send Slack notification.
    
    Args:
        channel: Channel name (e.g., "#sales") or user ID
        text: Message text
        blocks: Optional Slack Block Kit blocks
    
    Example:
        >>> send_slack("#sales", "🔥 New hot lead: Acme Corp")
    """
    payload = {
        "channel": channel,
        "text": text
    }
    if blocks:
        payload["blocks"] = blocks
    
    return send_command("slack_notify", payload)


def send_email(
    to: str,
    subject: str,
    body: str,
    from_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email via configured provider (n8n handles the actual sending).
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body (plain text or HTML)
        from_email: Sender email (optional)
    
    Example:
        >>> send_email("client@example.com", "Proposal Ready", "Hi, your proposal...")
    """
    payload = {
        "to": to,
        "subject": subject,
        "body": body
    }
    if from_email:
        payload["from"] = from_email
    
    return send_command("email_send", payload)


def block_calendar(
    title: str,
    start_time: str,
    duration_minutes: int = 30,
    attendees: Optional[list] = None
) -> Dict[str, Any]:
    """
    Block time in Google Calendar.
    
    Args:
        title: Event title
        start_time: ISO 8601 datetime string
        duration_minutes: Duration in minutes (default: 30)
        attendees: List of attendee emails (optional)
    
    Example:
        >>> block_calendar(
        ...     "Prep: Acme Call",
        ...     "2024-02-28T14:00:00Z",
        ...     duration_minutes=30
        ... )
    """
    return send_command("calendar_block", {
        "title": title,
        "start": start_time,
        "duration": duration_minutes,
        "attendees": attendees or []
    })


def create_notion_page(
    database_id: str,
    properties: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a page in Notion database.
    
    Args:
        database_id: Notion database ID
        properties: Notion page properties
    
    Example:
        >>> create_notion_page("abc123", {
        ...     "Name": {"title": [{"text": {"content": "Meeting Notes"}}]},
        ...     "Status": {"select": {"name": "Done"}}
        ... })
    """
    return send_command("notion_create", {
        "database_id": database_id,
        "properties": properties
    })


# ============== Batch Operations ==============

def multi_action(actions: list) -> list:
    """
    Execute multiple commands in sequence.
    
    Args:
        actions: List of dicts with 'command' and 'payload' keys
    
    Returns:
        List of results for each action
    
    Example:
        >>> multi_action([
        ...     {"command": "crm_create", "payload": {...}},
        ...     {"command": "slack_notify", "payload": {...}},
        ...     {"command": "calendar_block", "payload": {...}}
        ... ])
    """
    results = []
    for action in actions:
        result = send_command(
            action["command"],
            action.get("payload", {})
        )
        results.append(result)
    return results


# ============== Testing ==============

def test_bridge():
    """Run connectivity tests"""
    print("🧪 Testing n8n Bridge...")
    
    # Test 1: Ping
    print("\n1. Testing ping...")
    result = ping()
    assert result.get("status") == "pong", f"Ping failed: {result}"
    print("   ✅ Ping successful")
    
    # Test 2: Config check
    print("\n2. Checking configuration...")
    if not N8N_API_KEY:
        print("   ⚠️  N8N_BRIDGE_API_KEY not set")
    else:
        print("   ✅ API key configured")
    
    print(f"   🌐 Webhook URL: {N8N_WEBHOOK_URL}")
    
    print("\n✅ Bridge tests complete")
    return True


if __name__ == "__main__":
    test_bridge()
