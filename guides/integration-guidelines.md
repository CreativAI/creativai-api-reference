# Integration Guidelines

Best practices for building production-grade integrations with the CreativAI API.

---

## API Versioning

- All stable endpoints live at `/api/v2/`. Default to this unless a feature is explicitly documented under `/api/v3/`.
- **Use v3 for**: Sub-plates (`/api/v3/data-plates/sub-plates/...`) and Knowledge Extraction when you need the latest model capabilities.
- Pin client behavior to documented response fields. Do not rely on undocumented fields — they may change without notice.
- Follow the release notes and update this reference folder in lockstep with backend deploys.

---

## Authentication

- Generate **one API key per environment** (dev / staging / production). Never share keys across environments.
- Store keys in environment variables or a secrets manager (AWS Secrets Manager, HashiCorp Vault, GCP Secret Manager, Doppler).
- **Never** commit API keys to source control or embed them in client-side JavaScript, mobile bundles, or Docker images.
- Rotate keys on a schedule (quarterly for most apps; immediately after a suspected leak).
- Revoke compromised keys immediately via `DELETE /api/v2/api-keys/{key_id}`.

---

## Request Design

### Idempotency and Safety

- Treat all `POST` / `DELETE` / `PATCH` endpoints as stateful and potentially non-idempotent.
- For destructive operations (delete collection, remove member, abort upload) add a confirmation gate in your UI or CLI.
- Store returned identifiers (`job_id`, `indexing_id`, `session_id`, `plate_id`) durably so you can resume or inspect failed runs.

### Timeouts

Set timeouts on every outbound call:

| Call type | Recommended timeout |
|-----------|---------------------|
| Simple read (GET) | 15 seconds |
| Mutation (POST/PATCH/DELETE) | 30 seconds |
| Async job submission | 30 seconds |
| SSE streaming (Agentic Chat) | 10–15 minutes (or no timeout) |

### Content-Type

Always send `Content-Type: application/json` for POST/PATCH request bodies. Uploads to presigned S3 URLs must match the `content_type` declared when requesting the URL.

---

## Async Job Pattern

Most intensive operations are async. The canonical flow is:

```
1. POST to start endpoint → 202 Accepted + { "job_id": "..." }
2. Poll GET status endpoint every N seconds
3. On terminal state (completed/failed): proceed or handle error
```

**Best practices:**

- Persist `job_id` to your database before polling — if your process crashes you can resume.
- Use a polling interval appropriate to the operation (see [errors.md](errors.md#polling-async-jobs)).
- Implement a maximum wait timeout at the application level; surface a "taking longer than expected" message if exceeded.
- Never busy-loop — always `sleep` between polls.

```python
import time, requests

def poll_until_done(url, api_key, interval=15, max_wait=1800):
    headers = {"X-API-Key": api_key}
    deadline = time.time() + max_wait
    terminal = {"completed", "failed", "partial", "indexing_completed", "indexing_failed"}
    
    while time.time() < deadline:
        resp = requests.get(url, headers=headers, timeout=30).json()
        status = resp.get("data", {}).get("status", "unknown")
        if status in terminal:
            return resp
        time.sleep(interval)
    
    raise TimeoutError(f"Job did not complete within {max_wait}s")
```

---

## Retries and Backoff

Always implement exponential backoff with jitter for transient failures (`429`, `5xx`).

```
delay = min(base * 2^attempt, 30) + random(0, 0.3)
```

Do **not** retry `400`, `401`, `403`, `404`, or `422` — these indicate client errors that won't resolve on retry.

See [errors.md](errors.md) for the full retry reference.

---

## SSE (Server-Sent Events)

Agentic Chat uses SSE for streaming. Key considerations:

- Use `-N` (no-buffer) with curl: `curl -N -X POST ... -H "Accept: text/event-stream"`
- In JavaScript, use `fetch` with a `ReadableStream` reader (see [agentic-chat.md](agentic-chat.md)).
- If the connection drops while the agent is running, reconnect by POSTing with `{"message": ""}` — the server replays buffered events.
- Surface partial progress events in your UI (thinking, plan, node_enter/exit) so users see activity.
- Always expose an explicit **Stop** control; use `POST .../stop` when the user cancels.

---

## Rate Limits

CreativAI enforces per-user rate limits. If you hit `429`:

1. Read the `Retry-After` header if present.
2. Otherwise apply exponential backoff starting at 1 second.
3. Reduce concurrency — don't fan out more than 5 concurrent requests per user.
4. Cache read responses where appropriate (e.g., `/subscriptions/plans`, `/subscriptions/pricing`).

---

## Credit Management

Credits are deducted upfront for indexing and knowledge extraction jobs.

- **Always estimate before indexing**: `POST /api/v2/indexing/chunk-based/estimate-cost`
- **Check balance before large jobs**: `GET /api/v2/transactions/summary`
- **Validate in code**: `POST /api/v2/users/credits/validate-indexing`
- Set up monitoring: alert when balance drops below a threshold (e.g. 20% of monthly spend).

---

## Multi-Part Uploads

For files larger than 100 MB use multipart uploads:

1. Initiate with `POST /api/v2/collections/uploads/initiate` — specify `total_parts`
2. Upload each part (minimum 5 MB, except the last) via PUT to the part-specific presigned URL
3. Collect the `ETag` header from each PUT response
4. Complete with `POST /api/v2/collections/uploads/{upload_id}/complete` with all `{part_number, etag}` pairs
5. If a part fails, regenerate expired URLs with `POST .../regenerate-urls` and retry that part only
6. Abort with `DELETE /api/v2/collections/uploads/{upload_id}` if you decide to cancel

---

## Live Stream

- Always check `GET .../mediamtx-status` and `GET .../worker-status` before declaring a stream failure
- Display protocol-specific publish URLs clearly to operators
- Distinguish UI states: `WAITING` → `STARTING` → `STREAMING` → `PAUSED` → `STOPPED`
- Reconcile session state after app restarts by fetching `GET /api/v2/live-stream/sessions/{session_id}`
- For WebRTC (WHIP/WHEP) use the `?token=` query param since browsers cannot set custom headers on WebRTC signaling

---

## Logging and Observability

- **Add a request correlation ID** per call — log it alongside endpoint, status, and latency
- **Never log raw API keys** or full authorization headers in any log system
- **Redact** sensitive fields (`api_key`, `email`, full URLs with signed tokens) before shipping to telemetry
- **Structure your logs** — include `collection_id`, `job_id`, `session_id` in relevant log lines for traceability
- **Alert on**: repeated `5xx` errors, `INSUFFICIENT_CREDITS`, job failures

---

## Data Governance

- Follow your organization's data-retention policy for exported CSV and analytics artifacts
- Do not store presigned S3 URLs beyond their TTL (typically 1 hour)
- Use HTTPS for all API calls — HTTP is rejected
- When sharing collections, apply the **principle of least privilege**: default to `read_only` for consumers, grant `read_write` only when uploads or modifications are required
- Rotate API keys on personnel changes (when a team member leaves, revoke their key)

---

## SDK and Client Design Tips

If building a wrapper/SDK around the CreativAI API:

- Implement the full retry-with-backoff logic at the HTTP layer, not per-endpoint
- Expose polling helpers that abstract the async job pattern
- Surface `credits_used` and `job_id` in every response object for observability
- Cache public endpoints like `/subscriptions/plans` and `/subscriptions/pricing` with a TTL of ~1 hour
- Validate `collection_id` and `plate_id` locally before sending requests to avoid unnecessary API calls
- Implement circuit-breaker behavior: if 3 consecutive requests fail with `5xx`, back off for 60 seconds before trying again
