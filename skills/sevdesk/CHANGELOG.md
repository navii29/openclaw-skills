# Changelog - SevDesk Skill v2.1

## Summary
Major refactoring of the SevDesk skill with focus on code quality, maintainability, and new features.

## Changes Made

### 1. Added Enums for Magic Numbers (HIGH IMPACT)
**Problem:** Status codes, category IDs, and type codes were hardcoded as magic numbers throughout the codebase.

**Solution:** Introduced proper Python enums:
- `InvoiceStatus` (DRAFT=100, OPEN=200, PARTIAL=750, PAID=1000)
- `ContactCategory` (CUSTOMER=3, SUPPLIER=4, PARTNER=5)
- `InvoiceType` (INVOICE="RE", ADVANCE="AR", PARTIAL="TR", FINAL="ER", CREDIT="GS")
- `VoucherStatus` (DRAFT=100, OPEN=200, PARTIAL=750, PAID=1000)

**Benefits:**
- Type safety and IDE autocomplete
- Self-documenting code
- No risk of typos in status codes
- Easier maintenance

### 2. Replaced sys.argv with argparse (HIGH IMPACT)
**Problem:** CLI used manual sys.argv parsing which is error-prone and doesn't provide help text.

**Solution:** Full argparse implementation with:
- Subcommands with dedicated help
- Type validation for arguments
- Global flags (--token, --no-cache, --verbose, --version)
- Consistent help text and examples
- Better error messages

**New CLI usage:**
```bash
sevdesk contacts --search "Müller" --limit 50
sevdesk invoices --status open --start-date 2024-01-01
sevdesk stats --clear-cache
```

### 3. Added TTL-based Caching (MEDIUM IMPACT)
**Problem:** Every API call hit the server, even for repeated identical requests.

**Solution:** Implemented `SimpleCache` class:
- Configurable TTL (default 5 minutes)
- Cache statistics tracking
- Automatic expiration
- Optional per-request cache bypass

**Usage:**
```python
client = SevDeskClient(enable_cache=True, cache_ttl=300)
client.clear_cache()  # Manual clear
stats = client.get_stats()  # Shows cache hit rate
```

### 4. Added Response Metadata Tracking (MEDIUM IMPACT)
**Problem:** No visibility into API performance or rate limits.

**Solution:** `ResponseMetadata` dataclass tracking:
- Request count
- Cache hits/misses
- Response duration (ms)
- Rate limit headers (if provided by API)

### 5. Improved Error Messages (MEDIUM IMPACT)
**Problem:** Generic error messages without actionable guidance.

**Solution:** Enhanced `_parse_http_error()` with:
- User-friendly error descriptions
- Suggested fixes for common errors
- Specific handling for all HTTP status codes

**Example:**
```
Before: "API Error 401: 401 Unauthorized"
After:  "Invalid API token (401): Check your SEVDESK_API_TOKEN environment variable."
```

### 6. Added Config File Support (LOW IMPACT)
**Problem:** Token could only be provided via environment variable.

**Solution:** Support for JSON config files:
- Default paths: `sevdesk.json`, `~/.sevdesk/config.json`
- Custom path via `config_path` parameter
- Falls back to env var if config not found

**Example config:**
```json
{
  "api_token": "your_token_here"
}
```

### 7. Code Quality Improvements
- **Type hints:** Added proper type hints throughout (Dict, List, Optional, etc.)
- **Constants:** Moved magic strings/numbers to module-level constants
- **Docstrings:** Enhanced with Args/Returns sections
- **Formatting methods:** Moved to instance methods for consistency

### 8. Test Coverage
**Added tests for:**
- All new enum classes
- Cache functionality (expiration, stats, clearing)
- Response metadata
- Rate limit extraction
- Config file loading
- CLI argument parsing (implicit via argparse)

**Total:** 44 test cases

## Files Modified
1. `sevdesk_v2.py` - Main implementation (rewritten)
2. `test_sevdesk.py` - Updated tests (+15 new tests)
3. `SKILL.md` - Documentation (to be updated)

## Backward Compatibility
⚠️ **Breaking Changes:**
- CLI now uses argparse instead of positional args
- Some internal method signatures tightened with type hints

✅ **Compatible:**
- All API methods remain functionally identical
- Environment variable auth unchanged
- All existing functionality preserved

## Migration Guide

### CLI Changes
```bash
# Old:
python sevdesk.py contacts "Müller"
python sevdesk.py create-invoice 12345

# New:
python sevdesk.py contacts --search "Müller"
python sevdesk.py create-invoice 12345
```

### Code Changes
```python
# Old:
from sevdesk_v2 import SevDeskClient
client = SevDeskClient()

# New (still works):
from sevdesk_v2 import SevDeskClient, InvoiceStatus
client = SevDeskClient(enable_cache=True)
# Use InvoiceStatus.DRAFT instead of 100
```

## Performance Improvements
- **Caching:** Reduces API calls for repeated identical requests
- **Connection reuse:** Better HTTP session handling
- **Request metadata:** Visibility into performance bottlenecks

## Version
**v2.1.0** - February 24, 2026

---
*Refactored by Navii Automation*
