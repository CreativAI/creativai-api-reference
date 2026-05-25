# CreativAI API Reference

Public-facing, implementation-agnostic reference for integrating with the CreativAI Video Intelligence API. No backend source code is exposed — only contracts, examples, and integration guidance.

**Base URL:** `https://creativai-apis.com`  
**Current API version:** `v2` (latest stable). Sub-plates and Knowledge Extraction are also available at `v3`.  
**Interactive docs:** Available in-app at **Settings → API Docs**.

---

## Step 0 — Get Your API Key

Before making any API call you need an API key. Keys are created from the CreativAI dashboard.

### Sign Up / Log In

1. Go to **[app.creativai.io](https://app.creativai.io)** and create an account (or log in).
2. Verify your email address.
3. You will land on the **Dashboard** with a free-tier plan active.

### Create an API Key

1. Click your **profile avatar** (top-right) → **Settings**.
2. Navigate to the **API Keys** tab.
3. Click **Create New Key**, give it a descriptive name (e.g. `dev-local`, `prod-server`).
4. Copy the key immediately — it is shown **once**. Store it in a secrets manager or `.env` file.

> **Key format:** `<YOUR_API_KEY>`  
> Keys begin with `sk_live_`. Never commit them to source control.

### Rotate or Revoke a Key

```bash
export CREATIVAI_BASE_URL="https://creativai-apis.com"
export CREATIVAI_API_KEY="<YOUR_API_KEY>"

# List all your keys (IDs + names; secret value is never returned)
curl "$CREATIVAI_BASE_URL/api/v2/api-keys" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Create a new key programmatically
curl -X POST "$CREATIVAI_BASE_URL/api/v2/api-keys" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "ci-pipeline"}'

# Revoke a key by ID
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/api-keys/{key_id}" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Quick Start

```bash
export CREATIVAI_BASE_URL="https://creativai-apis.com"
export CREATIVAI_API_KEY="<YOUR_API_KEY>"

# Health check (no auth required)
curl "$CREATIVAI_BASE_URL/health"

# Verify your key
curl "$CREATIVAI_BASE_URL/api/v2/users/api-key-check" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
# → {"success": true, "data": {"valid": true}}

# Get your account info + credits
curl "$CREATIVAI_BASE_URL/api/v2/users/me/info" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### First Workflow in 5 Commands

```bash
# 1. Create a collection
COLLECTION_ID=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/collections" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_name":"quickstart","model":"default"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['collection_id'])")

# 2. Get a presigned upload URL
UPLOAD_URL=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/upload-url" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"filename":"sample.mp4","content_type":"video/mp4"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['upload_url'])")

# 3. Upload your video directly to S3 (no API key needed here)
curl -X PUT "$UPLOAD_URL" -H "Content-Type: video/mp4" --data-binary @sample.mp4

# 4. Start indexing
INDEXING_ID=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\":\"$COLLECTION_ID\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['indexing_id'])")

# 5. Search (after indexing completes)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\":\"$COLLECTION_ID\",\"text_query\":\"person walking\",\"search_type\":\"hybrid\"}"
```

---

## API Conventions

### Authentication

Every authenticated request requires one of these headers (both are equivalent):

```
X-API-Key: <YOUR_API_KEY>
Authorization: Bearer <YOUR_API_KEY>
```

### Response Envelope

Every response (success or error) uses the same envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

On error:

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

### API Versioning

| Version | Status | Use when |
|---------|--------|----------|
| `/api/v2/` | Current stable | All features |
| `/api/v3/` | Latest for select endpoints | Sub-plates, Knowledge Extraction (preferred) |

When a v3 route exists, always use v3. This reference shows the latest available version for each endpoint.

### Async Operations

Long-running jobs return `202 Accepted` with a `job_id`. Poll the status endpoint until you see a terminal state (`completed`, `failed`, `partial`).

```
POST /api/v2/indexing/chunk-based   → 202 { "indexing_id": "idx_xxx" }
GET  /api/v2/indexing/chunk-based/{id}/status → { "status": "processing" | "completed" | "failed" }
```

---

## Repository Structure

```
creativai-api-reference/
├── README.md                  ← you are here
├── guides/                    ← one guide per feature area
├── reference/endpoint-registry.md  ← full endpoint catalog
└── examples/
    ├── curl/                  ← runnable shell scripts
    └── python/                ← Python client + workflows
```

---

## Guides

| Guide | What it covers |
|-------|----------------|
| [getting-started.md](guides/getting-started.md) | Full first-integration walkthrough |
| [authentication.md](guides/authentication.md) | API key acquisition, auth headers, roles, security |
| [collections.md](guides/collections.md) | Create collections, upload media, multipart, S3 transfers |
| [indexing-and-search.md](guides/indexing-and-search.md) | Index, poll, semantic/visual/audio search, pagination |
| [data-plates.md](guides/data-plates.md) | Plates, sub-plates, verification workflow, CSV export |
| [knowledge-extraction.md](guides/knowledge-extraction.md) | AI column extraction, charts, synthesis chat |
| [agentic-chat.md](guides/agentic-chat.md) | SSE streaming agent, interrupts, reconnect |
| [live-stream-guide.md](guides/live-stream-guide.md) | RTSP/RTMP/SRT/HLS/WebRTC/YouTube live ingestion |
| [organizations-and-projects.md](guides/organizations-and-projects.md) | Org → Project → Collection hierarchy |
| [sharing-and-rbac.md](guides/sharing-and-rbac.md) | Invite, roles, groups, tasks, FCM push |
| [online-and-youtube-search.md](guides/online-and-youtube-search.md) | YouTube discovery and import |
| [users-billing-subscriptions.md](guides/users-billing-subscriptions.md) | Account, API keys, credits, invoices |
| [async-jobs.md](guides/async-jobs.md) | Polling pattern, status values, backoff |
| [errors.md](guides/errors.md) | Error codes, retry strategy, backoff |
| [integration-guidelines.md](guides/integration-guidelines.md) | Best practices, logging, security, governance |

---

## Running the Examples

```bash
# Set environment variables once
export CREATIVAI_BASE_URL="https://creativai-apis.com"
export CREATIVAI_API_KEY="<YOUR_API_KEY>"
export COLLECTION_ID="your-collection-id"

# Run any script
bash examples/curl/01_collections.sh
bash examples/curl/02_indexing_and_search.sh
bash examples/curl/04_agentic_chat_sse.sh
```

```bash
# Python workflows
pip install -r examples/python/requirements.txt
python examples/python/workflows.py
```

---

## Security Notes

- Never embed API keys in frontend source code or mobile app bundles
- Store keys in environment variables or a secrets manager (AWS Secrets Manager, HashiCorp Vault)
- Use separate keys per environment (dev / staging / production)
- Rotate keys regularly; immediately revoke any compromised key
- All API communication must use HTTPS

---

## Notes

- This is reference documentation only — no backend implementation code is included.
- Internal webhook endpoints are listed for architecture context; they are not for external use.
- Endpoint behavior and pricing can evolve — keep this folder in sync with backend releases.
