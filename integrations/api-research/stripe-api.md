# Stripe API Integration - Prototype

## Overview
Payment Automation für Subscription-Business und E-Commerce. Diese Integration ermöglicht:
- Automatische Rechnungsstellung
- Subscription Management
- Failed Payment Recovery
- Revenue Reporting

## API Basics

### Base URL
```
https://api.stripe.com/v1/
```

### Authentication
- **Typ**: API Key (sk_live_... / sk_test_...)
- **Header**: `Authorization: Bearer {api_key}`
- **Test Mode**: Alle API calls mit test keys sind sandboxed

### Rate Limits
- **Read**: 100 requests/second
- **Write**: 100 requests/second
- **Burst**: 150 requests/second

## Core Resources

### Customers
```bash
# Create customer
curl https://api.stripe.com/v1/customers \
  -u sk_test_...: \
  -d email="customer@example.com" \
  -d name="Max Mustermann"

# List customers
curl https://api.stripe.com/v1/customers?limit=100 \
  -u sk_test_...:
```

### Payment Intents
```bash
# Create payment intent
curl https://api.stripe.com/v1/payment_intents \
  -u sk_test_...: \
  -d amount=2000 \
  -d currency=eur \
  -d customer=cus_...

# Confirm payment
curl https://api.stripe.com/v1/payment_intents/{id}/confirm \
  -u sk_test_...:
```

### Subscriptions
```bash
# Create subscription
curl https://api.stripe.com/v1/subscriptions \
  -u sk_test_...: \
  -d customer=cus_... \
  -d "items[0][price]"=price_... \
  -d payment_behavior=default_incomplete
```

### Invoices
```bash
# Create invoice
curl https://api.stripe.com/v1/invoices \
  -u sk_test_...: \
  -d customer=cus_...

# Finalize and send
curl https://api.stripe.com/v1/invoices/{id}/finalize \
  -u sk_test_...:
```

## Use Cases für Navii Kunden

### 1. Automatische Rechnung bei Zahlungseingang
```
Trigger: stripe.payment_intent.succeeded
Action: Create invoice in sevDesk
```

### 2. Failed Payment Recovery
```
Trigger: stripe.invoice.payment_failed
Action: Send dunning email sequence
          -> Wait 3 days
          -> Retry payment
          -> Escalate if still failed
```

### 3. Subscription Analytics
```
Daily sync:
- MRR (Monthly Recurring Revenue)
- Churn Rate
- LTV calculations
-> Push to Google Sheets / Dashboard
```

### 4. Steuer-Reporting
```
Monthly:
- Export all transactions
- Calculate VAT by country
- Generate Steuerberater-Report
```

## Webhooks (Critical!)

### Required Endpoints
```
- payment_intent.succeeded
- payment_intent.payment_failed
- invoice.payment_failed
- invoice.paid
- customer.subscription.created
- customer.subscription.updated
- customer.subscription.deleted
- charge.refunded
```

### Webhook Security
```python
import stripe

# Verify webhook signature
payload = request.body
sig_header = request.headers['Stripe-Signature']
event = stripe.Webhook.construct_event(
    payload, sig_header, webhook_secret
)
```

## German Market Specifics

### SEPA Direct Debit
```bash
# Create SEPA payment method
curl https://api.stripe.com/v1/payment_methods \
  -u sk_test_...: \
  -d type=sepa_debit \
  -d "sepa_debit[iban]"=DE89370400440532013000
```

### SEPA Mandate References
- Pflichtfeld für SEPA-Lastschrift
- Format: [Firmenkuerzel]-[Kundennummer]-[Datum]
- Beispiel: NAVII-12345-20240224

### VAT Handling
```javascript
// German VAT (19%) on invoice
const invoice = await stripe.invoices.create({
  customer: 'cus_...',
  default_tax_rates: ['txr_...'], // 19% MwSt
});
```

## Error Handling

### Common Errors
- `card_declined` - Karte abgelehnt
- `insufficient_funds` - Nicht genug Guthaben
- `expired_card` - Karte abgelaufen
- `incorrect_cvc` - Falsches CVC

### Retry Strategy
```python
# Exponential backoff for rate limits
time.sleep(2 ** attempt)
```

## Test Cards

### Success
```
4242 4242 4242 4242
Any future date, any CVC
```

### Decline
```
4000 0000 0000 0002 (Generic decline)
4000 0000 0000 9995 (Insufficient funds)
4000 0000 0000 9987 (Lost card)
```

### SEPA
```
DE89370400440532013000 (Success)
DE62370400440532013001 (Failure)
```

## Status
🟡 PROTOTYPE - Ready for testing
