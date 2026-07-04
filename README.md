# CreativAI API Reference

CreativAI is a **Video Intelligence Platform** that lets you upload, index, search, and extract structured knowledge from video libraries at scale. It is built for teams that deal with large volumes of footage — security operators, media houses, sports analysts, content moderators, researchers, and enterprise data teams — who need to query video content the way a search engine queries text.

**What CreativAI enables:**
- **Semantic search across video** — "Find every moment a forklift enters the loading bay" across 10,000 hours of CCTV footage
- **Structured data extraction** — turn raw video segments into a spreadsheet: "Is PPE worn?", "How many people are visible?", "What emotion is the speaker expressing?"
- **AI-powered chat on your video data** — ask natural-language questions and get synthesised, cited answers from your indexed footage
- **Live stream analysis** — connect an IP camera or OBS stream and run real-time extraction while recording
- **Team annotation workflows** — divide footage into sub-plates, assign segments to annotators, track verification progress

**Base URL:** `https://creativai-apis.com`  
**Current API version:** `v2` (current and recommended for all features).  
**Interactive docs:** Available in-app via **API Documentation** in the left sidebar.

---

## What Can You Build?

| Use Case | Industry | Key APIs Used |
|----------|----------|---------------|
| Build searchable visual memory for autonomous systems | Robotics & Embodied AI | Collections → Indexing → Search → Data Plates |
| Find rare visual events and generate structured labels at scale | Research & Visual Data | Collections → Indexing → Data Plates → Knowledge Extraction |
| Detect suspicious activity and generate incident timelines | Public Safety & Security | Live Stream → Data Plates → Knowledge Extraction |
| Auto-tag scenes, people, objects, and brand moments in archives | Media & Entertainment | Collections → Indexing → Search → Knowledge Extraction |
| Analyze game footage for highlights and tactical patterns | Sports | Collections → Indexing → Search → Data Plates |
| Query multi-modal datasets (videos and images) in one workflow | Cross-Industry Operations | Collections → Indexing → Search → Agentic Chat |
| Enrich collection insights with visual charts and summaries | Analytics & BI | Knowledge Extraction → Charts |

---

## Step 0 — Get Your API Key

Before making any API call you need an API key. Keys are created from the CreativAI app.

### Sign Up / Log In

1. Go to **[creativ-ai.com](https://creativ-ai.com)** and create an account (or log in).
2. Verify your email address.
3. You will land on the **collections page (`/`)** with a free-tier plan active and welcome credits applied.

### Find Your API Key

Your API key is **automatically provisioned** when you sign up — there is nothing to create.

1. Click your **profile avatar** in the top-right corner to open the profile dropdown.
2. Click **API Key** to expand the section.
3. Click the **copy icon** to copy the key to your clipboard.

> **Key format:** Keys begin with `sk_live_`. Never commit them to source control.

---

## Quick Start

```bash
export CREATIVAI_BASE_URL="https://creativai-apis.com"
export CREATIVAI_API_KEY="<YOUR_API_KEY>"

# Health check (no auth required)
curl "$CREATIVAI_BASE_URL/health"

# Verify your key is active and check your account info
curl "$CREATIVAI_BASE_URL/api/v2/users/get_users_info" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
# → {"data": {"credits_remaining": 5000, "uploaded_hours": 0, ...}}
```

### First Workflow in 5 Commands

> **Scenario:** Import a dashcam recording from Google Drive, index it, and search for moments where a pedestrian is visible.
>
> **No local upload required** — the backend fetches the file directly from Google Drive into your collection.

```bash
# 1. Create a collection (video-only model is fine for dashcam footage)
COLLECTION_ID=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/collections" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_name": "dashcam-trip-2026-05", "model": "video_only"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['collection_id'])")

# 2. Transfer file from Google Drive (replace GOOGLE_ACCESS_TOKEN and FILE_ID with real values)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/upload/google-drive/transfer" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COLLECTION_ID\",
    \"access_token\": \"$GOOGLE_ACCESS_TOKEN\",
    \"file_ids\": [\"$DRIVE_FILE_ID\"],
    \"file_names\": [\"trip.mp4\"]
  }"

# 3. Start indexing (async — returns a job ID immediately)
INDEXING_ID=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COLLECTION_ID\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['indexing_id'])")

# 4. Poll until indexing is complete (takes ~1–3 min per hour of video)
while true; do
  STATUS=$(curl -s "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based/$INDEXING_ID/status" \
    -H "X-API-Key: $CREATIVAI_API_KEY" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['status'])")
  echo "Indexing: $STATUS"
  [ "$STATUS" = "completed" ] && break
  sleep 15
done

# 5. Search — find every moment a pedestrian is visible
curl -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COLLECTION_ID\", \"text_query\": \"pedestrian crossing road\", \"search_type\": \"hybrid\"}"
```

> Also works with Dropbox (`POST /api/v2/upload/dropbox/transfer`) and Hugging Face (`POST /api/v2/upload/huggingface/transfer`). See [upload-integrations.md](guides/upload-integrations.md) for the full OAuth setup for each provider.

---

## API Conventions

### Authentication

Every authenticated request requires one of these headers (both are equivalent):

```
X-API-Key: <YOUR_API_KEY>
Authorization: Bearer <YOUR_API_KEY>
```

`X-API-Key` is preferred for server-to-server calls. `Authorization: Bearer` is useful when integrating with tools that follow the OAuth2 convention.

> **Exception:** WebRTC signaling endpoints use `?token=<YOUR_API_KEY>` as a query parameter because browsers cannot set custom headers in WebRTC negotiation requests.

### Embedding Models

CreativAI supports two embedding models. Choose when creating a collection — you cannot change the model afterwards.

| `model` | Supports | Best for |
|---------|----------|----------|
| `"video_only"` (default) | Video frames, audio/subtitles | CCTV, dashcam, general video search |
| `"multimodal"` | Video + images | Multi-modal analysis, YouTube content, mixed media workflows |

### Response Envelope

Every response (success or error) uses the same JSON envelope:

```json
{
  "success": true,
  "data": { "..." },
  "error": null
}
```

On error:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INSUFFICIENT_CREDITS",
    "message": "Not enough credits to complete this indexing job",
    "details": { "required": 120, "available": 45 },
    "timestamp": "2026-05-26T10:00:00Z"
  }
}
```

Always check `success` first. If `false`, inspect `error.code` — see [errors.md](guides/errors.md) for the full code list and retry guidance.

### API Versioning

| Version | Status | Use when |
|---------|--------|----------|
| `/api/v2/` | Current stable | All features |

If legacy `/api/v3/` aliases exist in older clients, migrate to `/api/v2/`.

### Async Operations

Long-running jobs (indexing, knowledge extraction, plate creation, S3 transfers) return `202 Accepted` immediately with a `job_id`. Poll the status endpoint until you see a terminal state.

| State | Meaning |
|-------|---------|
| `initiated` | Job queued, not yet started |
| `processing` | Actively running |
| `completed` | Success — results available |
| `failed` | Permanent failure — check `error` field |
| `partial` | Some items succeeded, some failed |

```
POST /api/v2/indexing/chunk-based          → 202 { "indexing_id": "idx_xxx" }
GET  /api/v2/indexing/chunk-based/{id}/status → { "status": "processing" | "completed" | "failed" }
```

**Recommended polling interval:** 5 s initially, back off to 30 s for long jobs. See [async-jobs.md](guides/async-jobs.md) for a full polling helper.

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

Each guide covers one feature area in depth with request/response examples, field tables, and real-world context.

### Core Workflow

| Guide | What it covers | Real-world example |
|-------|----------------|--------------------|
| [getting-started.md](guides/getting-started.md) | End-to-end first integration: upload → index → search → extract | Upload 10 dashcam videos, index them, find every moment a pedestrian is visible |
| [authentication.md](guides/authentication.md) | API key location, auth headers, key rotation, roles (admin / read_write / read_only), security best practices | Separate keys for dev, CI, and prod; revoke a compromised key immediately |
| [async-jobs.md](guides/async-jobs.md) | Polling pattern for 202 jobs, status lifecycle, exponential backoff | Wait for an indexing job to complete before triggering a search |
| [errors.md](guides/errors.md) | Error codes, HTTP status meanings, retryable vs non-retryable, backoff formula | Handle `INSUFFICIENT_CREDITS` gracefully; retry `503` with jitter |
| [integration-guidelines.md](guides/integration-guidelines.md) | Production best practices: versioning, idempotency, rate limits, logging, data governance | Build a robust CI pipeline that indexes nightly footage uploads reliably |

### Collections & Media

| Guide | What it covers | Real-world example |
|-------|----------------|--------------------|
| [upload-integrations.md](guides/upload-integrations.md) | Import media from Google Drive, Dropbox, and Hugging Face without local download; OAuth setup, list endpoints, transfer endpoints, per-file results | User selects 20 videos from their Google Drive; backend transfers them directly into the collection without the browser ever touching the file bytes |
| [collections.md](guides/collections.md) | Create collections (video-only or multi-modal models), presigned S3 upload URL for direct upload, multipart upload for large files, transfer from existing S3 buckets | Ingest 500 GB of archival broadcast footage from an S3 bucket in a single transfer job |
| [indexing-and-search.md](guides/indexing-and-search.md) | Start indexing jobs, poll status, estimate credit cost, semantic/visual/audio search, pagination, image-query search | "Find all moments a red Ferrari is visible" — visual search using an uploaded reference image |

### Analysis & Extraction

| Guide | What it covers | Real-world example |
|-------|----------------|--------------------|
| [data-plates.md](guides/data-plates.md) | Create plates from search results or full collections, manage segments, filter by extracted column values, split work across annotators with sub-plates (`segment_wise` / `filter` / `column_wise`), export to CSV | Create a plate of all "near-miss" incidents from warehouse footage; apply filter `"Is PPE worn?": "No"` to isolate violations; auto-distribute the 800 matches across 4 annotators |
| [knowledge-extraction.md](guides/knowledge-extraction.md) | Add AI extraction columns (questions answered per-segment), multi-question batch jobs, reference images, chat with plate data, auto-generated charts | Ask "Is the worker wearing a hard hat?" across 2,000 segments; export a compliance report; chat: "Which camera angle has the highest violation rate?" |
| [agentic-chat.md](guides/agentic-chat.md) | SSE streaming AI agent, multi-step search planning, execution plan events, interrupts (search feedback, YouTube candidates), stop/resume, reconnect after disconnect | "Summarise all camera angles that show a vehicle entering between 2 AM and 4 AM and compare to last week" — agent searches, synthesises, and cites clips |

### Live & Online Video

| Guide | What it covers | Real-world example |
|-------|----------------|--------------------|
| [live-stream-guide.md](guides/live-stream-guide.md) | Connect RTSP/RTMP/SRT/HLS/WebRTC/YouTube streams, start analysis sessions, add questions, poll segment results, manage MediaMTX | Point an IP camera at a factory conveyor belt; extract "defect visible?" every 30 seconds in real time |
| [online-and-youtube-search.md](guides/online-and-youtube-search.md) | Server-side online search (no extension), browser-extension YouTube Search v2 (refine → submit → curate → index) | Find the 20 most relevant YouTube tutorials on "robotic arm calibration" and index them into a training knowledge base |

### Teams & Access

| Guide | What it covers | Real-world example |
|-------|----------------|--------------------|
| [organizations-and-projects.md](guides/organizations-and-projects.md) | Create orgs and projects to organise collections, multi-tenant isolation | Agency with multiple clients: each client is a project; each campaign is a collection |
| [sharing-and-rbac.md](guides/sharing-and-rbac.md) | Invite team members, assign roles (admin / read_write / read_only), restrict per-plate access, manage groups, FCM push notifications | Invite 5 annotators with `read_write` access restricted to their assigned sub-plate; invite a client with `read_only` access to the final plate |
| [tasks.md](guides/tasks.md) | Create and assign annotation/verification tasks, track progress, activity log, auto-distribute a plate across a team | Admin creates a verification task for 2,000 near-miss segments; `auto-distribute` splits the work equally across 4 annotators who update progress daily |

### Billing & Account

| Guide | What it covers | Real-world example |
|-------|----------------|--------------------|
| [users-billing-subscriptions.md](guides/users-billing-subscriptions.md) | Check credit balance, view transactions, upgrade/cancel subscriptions, download invoices, manage API keys programmatically | Check remaining credits before triggering a large indexing batch; export a monthly invoice PDF for finance |

---

## Running the Examples

```bash
# Set environment variables once
export CREATIVAI_BASE_URL="https://creativai-apis.com"
export CREATIVAI_API_KEY="<YOUR_API_KEY>"
export COLLECTION_ID="your-collection-id"

# Run any cURL script
bash examples/curl/01_collections.sh
bash examples/curl/02_indexing_and_search.sh
bash examples/curl/04_agentic_chat_sse.sh
```

```bash
# Python end-to-end workflows
pip install -r examples/python/requirements.txt
python examples/python/workflows.py
```

---

## Security Notes

- **Never embed API keys** in frontend JavaScript, mobile app bundles, or public repositories — they would be visible to anyone who inspects the source
- **Use environment variables** for local development (`.env` files that are `.gitignore`d)
- **Use a secrets manager** in production: AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault, or equivalent
- **One key per environment** — separate keys for dev, staging, and production so a leaked dev key cannot affect production data
- **Rotate regularly** — revoke and reissue keys on a schedule (e.g. every 90 days) and immediately upon any suspected compromise
- **All traffic over HTTPS** — the API does not accept plain HTTP; always use `https://creativai-apis.com`

---

## Notes

- This is reference documentation only — no backend implementation code is included.
- Internal webhook endpoints (`/internal/...`) are listed for architecture context; they are called by infrastructure, not external clients.
- Endpoint behaviour and credit pricing can evolve — keep this folder in sync with backend releases.
- The [endpoint-registry.md](reference/endpoint-registry.md) lists the current v2 endpoints for integration.
