# SevDesk Skill

Automate your German accounting with SevDesk. Create invoices, manage contacts, track vouchers, and reconcile bank transactions - all through natural language commands.

**Version:** 2.2.0  
**Last Updated:** February 24, 2026

## Features

### Core Features (v2.0+)
- ✅ **Smart Caching** - TTL-based response caching reduces API calls
- ✅ **Circuit Breaker** - Automatic failover on API issues
- ✅ **Retry Logic** - Exponential backoff for transient failures
- ✅ **Input Validation** - Decorator-based validation for all inputs
- ✅ **Type Safety** - Full type hints and enums for all status codes
- ✅ **Modern CLI** - argparse-based command-line interface
- ✅ **Rate Limit Tracking** - Monitor API usage and limits

### v2.2.0 New Features 🚀
- ✅ **Batch Operations** - Bulk create/update contacts and invoices with concurrency control
- ✅ **Health Monitoring** - API connectivity checks with detailed diagnostics
- ✅ **Webhook Support** - Register, manage, and verify SevDesk webhooks
- ✅ **CSV Export/Import** - Data portability with full contact/invoice export
- ✅ **Operation Queue** - Offline operation buffering with disk persistence
- ✅ **Async Processing** - Parallel batch operations for maximum throughput

## Quick Start

```python
from sevdesk_v2 import SevDeskClient, InvoiceStatus, WebhookEvent

# Initialize with all v2.2.0 features
client = SevDeskClient(
    enable_cache=True,
    batch_concurrency=5,
    webhook_secret="your_webhook_secret"
)

# List all contacts
contacts = client.list_contacts()

# Create an invoice (uses enums for type safety)
invoice = client.create_invoice(
    contact_id="12345",
    items=[{"name": "Consulting", "price": 500, "quantity": 1}],
    invoice_type=InvoiceType.INVOICE
)

# Check API health
health = client.health_check()
print(f"API is {'healthy' if health.healthy else 'unhealthy'}")
```

## Installation

1. Get your API token from SevDesk (Settings → User → API Token)
2. Set environment variable: `export SEVDESK_API_TOKEN=your_token`
3. Or create config file `sevdesk.json`: `{"api_token": "your_token"}`

## CLI Usage

### Basic Commands
```bash
# List contacts with search
python sevdesk_v2.py contacts --search "Müller" --limit 50

# List open invoices from date range
python sevdesk_v2.py invoices --status open --start-date 2024-01-01

# Show unpaid invoices overdue by 30 days
python sevdesk_v2.py unpaid --days 30

# View API statistics and cache hit rate
python sevdesk_v2.py stats --clear-cache
```

### v2.2.0: Health Check
```bash
# Check API health
python sevdesk_v2.py health

# Custom timeout
python sevdesk_v2.py health --timeout 10
```

### v2.2.0: Batch Operations
```bash
# Batch create contacts from CSV
python sevdesk_v2.py batch-create-contacts contacts.csv

# Dry run to validate CSV
python sevdesk_v2.py batch-create-contacts contacts.csv --dry-run

# Batch update invoice status
python sevdesk_v2.py batch-update-invoices "inv1,inv2,inv3" --status paid
```

### v2.2.0: Export/Import
```bash
# Export contacts to CSV
python sevdesk_v2.py export-contacts --output contacts_export.csv

# Export invoices with filters
python sevdesk_v2.py export-invoices --status open --start-date 2024-01-01
```

### v2.2.0: Webhooks
```bash
# List all webhooks
python sevdesk_v2.py webhooks

# Create webhook
python sevdesk_v2.py create-webhook "https://myapp.com/webhook" \
    --events "ContactCreate,InvoiceCreate" \
    --name "My Webhook"

# Delete webhook
python sevdesk_v2.py delete-webhook webhook_id
```

### v2.2.0: Operation Queue
```bash
# View queue status
python sevdesk_v2.py queue

# Process queued operations
python sevdesk_v2.py queue-process

# Clear queue
python sevdesk_v2.py queue-clear
```

## API Reference

### Core Methods
- `list_contacts()`, `create_contact()` - Contact management
- `list_invoices()`, `create_invoice()`, `send_invoice_email()` - Invoicing
- `list_vouchers()`, `create_voucher()` - Expense tracking
- `list_bank_accounts()`, `list_transactions()` - Banking
- `get_stats()` - Usage statistics

### v2.2.0: Batch Operations
```python
# Batch create contacts
contacts_data = [
    {"name": "John Doe", "email": "john@example.com"},
    {"name": "Jane Smith", "email": "jane@example.com"},
]
result = client.batch_create_contacts(contacts_data)
print(f"Created {result.success_count} contacts in {result.duration_ms}ms")

# Batch create invoices
invoices_data = [
    {"contact_id": "123", "items": [{"name": "Item 1", "price": 100}]},
    {"contact_id": "456", "items": [{"name": "Item 2", "price": 200}]},
]
result = client.batch_create_invoices(invoices_data)

# Batch update invoice status
result = client.batch_update_invoice_status(
    ["inv1", "inv2", "inv3"],
    InvoiceStatus.PAID
)
```

### v2.2.0: Health Check
```python
health = client.health_check(timeout=5.0)
if health.healthy:
    print(f"✅ API responsive in {health.response_time_ms:.1f}ms")
else:
    print(f"❌ {health.message}")
```

### v2.2.0: Webhooks
```python
from sevdesk_v2 import WebhookEvent

# Register webhook
webhook = client.create_webhook(
    url="https://myapp.com/webhook",
    events=[WebhookEvent.CONTACT_CREATED, WebhookEvent.INVOICE_CREATED],
    name="My Integration"
)

# List webhooks
webhooks = client.list_webhooks()

# Delete webhook
client.delete_webhook("webhook_id")

# Verify webhook signature (in your webhook handler)
import requests
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    signature = request.headers.get('X-SevDesk-Signature')
    if client.verify_webhook_signature(request.data, signature):
        # Process webhook
        client.webhook_handler.process_webhook(
            request.headers.get('X-SevDesk-Event'),
            request.json
        )
        return '', 200
    return 'Invalid signature', 401
```

### v2.2.0: Export/Import
```python
# Export to CSV
csv_content = client.export_contacts_csv()
# or save to file
client.export_contacts_csv(filename="contacts.csv")

# Export invoices with filters
client.export_invoices_csv(
    filename="invoices.csv",
    status="open",
    start_date="2024-01-01"
)

# Import from CSV
csv_data = """id,name,email
,John Doe,john@example.com
,Jane Smith,jane@example.com"""

result = client.import_contacts_csv(csv_data)
print(f"Imported {result.success_count} contacts")

# Dry run to validate
dry_result = client.import_contacts_csv(csv_data, dry_run=True)
```

### v2.2.0: Operation Queue
```python
# Initialize with persistence
client = SevDeskClient(
    queue_persist_path="~/.sevdesk/queue.json"
)

# Queue operations for offline execution
client.queue_operation("create_contact", {
    "name": "Queued Contact",
    "email": "queued@example.com"
})

# Check queue status
status = client.get_queue_status()
print(f"{status['queued_operations']} operations queued")

# Process all queued operations
result = client.process_queue()
print(f"Processed {result.success_count}/{result.total}")

# Clear queue
client.clear_queue()
```

## Changelog

### v2.2.0 (Feb 2026) 🚀
**New Features:**
- **Batch Operations** - Concurrent bulk create/update for contacts and invoices
- **Health Monitoring** - API connectivity checks with detailed diagnostics
- **Webhook Support** - Full webhook lifecycle management with signature verification
- **CSV Export/Import** - Complete data portability
- **Operation Queue** - Offline operation buffering with disk persistence
- **Async Processing** - ThreadPoolExecutor for parallel operations

**Improvements:**
- Added `WebhookEvent` enum for all supported webhook types
- Added `BatchResult` dataclass for batch operation results
- Added `HealthStatus` dataclass for health check results
- Added `WebhookHandler` class for webhook processing
- Added `OperationQueue` class for offline operation management
- Enhanced CLI with new commands for all v2.2.0 features

### v2.1.0 (Feb 2026)
- Added TTL-based caching
- Replaced sys.argv with argparse
- Added enums for all status codes
- Added response metadata tracking
- Added config file support
- Improved error messages with suggestions

### v2.0.0 (Feb 2026)
- Added circuit breaker pattern
- Added retry logic with exponential backoff
- Added input validation decorators
- Added pagination support
- Added comprehensive test suite

### v1.0.0 (Feb 2026)
- Initial release
- Basic CRUD operations for contacts, invoices, vouchers
- Banking integration
