# Skill Building Patterns

## Wiederverwendbare Automation-Patterns

### Error Handling Pattern
```python
try:
    # Operation
except Exception as e:
    log_error(e)
    notify_admin()
    fallback_action()
```

### Config Loading Pattern
```python
def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    return config
```

### Database Pattern
```python
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
# ... operations ...
conn.commit()
conn.close()
```

## Integration Patterns

### API Integration
- Always use timeout
- Implement retry logic
- Cache responses

### Webhook Handler
- Verify signatures
- Queue processing
- Async handling

## Documentation Patterns
- README.md mit Features-Liste
- config.env.example
- install.sh für Setup
- Makefile für Commands

## Pricing Patterns
- €999-€1799 für B2B Tools
- Bundle-Rabatt 15-20%
- Agency-Guide für Reseller

---

## Advanced Patterns (Learned 2026-02-25)

### Retry with Exponential Backoff
```python
from functools import wraps
import time

def retry_on_error(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay * (2 ** attempt))
        return wrapper
    return decorator
```

### Pydantic Config Validation
```python
from pydantic import BaseSettings, Field

class SkillConfig(BaseSettings):
    provider: str = Field(..., regex='^(google|outlook|calendly|apple)$')
    working_hours_start: str = Field(default='09:00', regex='^\d{2}:\d{2}$')
    buffer_minutes: int = Field(default=15, ge=0, le=120)
    
    class Config:
        env_file = 'config.env'
```

### Structured JSON Logging
```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module
        })
```

### Health Check Pattern
```python
def health_check():
    """For monitoring and Docker HEALTHCHECK"""
    checks = {
        'config': os.path.exists(CONFIG_FILE),
        'database': check_db_connection(),
        'api': check_api_connection(),
    }
    return all(checks.values()), checks
```

### E-Rechnung (ZUGFeRD) Pattern
```python
# Hybrid PDF + XML Structure
# rechnung.pdf (human readable)
#   └── zugferd-invoice.xml (machine readable)
#       └── EN 16931 compliant data

Required fields (EN 16931):
- Invoice number, date, currency
- Seller: Name, address, VAT ID
- Buyer: Name, address
- Line items: Description, quantity, unit, price, VAT rate
- Payment terms
```

### Event-Driven Architecture (EDA)
```python
# Cron as Event Emitter
# sessions_spawn as Event Consumer
# Memory as Event Store
# Loose coupling enables scaling
```

### Saga Pattern for Workflows
```python
# Compensatable transactions
# Retry logic per step
# State machine in memory/sagas/
# Compensation chain on errors

Example: Invoice Processing Saga
1. Receive Invoice (PDF) → Comp: Delete
2. Extract Data (OCR) → Comp: Reset
3. Validate GoBD → Comp: Flag invalid
4. Create Booking → Comp: Delete booking
5. Archive Document → Comp: Restore
```

