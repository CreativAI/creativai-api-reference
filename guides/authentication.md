# Authentication

## How to Get Your API Key

All API calls (except public endpoints like `/health`) require an API key.

### 1. Create an Account

Sign up at **[creativ-ai.com](https://creativ-ai.com)**. After email verification you will land on the Dashboard with a free-tier plan active and welcome credits already applied.

### 2. Copy Your API Key

Your API key is **automatically provisioned** on signup — there is nothing to create.

1. Click your **profile avatar** in the top-right corner to open the profile dropdown.
2. Scroll to the **API Key** section at the bottom of the dropdown.
3. Click **API Key** to expand and reveal the key.
4. Click the **copy icon** to copy it to your clipboard.

> Keys begin with `sk_live_`. Never commit API keys to source control.

The API key is also visible in the same way from the **account menu** at the bottom of the left sidebar.

### 3. Set Your Environment Variables

```bash
export CREATIVAI_BASE_URL="https://creativai-apis.com"
export CREATIVAI_API_KEY="<YOUR_API_KEY>"
```

### 4. Verify the Key

```bash
curl "$CREATIVAI_BASE_URL/api/v2/users/api-key-check" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Request:** `GET /api/v2/users/api-key-check` (no auth required — test from anywhere)

**Response (valid key):**
```json
{
  "success": true,
  "data": { "valid": true },
  "error": null
}
```

**Response (invalid key):**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing API key",
    "details": {},
    "timestamp": "2026-05-26T10:00:00Z"
  }
}
```

---

## Manage API Keys

### List All Keys

Returns key metadata (ID, name, created date). The secret value is never returned after creation.

```bash
curl "$CREATIVAI_BASE_URL/api/v2/api-keys" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "api_keys": [
      {
        "key_id": "key_abc123",
        "name": "dev-local",
        "created_at": "2026-05-01T09:00:00Z",
        "last_used_at": "2026-05-26T08:42:00Z"
      },
      {
        "key_id": "key_def456",
        "name": "ci-pipeline",
        "created_at": "2026-05-10T14:30:00Z",
        "last_used_at": null
      }
    ]
  },
  "error": null
}
```

### Create a New Key

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/api-keys" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "ci-pipeline"}'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Human-readable label for this key |

**Response:**
```json
{
  "success": true,
  "data": {
    "key_id": "key_ghi789",
    "name": "ci-pipeline",
    "api_key": "<YOUR_API_KEY>",
    "created_at": "2026-05-26T10:00:00Z"
  },
  "error": null
}
```

> Copy `api_key` from this response. It will not be shown again.

### Revoke a Key

```bash
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/api-keys/{key_id}" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": { "message": "API key revoked" },
  "error": null
}
```

---

## Using Your API Key

All authenticated endpoints accept the key in either of two headers:

```
X-API-Key: <YOUR_API_KEY>
Authorization: Bearer <YOUR_API_KEY>
```

Both are equivalent. `X-API-Key` is preferred for server-to-server calls.

### Example: Get Current User

```bash
curl "$CREATIVAI_BASE_URL/api/v2/users/me" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "usr_abc123",
    "email": "you@example.com"
  },
  "error": null
}
```

### Example: Get Account Info (Credits, Usage)

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
    "total_indexed_hours": 4.5,
    "search_requests": 128,
    "total_clips_analyzed": 340
  },
  "error": null
}
```

---

## Response Envelope

Every response (success or error) follows the same structure:

```json
{
  "success": true | false,
  "data": { ... } | null,
  "error": null | {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {},
    "timestamp": "2026-05-26T10:00:00Z"
  }
}
```

---

## HTTP Status Codes

| Status | Meaning | Retryable |
|--------|---------|-----------|
| 200 | Success | — |
| 201 | Resource created | — |
| 202 | Async job accepted | — |
| 207 | Partial success (some items failed) | — |
| 400 | Bad request / validation error | No |
| 401 | Missing or invalid API key | No |
| 403 | Valid key, insufficient permissions | No |
| 404 | Resource not found | No |
| 409 | Conflict (duplicate, wrong state) | No |
| 422 | Semantic validation failure | No |
| 429 | Rate limited | Yes — with backoff |
| 500 | Internal server error | Yes — with backoff |
| 503 | Service temporarily unavailable | Yes — with backoff |

### Application Error Codes

| Code | Meaning |
|------|---------|
| `UNAUTHORIZED` | Missing or invalid API key |
| `FORBIDDEN` | Valid key, but caller lacks required role |
| `NOT_FOUND` | Collection, plate, job, or user does not exist |
| `BAD_REQUEST` | Malformed body or missing required field |
| `CONFLICT` | Resource already exists or state conflict |
| `TIER_LIMIT` | Your plan's quota is reached (collections, storage, etc.) |
| `INSUFFICIENT_CREDITS` | Not enough AI credits to perform the operation |
| `RATE_LIMITED` | Too many requests in a short window |
| `PARTIAL_SUCCESS` | Batch operation — some items succeeded, some failed |

---

## Roles & Authorization

Collection-level access is governed by four roles:

| Role | Create/Delete | Upload/Index | Search/View | Invite Members |
|------|:---:|:---:|:---:|:---:|
| `admin` | ✅ | ✅ | ✅ | ✅ |
| `read_write` | ❌ | ✅ | ✅ | ❌ |
| `read_only` | ❌ | ❌ | ✅ | ❌ |
| `viewer` | ❌ | ❌ | ✅ | ❌ |

> `viewer` is a legacy alias for `read_only`. Use `read_only` in new integrations.

Collection owners always have `admin` rights. Invite members at a lower role to restrict what they can do.

---

## WebRTC Authentication (WHIP/WHEP)

Browser-based WebRTC (WHIP/WHEP) signaling cannot set custom request headers. Pass the API key as a query parameter instead:

```
POST /api/v2/live-stream/sessions/{session_id}/whip?token=YOUR_API_KEY
POST /api/v2/live-stream/sessions/{session_id}/whep?token=YOUR_API_KEY
```

Do not use this form for non-browser clients.

---

## Security Best Practices

- **Never embed API keys** in frontend JavaScript, mobile app binaries, or any client-side code
- **Store keys in environment variables** or a secrets manager (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager)
- **One key per environment** — maintain separate keys for development, staging, and production
- **Rotate keys periodically** — create a new key, update your configuration, then revoke the old key
- **Revoke compromised keys immediately** — use the dashboard or the `DELETE /api/v2/api-keys/{key_id}` endpoint
- **HTTPS only** — the API does not accept HTTP connections
- **Use least-privilege roles** — share collections with the minimum role needed; prefer `read_only` for consumers
