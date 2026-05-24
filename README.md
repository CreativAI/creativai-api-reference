# CreativAI API Reference

Public-facing, implementation-agnostic reference for integrating with the CreativAI Video Intelligence API. No backend source code is exposed — only contracts, examples, and integration guidance.

---

## Quick Start

```bash
export CREATIVAI_BASE_URL="https://api.creativai.io"
export CREATIVAI_API_KEY="your_api_key"

# Health check
curl "$CREATIVAI_BASE_URL/health"

# Verify your key
curl -X GET "$CREATIVAI_BASE_URL/api/v2/users/me" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Structure

```
creativai-api-reference/
├── README.md
├── guides/              ← feature guides (one per capability)
├── reference/           ← complete endpoint catalog
└── examples/
    ├── curl/            ← runnable shell scripts
    └── python/          ← Python client + workflow examples
```

---

## guides/

Each file is a self-contained guide with endpoint tables, cURL commands, and Python examples.

| File | What it covers |
|------|---------------|
| `getting-started.md` | First integration walkthrough (create → upload → index → search) |
| `authentication.md` | Auth headers, roles, security best practices |
| `collections.md` | Create collections, upload media, S3 transfers, multipart uploads |
| `indexing-and-search.md` | Index media, poll jobs, run semantic/visual/audio search |
| `data-plates.md` | Build structured tables from segments, sub-plates, verification, CSV export |
| `knowledge-extraction.md` | AI column extraction, charts, synthesis query |
| `agentic-chat.md` | SSE streaming multi-turn AI agent over your collections |
| `live-stream-guide.md` | Real-time stream ingestion via RTMP/RTSP/SRT/HLS/WebRTC/YouTube |
| `organizations-and-projects.md` | Org and project hierarchy, scoped collection listing |
| `sharing-and-rbac.md` | Invite members, roles, groups, tasks, FCM push notifications |
| `online-and-youtube-search.md` | Discover and import web/YouTube videos into collections |
| `users-billing-subscriptions.md` | Account info, API keys, credits, transactions, subscriptions, invoices |
| `async-jobs.md` | Polling pattern for all long-running operations |
| `errors.md` | HTTP codes, retry strategy, backoff |
| `integration-guidelines.md` | Versioning, idempotency, logging, data governance |

---

## reference/

| File | What it covers |
|------|---------------|
| `endpoint-registry.md` | Complete catalog of all ~235 endpoints grouped by module |

---

## examples/curl/

| Script | Demonstrates |
|--------|-------------|
| `01_collections.sh` | Create collection, get upload URL, upload via presigned URL |
| `02_indexing_and_search.sh` | Start indexing, poll status, run semantic search |
| `03_data_plates_and_ke.sh` | List plates, add knowledge extraction columns |
| `04_agentic_chat_sse.sh` | SSE streaming chat with the agentic agent |
| `05_live_stream.sh` | Create session, start RTMP stream, poll worker readiness |

```bash
export CREATIVAI_BASE_URL="https://api.creativai.io"
export CREATIVAI_API_KEY="your_api_key"
export COLLECTION_ID="your-collection-id"

bash examples/curl/01_collections.sh
```

---

## examples/python/

| File | Purpose |
|------|---------|
| `client.py` | Minimal reference HTTP client with helper methods |
| `workflows.py` | End-to-end workflow examples (create, search, live stream) |
| `requirements.txt` | Only `requests` — no heavy dependencies |

```bash
pip install -r examples/python/requirements.txt
CREATIVAI_API_KEY=your_key python examples/python/workflows.py
```

---

## Conventions

- **Base paths**: V2 → `/api/v2/*` — V3 → `/api/v3/*` (Data Plates advanced features)
- **Auth**: `X-API-Key: <KEY>` or `Authorization: Bearer <KEY>`
- **Response envelope**:
  ```json
  { "success": true, "data": {}, "error": null }
  ```
- **Async operations**: submit returns `job_id` immediately (202) — poll status until `completed` or `failed`
- **SSE**: Agentic Chat streams as `text/event-stream` — use `-N` with curl, or `stream=True` in requests

---

## Notes

- This is reference documentation only — no backend implementation code is included.
- Internal webhook endpoints are listed for architecture context; they are not for external use.
- Endpoint behavior and pricing can evolve — keep this folder in sync with backend releases.
