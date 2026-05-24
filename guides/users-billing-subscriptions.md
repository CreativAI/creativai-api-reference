# Users, Billing & Subscriptions

Manage your account, API keys, credits, subscriptions, and payment history.

---

## Users

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v2/users/me` | Get current user ID |
| GET | `/api/v2/users/me/uploaded-hours` | Total uploaded hours + storage used |
| GET | `/api/v2/users/me/info` | Full info: credits, hours, searches |
| GET | `/api/v2/users/api-key-check` | Check if current API key is valid (no auth required) |
| POST | `/api/v2/users/credits/claim-welcome` | Claim one-time welcome credits |
| POST | `/api/v2/users/credits/validate-indexing` | Check credit sufficiency for indexing |

### cURL Examples

```bash
# Who am I?
curl -X GET "$CREATIVAI_BASE_URL/api/v2/users/me" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Full account info
curl -X GET "$CREATIVAI_BASE_URL/api/v2/users/me/info" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Claim welcome credits (one-time)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/users/credits/claim-welcome" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## API Keys

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v2/api-keys` | List your API keys |
| POST | `/api/v2/api-keys` | Create a new API key |
| DELETE | `/api/v2/api-keys/{key_id}` | Revoke an API key |

---

## Transactions (Credit History)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v2/transactions` | Paginated transaction history |
| GET | `/api/v2/transactions/summary` | Balance, totals, storage |
| GET | `/api/v2/transactions/breakdown` | Usage by feature category |
| GET | `/api/v2/transactions/breakdown/collections` | Usage by collection |
| GET | `/api/v2/transactions/breakdown/plates` | Usage by data plate |
| GET | `/api/v2/transactions/breakdown/sessions` | Usage by agentic chat session |
| GET | `/api/v2/transactions/categories` | Valid filter categories |
| GET | `/api/v2/transactions/timeline` | Credit usage over time (for charts) |
| GET | `/api/v2/transactions/export` | Export CSV download |

```bash
# Credit balance and summary
curl -X GET "$CREATIVAI_BASE_URL/api/v2/transactions/summary" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Export transaction history
curl -X GET "$CREATIVAI_BASE_URL/api/v2/transactions/export" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -o transactions.csv
```

---

## Subscriptions

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v2/subscriptions/plans` | All plans (public) |
| GET | `/api/v2/subscriptions/pricing` | Token rates and price estimates (public) |
| GET | `/api/v2/subscriptions/me` | Current subscription |
| GET | `/api/v2/subscriptions/features` | Feature flags for current tier |
| GET | `/api/v2/subscriptions/features/all` | Feature matrix for all tiers (public) |
| GET | `/api/v2/subscriptions/storage-usage` | Storage used + projected cost |
| POST | `/api/v2/subscriptions/checkout` | Create Stripe checkout session |
| POST | `/api/v2/subscriptions/portal` | Open Stripe customer portal |
| POST | `/api/v2/subscriptions/cancel` | Cancel at end of billing period |
| GET | `/api/v2/subscriptions/billing/overdue-status` | Storage overdue status |

```bash
# View all subscription plans
curl -X GET "$CREATIVAI_BASE_URL/api/v2/subscriptions/plans"

# My current subscription
curl -X GET "$CREATIVAI_BASE_URL/api/v2/subscriptions/me" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Create a checkout session
curl -X POST "$CREATIVAI_BASE_URL/api/v2/subscriptions/checkout" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"plan_id": "pro", "success_url": "https://app.example.com/success", "cancel_url": "https://app.example.com/cancel"}'
```

---

## Payments & Invoices

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v2/payments/stripe-webhook` | Stripe event webhook (called by Stripe) |
| GET | `/api/v2/payments/status/{payment_id}` | Get payment status |
| GET | `/api/v2/payments/verify/{payment_id}` | Verify payment + credits credited |
| GET | `/api/v2/invoices` | List invoices |
| GET | `/api/v2/invoices/{invoice_id}` | Get invoice details |
| GET | `/api/v2/invoices/{invoice_id}/download` | Download invoice PDF |

```bash
# List invoices
curl -X GET "$CREATIVAI_BASE_URL/api/v2/invoices" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Download a specific invoice PDF
curl -X GET "$CREATIVAI_BASE_URL/api/v2/invoices/$INVOICE_ID/download" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -o invoice.pdf
```
