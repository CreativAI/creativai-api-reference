# Errors & Retries

## Response Shape

Every response follows a consistent success/error envelope:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Collection col_xxx not found",
    "details": { "collection_id": "col_xxx" },
    "timestamp": "2026-05-26T10:00:00Z"
  }
}
```

When `success` is `true`, `error` is `null`. When `success` is `false`, `data` is `null`.

---

## HTTP Status Codes

| Status | Meaning | Typical Cause |
|--------|---------|---------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Async job started; poll with the returned job ID |
| 207 | Multi-Status | Partial success in a batch operation |
| 400 | Bad Request | Malformed body, missing required field, or invalid parameter |
| 401 | Unauthorized | API key missing or invalid |
| 403 | Forbidden | Valid key, but caller lacks the required role |
| 404 | Not Found | Collection, plate, job, or user does not exist |
| 409 | Conflict | Duplicate resource or illegal state transition |
| 422 | Unprocessable Entity | Semantic validation failure (e.g., wrong field type) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server-side failure |
| 503 | Service Unavailable | Dependency temporarily down |

---

## Application Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `FORBIDDEN` | 403 | Caller lacks required collection role |
| `NOT_FOUND` | 404 | Requested resource does not exist |
| `BAD_REQUEST` | 400 | Validation error in request body or params |
| `CONFLICT` | 409 | Resource already exists or state conflict |
| `TIER_LIMIT` | 403 | Plan quota reached (collections, storage, etc.) |
| `INSUFFICIENT_CREDITS` | 402 | Not enough AI credits for the operation |
| `RATE_LIMITED` | 429 | Too many requests in a short window |
| `PARTIAL_SUCCESS` | 207 | Batch operation where some items succeeded |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server failure |

---

## Common Error Scenarios

### `TIER_LIMIT`

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "TIER_LIMIT",
    "message": "Maximum number of collections reached for your plan",
    "details": { "current": 3, "limit": 3, "plan": "free" },
    "timestamp": "2026-05-26T10:00:00Z"
  }
}
```

**Fix:** Delete unused collections or upgrade your subscription at `/api/v2/subscriptions/checkout`.

### `INSUFFICIENT_CREDITS`

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INSUFFICIENT_CREDITS",
    "message": "Insufficient credits. Required: 26.4, available: 5.2",
    "details": { "required": 26.4, "available": 5.2 },
    "timestamp": "2026-05-26T10:00:00Z"
  }
}
```

**Fix:** Check balance with `GET /api/v2/transactions/summary`. Use `POST /api/v2/indexing/chunk-based/estimate-cost` to verify cost before submitting.

### `UNAUTHORIZED`

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

**Fix:** Ensure you're sending `X-API-Key: sk_live_...` in the request header. Verify the key at `GET /api/v2/users/api-key-check`.

### `BAD_REQUEST` — preprocessing not complete

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Cannot start indexing: preprocessing is not complete",
    "details": { "preprocessing_status": "processing" },
    "timestamp": "2026-05-26T10:00:00Z"
  }
}
```

**Fix:** Poll `GET /api/v2/indexing/preprocessing-status/{collection_id}` until `can_start_indexing: true`.

---

## Retry Guidance

### Retryable Errors

Always safe to retry with backoff:

| Status | Error Code |
|--------|-----------|
| 429 | `RATE_LIMITED` |
| 500 | `INTERNAL_SERVER_ERROR` |
| 502 | Bad Gateway |
| 503 | Service Unavailable |
| 504 | Gateway Timeout |

### Do Not Retry

These indicate a client-side problem that retrying will not fix:

| Status | Error Code | Reason |
|--------|-----------|--------|
| 400 | `BAD_REQUEST` | Fix the request body |
| 401 | `UNAUTHORIZED` | Fix or rotate API key |
| 403 | `FORBIDDEN` / `TIER_LIMIT` | Adjust permissions or plan |
| 404 | `NOT_FOUND` | Verify resource IDs |
| 409 | `CONFLICT` | State issue — check current resource state |
| 422 | `UNPROCESSABLE_ENTITY` | Fix field type or value |

---

## Exponential Backoff with Jitter

Use exponential backoff with random jitter for all retryable errors.

```
delay = min(base * 2^attempt, max_delay) + random(0, jitter_max)
```

**Example sequence (seconds):** `1.2, 2.6, 5.1, 10.4, 20.3, 30 (cap)`

```python
import time, random, requests

def call_with_retry(url, headers, max_attempts=5):
    base = 1.0
    max_delay = 30.0
    
    for attempt in range(max_attempts):
        resp = requests.get(url, headers=headers, timeout=30)
        
        if resp.status_code not in (429, 500, 502, 503, 504):
            return resp  # success or non-retryable error
        
        if attempt == max_attempts - 1:
            raise Exception(f"Max retries exceeded: {resp.status_code}")
        
        delay = min(base * (2 ** attempt), max_delay) + random.uniform(0, 0.3 * base)
        time.sleep(delay)
```

```bash
# Bash retry loop example
retry_curl() {
  local URL=$1; local MAX=5; local ATTEMPT=0; local DELAY=1
  while [ $ATTEMPT -lt $MAX ]; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL" -H "X-API-Key: $CREATIVAI_API_KEY")
    [ "$STATUS" -lt 500 ] && [ "$STATUS" -ne 429 ] && return 0
    ATTEMPT=$((ATTEMPT + 1))
    DELAY=$((DELAY * 2))
    sleep $DELAY
  done
  return 1
}
```

---

## Polling Async Jobs

For long-running jobs, poll with a reasonable interval rather than tight loops.

| Operation | Recommended poll interval |
|-----------|--------------------------|
| Preprocessing status | Every 15 seconds |
| Indexing status | Every 15–30 seconds |
| Plate creation | Every 5 seconds |
| Knowledge extraction | Every 10 seconds |
| Online / YouTube search | Every 10 seconds |
| S3 Transfer | Every 30 seconds |

---

## Observability Best Practices

- **Add a request ID** to each outbound call (e.g. `X-Request-Id: uuid`) — log it and include it in support requests
- **Log the response envelope** — always record `success`, `error.code`, HTTP status, and latency
- **Persist job IDs** — store `indexing_id`, `job_id`, `session_id` in your database so you can resume or inspect failed runs
- **Set timeouts** — use 30s for most calls; 10 min for SSE streaming connections
