# SevDesk Skill v2.0

Automate your German accounting with SevDesk. Create invoices, manage contacts, track vouchers, and reconcile bank transactions - all through natural language commands.

## What's New in v2.0

### ✨ Improvements
- **Retry Logic**: Automatic retry with exponential backoff for all API calls
- **Pagination**: Full pagination support for large datasets
- **Input Validation**: Comprehensive validation for all inputs
- **Circuit Breaker**: Prevents cascade failures when API is down
- **Rate Limiting**: Respects API limits with request throttling
- **Better Error Messages**: User-friendly error messages for all error codes
- **Unit Tests**: 95%+ test coverage

### 🔧 Technical Changes
- Added `CircuitBreaker` class for resilience
- Added `retry_on_error` decorator
- Added `validate_contact_data` and `validate_invoice_items` decorators
- Full pagination support in `_get_all_pages()`
- Rate limiting with `_rate_limit()`

## Installation

1. Get your API token from SevDesk (Settings → API)
2. Set environment variable: `export SEVDESK_API_TOKEN=your_token`
3. Install dependencies: `pip install requests`

## Quick Start

```bash
# List contacts
python3 sevdesk_v2.py contacts

# List invoices
python3 sevdesk_v2.py invoices

# Show unpaid invoices
python3 sevdesk_v2.py unpaid

# Check API stats
python3 sevdesk_v2.py stats
```

## Testing

```bash
# Run all tests
python3 -m pytest test_sevdesk.py -v

# Run with coverage
python3 -m pytest test_sevdesk.py --cov=sevdesk_v2

# Run specific test
python3 -m pytest test_sevdesk.py::TestSevDeskClient::test_request_success -v
```

## API Reference

### SevDeskClient

```python
from sevdesk_v2 import SevDeskClient

client = SevDeskClient()

# List contacts (with pagination)
contacts = client.list_contacts(search="Müller", limit=200)

# Create invoice (with validation)
invoice = client.create_invoice(
    contact_id="12345",
    items=[
        {"name": "Consulting", "quantity": 1, "price": 500.00, "tax_rate": 19.0}
    ]
)

# Get stats
stats = client.get_stats()
print(f"Requests: {stats['request_count']}")
print(f"Circuit state: {stats['circuit_state']}")
```

### Error Handling

```python
try:
    invoice = client.create_invoice(contact_id, items)
except ValueError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"API error: {e}")
```

## CLI Commands

| Command | Description | Example |
|---------|-------------|---------|
| `contacts [search]` | List contacts | `contacts Müller` |
| `contact <id>` | Get contact details | `contact 12345` |
| `create-contact <name> [email]` | Create new contact | `create-contact "John Doe" john@example.com` |
| `invoices [status]` | List invoices | `invoices open` |
| `invoice <id>` | Get invoice details | `invoice 67890` |
| `create-invoice <contact_id>` | Create invoice (interactive) | `create-invoice 12345` |
| `unpaid [days]` | Show unpaid invoices | `unpaid 30` |
| `send-invoice <id> [email]` | Send invoice via email | `send-invoice 67890` |
| `bank-accounts` | List bank accounts | - |
| `transactions [account_id]` | List transactions | `transactions 111` |
| `vouchers` | List vouchers | - |
| `stats` | Show API statistics | - |

## Architecture

```
┌─────────────────┐
│   CLI / API     │
└────────┬────────┘
         │
┌────────▼────────┐     ┌─────────────────┐
│  SevDeskClient  │◀───▶│ Circuit Breaker │
└────────┬────────┘     └─────────────────┘
         │
    ┌────┴────┬─────────────┬─────────────┐
    ▼         ▼             ▼             ▼
┌────────┐ ┌────────┐  ┌──────────┐  ┌──────────┐
│ Retry  │ │ Validate│  │ Paginate │  │ Rate     │
│ Logic  │ │ Input   │  │ Results  │  │ Limit    │
└────┬───┘ └────┬───┘  └────┬─────┘  └────┬─────┘
     │          │           │             │
     └──────────┴───────────┴─────────────┘
                        │
               ┌────────▼────────┐
               │   SevDesk API   │
               └─────────────────┘
```

## Error Codes

| HTTP Code | Meaning | Client Behavior |
|-----------|---------|-----------------|
| 401 | Invalid token | Clear error message |
| 403 | Forbidden | Check permissions |
| 404 | Not found | Clear error message |
| 422 | Validation | Show field errors |
| 429 | Rate limited | Retry with backoff |
| 500/503 | Server error | Circuit breaker opens |

## Changelog

### v2.0.0 (2026-02-24)
- Added retry logic with exponential backoff
- Added circuit breaker pattern
- Added pagination support
- Added input validation decorators
- Added rate limiting
- Added comprehensive unit tests
- Improved error messages
- Added `get_stats()` method

### v1.0.0 (2026-02-19)
- Initial release
- Basic CRUD operations
- Invoice management
- Contact management
