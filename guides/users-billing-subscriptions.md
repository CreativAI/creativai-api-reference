# Users, Billing & Subscriptions

Manage your account, API keys, credits, subscriptions, and payment history.

---

## Users

### Get Current User ID

```bash
curl "$CREATIVAI_BASE_URL/api/v2/users/me" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "usr_abc123"
  },
  "error": null
}
```

### Get Full Account Info

Returns credits, usage metrics, and storage stats.

```bash
curl "$CREATIVAI_BASE_URL/api/v2/users/me/info" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "usr_abc123",
    "credits": 150.0,
    "total_indexed_hours": 12.5,
    "search_requests": 248,
    "total_videos_analyzed": 1840,
    "total_images_analyzed": 96
  },
  "error": null
}
```

### Get Uploaded Hours

```bash
curl "$CREATIVAI_BASE_URL/api/v2/users/me/uploaded-hours" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_uploaded_hours": 18.3,
    "total_files_size_GB": 64.2
  },
  "error": null
}
```

### Verify API Key

```bash
curl "$CREATIVAI_BASE_URL/api/v2/users/api-key-check" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{ "success": true, "data": { "valid": true }, "error": null }
```

### Claim Welcome Credits

One-time bonus credits for new accounts.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/users/credits/claim-welcome" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "credits_added": 50.0,
    "new_balance": 50.0,
    "message": "Welcome credits claimed successfully"
  },
  "error": null
}
```

### Validate Credits for Indexing

Check whether you have enough credits before starting a job.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/users/credits/validate-indexing" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "user_credits": 150.0,
    "cost": 26.4,
    "files_to_be_indexed": ["s3://bucket/collections/col_xxx/uploads/sample.mp4"]
  },
  "error": null
}
```

---

## API Keys

API keys authenticate all API requests. See [authentication.md](authentication.md) for the full dashboard flow.

`/api/v2/api-keys` endpoints are for dashboard clients and require a Firebase ID token:

```bash
curl "$CREATIVAI_BASE_URL/api/v2/api-keys" \
  -H "Authorization: Bearer $FIREBASE_ID_TOKEN"
```

**Response:**
```json
{ "api_key": "sk_live_xxx" }
```

Create if missing:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/api-keys" \
  -H "Authorization: Bearer $FIREBASE_ID_TOKEN"
```

This call returns the existing key if one already exists.

---

## Transactions (Credit History)

### Summary (Balance + Totals)

```bash
curl "$CREATIVAI_BASE_URL/api/v2/transactions/summary" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "current_balance": 123.6,
    "total_credits_earned": 200.0,
    "total_credits_spent": 76.4,
    "storage_used_gb": 64.2,
    "storage_cost_per_gb": 0.05
  },
  "error": null
}
```

### Paginated Transaction List

```bash
curl "$CREATIVAI_BASE_URL/api/v2/transactions?page=1&page_size=20" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "transaction_id": "txn_abc123",
        "type": "debit",
        "category": "indexing",
        "amount": 26.4,
        "balance_after": 123.6,
        "description": "Indexing: 12 videos, 480 chunks",
        "collection_id": "col_xxx",
        "created_at": "2026-05-26T10:08:32Z"
      }
    ],
    "total": 48,
    "page": 1,
    "page_size": 20
  },
  "error": null
}
```

### Usage Breakdown

```bash
# By feature category
curl "$CREATIVAI_BASE_URL/api/v2/transactions/breakdown" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# By collection
curl "$CREATIVAI_BASE_URL/api/v2/transactions/breakdown/collections" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Export CSV
curl "$CREATIVAI_BASE_URL/api/v2/transactions/export" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -o transactions.csv
```

---

## Subscriptions

### List All Plans (public)

```bash
curl "$CREATIVAI_BASE_URL/api/v2/subscriptions/plans"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "plans": [
      {
        "plan_id": "free",
        "name": "Free",
        "price_monthly": 0,
        "credits_included": 50,
        "max_collections": 3,
        "max_storage_gb": 10
      },
      {
        "plan_id": "pro",
        "name": "Pro",
        "price_monthly": 49,
        "credits_included": 500,
        "max_collections": 50,
        "max_storage_gb": 500
      }
    ]
  },
  "error": null
}
```

### My Current Subscription

```bash
curl "$CREATIVAI_BASE_URL/api/v2/subscriptions/me" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "plan_id": "pro",
    "status": "active",
    "current_period_start": "2026-05-01T00:00:00Z",
    "current_period_end": "2026-06-01T00:00:00Z",
    "cancel_at_period_end": false
  },
  "error": null
}
```

### Create Stripe Checkout Session

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/subscriptions/checkout" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "pro",
    "success_url": "https://app.example.com/success",
    "cancel_url": "https://app.example.com/cancel"
  }'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plan_id` | string | Yes | Target plan ID (from `/subscriptions/plans`) |
| `success_url` | string | Yes | Redirect URL on successful payment |
| `cancel_url` | string | Yes | Redirect URL if user cancels checkout |

**Response:**
```json
{
  "success": true,
  "data": {
    "checkout_url": "https://checkout.stripe.com/pay/cs_test_...",
    "session_id": "cs_test_abc123"
  },
  "error": null
}
```

### Cancel Subscription

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/subscriptions/cancel" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Cancels at the end of the current billing period. `cancel_at_period_end` becomes `true`.

---

## Payments & Invoices

### Get Payment Status

```bash
curl "$CREATIVAI_BASE_URL/api/v2/payments/status/{payment_id}" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "payment_id": "pay_abc123",
    "status": "succeeded",
    "amount": 49.00,
    "currency": "usd",
    "credits_credited": 500,
    "created_at": "2026-05-01T10:00:00Z"
  },
  "error": null
}
```

### List Invoices

```bash
curl "$CREATIVAI_BASE_URL/api/v2/invoices" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "invoices": [
      {
        "invoice_id": "inv_abc123",
        "amount": 49.00,
        "currency": "usd",
        "status": "paid",
        "billing_period": "May 2026",
        "created_at": "2026-05-01T00:00:00Z"
      }
    ]
  },
  "error": null
}
```

### Download Invoice PDF

```bash
curl "$CREATIVAI_BASE_URL/api/v2/invoices/$INVOICE_ID/download" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -o invoice.pdf
```
