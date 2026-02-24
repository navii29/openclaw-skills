# SevDesk Skill

Automate your German accounting with SevDesk. Create invoices, manage contacts, track vouchers, and reconcile bank transactions - all through natural language commands.

**Version:** 2.1.0  
**Last Updated:** February 24, 2026

## Features

- ✅ **Smart Caching** - TTL-based response caching reduces API calls
- ✅ **Circuit Breaker** - Automatic failover on API issues
- ✅ **Retry Logic** - Exponential backoff for transient failures
- ✅ **Input Validation** - Decorator-based validation for all inputs
- ✅ **Type Safety** - Full type hints and enums for all status codes
- ✅ **Modern CLI** - argparse-based command-line interface
- ✅ **Rate Limit Tracking** - Monitor API usage and limits

## Quick Start

```python
from sevdesk_v2 import SevDeskClient, InvoiceStatus

# Initialize with caching enabled
client = SevDeskClient(enable_cache=True)

# List all contacts
contacts = client.list_contacts()

# Create an invoice (uses enums for type safety)
invoice = client.create_invoice(
    contact_id="12345",
    items=[{"name": "Consulting", "price": 500, "quantity": 1}],
    invoice_type=InvoiceType.INVOICE
)
```

## Installation

1. Get your API token from SevDesk (Settings → User → API Token)
2. Set environment variable: `export SEVDESK_API_TOKEN=your_token`
3. Or create config file `sevdesk.json`: `{"api_token": "your_token"}`

## CLI Usage

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

## API Reference

See `sevdesk_v2.py` for full API. Key methods:
- `list_contacts()`, `create_contact()` - Contact management
- `list_invoices()`, `create_invoice()`, `send_invoice_email()` - Invoicing
- `list_vouchers()`, `create_voucher()` - Expense tracking
- `list_bank_accounts()`, `list_transactions()` - Banking
- `get_stats()` - Usage statistics

## Changelog

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

