# Webhook Tester

Test webhook endpoints with pre-built payloads for n8n, Make, Zapier, and custom integrations.

## Quick Start

```bash
# Test with simple payload
python3 webhook_tester.py https://your-webhook.com

# Test with lead payload
python3 webhook_tester.py https://n8n.cloud/hook/xxx -p lead

# List available payloads
python3 webhook_tester.py -l
```

## Payloads

| Payload | Use Case |
|---------|----------|
| `lead` | New lead notification |
| `contact` | Contact form submission |
| `order` | New order/purchase |
| `simple` | Basic connectivity test |

## Features

- 🚀 POST requests with JSON payloads
- 📊 Status code validation
- 🔄 Batch testing multiple URLs
- 📝 Response capture

## Integration Testing

### n8n
```bash
python3 webhook_tester.py https://navii-automation.app.n8n.cloud/webhook/test -p lead
```

### Make (Integromat)
```bash
python3 webhook_tester.py https://hook.make.com/xxx -p contact
```

### Zapier
```bash
python3 webhook_tester.py https://hooks.zapier.com/hooks/catch/xxx/ -p order
```

## Python API

```python
from webhook_tester import test_webhook

# Test a webhook
success = test_webhook(
    url="https://api.example.com/webhook",
    payload_name="lead"
)
```

## Use Cases

- ✅ Test CRM integrations
- ✅ Validate marketing automation
- ✅ Debug webhook failures
- ✅ Load testing endpoints
