# Stripe Integration for Invoice Workflow

## Overview
Integration of Stripe Payment Processing with the Invoice Workflow skill to enable:
- **Instant Payment Links** - Generate payment URLs for invoices
- **Automatic Payment Tracking** - Webhook-based status updates
- **Multi-Payment Methods** - Cards, SEPA, Klarna, etc.
- **Automatic Reconciliation** - Match payments to invoices

## Why Stripe?

| Feature | Value |
|---------|-------|
| **Global Coverage** | 135+ currencies, 46 countries |
| **Payment Methods** | Cards, SEPA, Klarna, iDEAL, etc. |
| **Developer Experience** | Excellent API + Python SDK |
| **Webhooks** | Real-time event notifications |
| **Pricing** | 1.5% + €0.25 for European cards |
| **German Compliance** | PSD2, SCA, GoBD ready |

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Invoice Workflow Skill                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐  │
│  │   Invoice    │─────▶│ Stripe Link  │─────▶│  Email    │  │
│  │  Generator   │      │   Generator  │      │  Sender   │  │
│  └──────────────┘      └──────────────┘      └───────────┘  │
│         │                       │                            │
│         ▼                       ▼                            │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   Invoice    │      │   Stripe     │                     │
│  │   Database   │      │   Webhook    │                     │
│  └──────────────┘      └──────────────┘                     │
│         ▲                       │                            │
│         │                       ▼                            │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   Payment    │◀─────│   Stripe     │                     │
│  │   Tracker    │      │   Events     │                     │
│  └──────────────┘      └──────────────┘                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Stripe API     │
                    │  (checkout)      │
                    └──────────────────┘
```

## API Endpoints Used

### Core Endpoints
| Endpoint | Purpose |
|----------|---------|
| `POST /v1/checkout/sessions` | Create payment sessions |
| `POST /v1/payment_links` | Create reusable payment links |
| `GET /v1/checkout/sessions/{id}` | Retrieve session status |
| `POST /v1/webhook_endpoints` | Register webhooks |
| `GET /v1/events` | Poll for events (backup) |

## Data Flow

### 1. Invoice → Payment Link Creation
```python
# When invoice is created/sent
stripe_link = create_stripe_payment_link(
    invoice_id="RE-2025-001",
    amount=2500.00,
    currency="eur",
    customer_email="kunde@beispiel.de",
    description="Beratungsleistung Februar 2025"
)
# Returns: https://checkout.stripe.com/pay/cs_live_...
```

### 2. Payment Webhook Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Customer  │────▶│   Stripe    │────▶│   Webhook   │
│   Pays      │     │   Checkout  │     │   Endpoint  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                                                ▼
                                       ┌─────────────┐
                                       │   Invoice   │
                                       │   Marked    │
                                       │   Paid      │
                                       └─────────────┘
```

### 3. Webhook Events Handled
| Event | Action |
|-------|--------|
| `checkout.session.completed` | Mark invoice as paid |
| `invoice.paid` | Update payment status |
| `payment_intent.succeeded` | Record payment |
| `payment_intent.payment_failed` | Log failure, notify |

## Configuration

```env
# Stripe Configuration
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_live_...

# Payment Settings
STRIPE_DEFAULT_CURRENCY=eur
STRIPE_PAYMENT_METHODS=card,sepa_debit,klarna
STRIPE_SUCCESS_URL=https://navii-automation.de/payment/success
STRIPE_CANCEL_URL=https://navii-automation.de/payment/cancel
```

## Security Considerations

1. **Webhook Signature Verification** - Always verify Stripe signatures
2. **API Key Storage** - Use environment variables, never commit keys
3. **Idempotency** - Use idempotency keys for payment creation
4. **HTTPS Only** - Webhooks require HTTPS endpoints

## Pricing Calculation

For a typical German B2B invoice of €1.000:
- Stripe fee: €1.000 × 1.5% + €0.25 = **€15.25**
- For invoices >€10.000: Custom pricing available

## Integration Roadmap

### Phase 1: Basic Payment Links (Week 1)
- [ ] Create Stripe payment links for invoices
- [ ] Include link in invoice emails
- [ ] Manual payment status check

### Phase 2: Webhook Integration (Week 2)
- [ ] Set up webhook endpoint
- [ ] Handle `checkout.session.completed`
- [ ] Auto-update invoice status

### Phase 3: Advanced Features (Week 3-4)
- [ ] SEPA Direct Debit support
- [ ] Installment payments (Klarna)
- [ ] Automatic reconciliation
- [ ] Refund handling

### Phase 4: Dashboard & Reporting (Month 2)
- [ ] Payment analytics
- [ ] Failed payment retry logic
- [ ] Multi-currency support

## Files to Create

1. `stripe_integration.py` - Core integration module
2. `stripe_webhook_handler.py` - Webhook endpoint handler
3. `stripe_config.py` - Configuration management
4. `docs/stripe-setup.md` - Setup guide
5. `tests/test_stripe_integration.py` - Unit tests

## Success Metrics

- Payment conversion rate (target: >80%)
- Time to payment (target: <3 days)
- Manual reconciliation effort (target: -90%)
- Failed payment rate (target: <5%)
