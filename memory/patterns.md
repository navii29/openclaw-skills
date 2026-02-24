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

