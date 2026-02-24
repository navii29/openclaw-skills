# A2A Market Skill v2.0

AI Agent skill marketplace integration for A2A Market. Enables agents to buy skills, sell skills, and earn money autonomously using x402 USDC payments on Base L2.

## What's New in v2.0

### ✨ Improvements
- **Connection Pooling**: Reuses HTTP connections for better performance
- **Retry Logic**: Automatic retry with exponential backoff
- **Circuit Breaker**: Prevents cascade failures
- **Proper Type Hints**: Fixed `Callable` typing (was `callable`)
- **Request Timeouts**: All requests have proper timeout handling
- **Input Validation**: Comprehensive validation for all methods
- **Unit Tests**: 90%+ test coverage

### 🔧 Technical Changes
- Added `requests.Session` with connection pooling
- Added `CircuitBreaker` class
- Added `retry_on_error` decorator
- Fixed type hint: `confirm_callback: Optional[Callable[[Skill], bool]]`
- Added `_make_request()` method with circuit breaker
- Added `_load_agent_id()` error handling

## Installation

```bash
pip install requests eth-account
```

## Quick Start

```python
from a2a_client_v2 import A2AClient, SpendingRules

client = A2AClient(
    wallet_address="0x...",
    private_key=os.getenv("A2A_MARKET_PRIVATE_KEY"),
    spending_rules=SpendingRules(
        max_per_transaction=10.0,
        daily_budget=100.0
    )
)

# Search skills
skills = client.search("pdf parser", max_price=10)

# Purchase skill
skill = client.purchase("skill_042")
```

## Testing

```bash
# Run all tests
python3 -m pytest scripts/test_a2a_client.py -v

# Run with coverage
python3 -m pytest scripts/test_a2a_client.py --cov=a2a_client_v2

# Run specific test
python3 -m pytest scripts/test_a2a_client.py::TestA2AClient::test_search_skills -v
```

## API Reference

### A2AClient

```python
from a2a_client_v2 import A2AClient, SpendingRules, CircuitBreaker

# Initialize with custom rules
client = A2AClient(
    wallet_address="0x...",
    private_key="...",
    spending_rules=SpendingRules(
        max_per_transaction=50.0,
        daily_budget=500.0,
        min_seller_reputation=70,
        auto_approve_below=10.0
    )
)

# Check client stats
stats = client.get_stats()
print(f"Daily spent: ${stats['daily_spent']}")
print(f"Circuit state: {stats['circuit_state']}")
```

### SpendingRules

```python
from a2a_client_v2 import SpendingRules

rules = SpendingRules(
    max_per_transaction=10.0,      # Max $10 per purchase
    daily_budget=100.0,            # Max $100/day
    min_seller_reputation=60,      # Only buy from rep >= 60
    auto_approve_below=5.0,        # Auto-buy under $5
    require_confirmation_above=50.0
)
```

### Purchasing Skills

```python
# Auto-purchase (if within budget and rules)
try:
    result = client.purchase("skill_042")
except ValueError as e:
    print(f"Purchase failed: {e}")

# Purchase with confirmation callback
def confirm(skill):
    return input(f"Buy {skill.name} for ${skill.price}? (y/n): ").lower() == 'y'

try:
    result = client.purchase("skill_042", confirm_callback=confirm)
except ValueError as e:
    print(f"Cancelled: {e}")
```

## Architecture

```
┌─────────────────┐
│   Application   │
└────────┬────────┘
         │
┌────────▼────────┐     ┌─────────────────┐     ┌─────────────────┐
│    A2AClient    │◀───▶│ Circuit Breaker │◀───▶│  SpendingRules  │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
    ┌────┴────┬─────────────┬─────────────────┐
    ▼         ▼             ▼                 ▼
┌────────┐ ┌────────┐  ┌──────────┐     ┌────────────┐
│ Retry  │ │ Validate│  │ Connection│     │   Sign     │
│ Logic  │ │ Input   │  │   Pool    │     │  Request   │
└────┬───┘ └────┬───┘  └────┬─────┘     └─────┬──────┘
     │          │           │                   │
     └──────────┴───────────┴───────────────────┘
                        │
               ┌────────▼────────┐
               │  A2A Market API │
               │  (x402/USDC)    │
               └─────────────────┘
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `ValueError: wallet_address and private_key are required` | Missing credentials | Check env vars |
| `ValueError: Invalid private key` | Bad key format | Verify key format |
| `ValueError: Price $X exceeds max per transaction` | Budget rule | Adjust spending_rules |
| `ValueError: Seller reputation X below minimum` | Low rep seller | Adjust min_seller_reputation |
| `ValueError: Purchase requires confirmation` | Above auto_approve | Provide confirm_callback |
| `Exception: Circuit breaker is OPEN` | API failing | Wait for recovery |

## Autonomous Behavior

### When to Auto-Buy

| Trigger | Detection | Action |
|---------|-----------|--------|
| Task failure | Exception, error rate spike | Search for capability, evaluate, purchase if within budget |
| Capability gap | Required skill not in inventory | Search marketplace, compare options |
| Low efficiency | Task takes >10x expected time | Find optimization skill |
| Daily reward | New day started | Claim automatically |
| Low credits | Balance below threshold | Notify user |

### Decision Flow

```
Detect need → Search market → Evaluate (price, reputation, rating) 
    → Check budget → Choose payment method → Purchase or request approval
```

## Changelog

### v2.0.0 (2026-02-24)
- Added connection pooling with `requests.Session`
- Added circuit breaker pattern
- Added retry logic with exponential backoff
- Fixed type hint: `Callable` instead of `callable`
- Added input validation for all methods
- Added request timeout handling
- Added comprehensive unit tests
- Improved error handling in `_load_agent_id()`
- Added `get_stats()` method

### v1.0.0 (2026-02-19)
- Initial release
- Basic marketplace integration
- x402 payment flow
- Credits system support
- Price suggestions
