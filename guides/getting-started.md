# Getting Started

This guide walks you through the complete CreativAI workflow — from first API call to a running AI-powered search and analysis pipeline. Follow this guide top-to-bottom the first time you integrate.

> **No local upload required.** CreativAI pulls media directly from your cloud storage — Google Drive, Dropbox, or Hugging Face. Your browser never has to send a single video byte to our servers.

## How It All Fits Together

```
Your App
  │
  ├── 0. Get API Key (app → profile dropdown → API Key)
  │
  ├── 1. Verify Authentication
  │
  ├── 2. Create a Collection (choose embedding model)
  │
  ├── 3. Import Media — pick one:
  │       ├── Google Drive  →  POST /api/v2/upload/google-drive/transfer
  │       ├── Dropbox       →  POST /api/v2/upload/dropbox/transfer
  │       └── Hugging Face  →  POST /api/v2/upload/huggingface/transfer
  │
  ├── 4. Preprocessing (automatic, ~1–3 min/video — no action needed)
  │
  ├── 5. Index  (embeds media → Milvus vector store)
  │
  ├── 6. Search (semantic, hybrid, vision, or audio)
  │
  ├── 7. Data Plates (curated result sets — the analysis unit)
  │       └── Sub-Plates  (split work across annotators)
  │
  ├── 8. Knowledge Extraction (AI answers per segment → structured table)
  │       └── Filters  (slice the table by any column value)
  │
  ├── 9. Agentic Chat — SSE (multi-step AI agent over your collection)
  │
  ├── 10. Sharing & RBAC (invite team members, assign roles)
  │
  └── 11. Task Management (create, assign, and track annotation jobs)
```

---

---

## Step 0 — Get Your API Key

**Sign up or log in** at [app.creativai.io](https://app.creativai.io), then:

1. Click your profile avatar (top-right) → **Settings** → **API Keys**
2. Click **Create New Key**, give it a name (e.g. `dev-local`)
3. Copy the key — it is shown **once**

Store in your shell:
```bash
export CREATIVAI_BASE_URL="https://creativai-apis.com"
export CREATIVAI_API_KEY="<YOUR_API_KEY>"
```

See [authentication.md](authentication.md) for full key management (create, list, revoke).

---

## Step 1 — Verify Authentication

Validate your API key and retrieve account info (credits, usage):

```bash
curl "$CREATIVAI_BASE_URL/api/v2/users/get_users_info" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "usr_abc123",
    "credits": 150.0,
    "total_indexed_hours": 0.0,
    "search_requests": 0,
    "total_videos_analyzed": 0,
    "total_images_analyzed": 0
  },
  "error": null
}
```

## Step 2 — Create a Collection

Collections are namespaced workspaces for your media. Choose the right embedding model upfront — it cannot be changed after creation.

| Model | `model` value | Best For |
|---|---|---|
| Video-Only (default) | `"video_only"` | Video-only, 512-dim vision + 1024-dim subtitle vectors |
| Multimodal | `"multimodal"` | Videos, images — unified 4096-dim multimodal |

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection_name` | string | Yes | Unique name for this collection |
| `description` | string | No | Human-readable description |
| `model` | string | No | `"video_only"` (Video-Only) or `"multimodal"` (Multimodal). Default: `"video_only"` |
| `organization_id` | string | No | Scope the collection to an org |
| `project_name` | string | No | Scope the collection to a project within the org |

```bash
RESPONSE=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/collections" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "my-first-collection",
    "description": "Getting started test collection",
    "model": "video_only"
  }')

COLLECTION_ID=$(echo $RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['collection_id'])")
echo "Collection ID: $COLLECTION_ID"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "collection_id": "my-first-collection_a1b2c3d4",
    "collection_name": "my-first-collection",
    "description": "Getting started test collection",
    "model": "video_only",
    "status": "active",
    "organization_id": "org_abc123",
    "project_name": "Default Project",
    "created_at": "2026-05-26T10:00:00Z"
  },
  "error": null
}
```

> **Tier limit:** If you've reached your plan's collection limit, you'll get error code `TIER_LIMIT`. Delete unused collections or upgrade your plan.

## Step 3 — Import Media (no local upload required)

CreativAI pulls your media directly from the cloud. Pick the provider where your videos already live. The backend downloads and stores them in your collection — no file ever passes through your browser.

> See [upload-integrations.md](upload-integrations.md) for full OAuth setup, pagination, and error handling for each provider.

### Option A — Google Drive

**Prerequisites:** Complete the Google OAuth flow in your app to obtain an `access_token`.

```bash
# 1. List your Drive video files
curl "$CREATIVAI_BASE_URL/api/v2/upload/google-drive/files?access_token=$GOOGLE_ACCESS_TOKEN" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
        "name": "interview.mp4",
        "mimeType": "video/mp4",
        "size": "104857600"
      }
    ],
    "next_page_token": null
  }
}
```

```bash
# 2. Transfer selected files into your collection
curl -X POST "$CREATIVAI_BASE_URL/api/v2/upload/google-drive/transfer" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "access_token": "'$GOOGLE_ACCESS_TOKEN'",
    "file_ids": ["1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"],
    "file_names": ["interview.mp4"]
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      { "file_id": "1BxiMVs0XRA5...", "status": "ok", "video_id": "vid_abc123" }
    ]
  }
}
```

Always check `results[].status` per file — the endpoint returns `200` even when individual files fail.

---

### Option B — Dropbox

**Prerequisites:** Complete the Dropbox OAuth flow to obtain an `access_token`.

```bash
# 1. List your Dropbox video files
curl "$CREATIVAI_BASE_URL/api/v2/upload/dropbox/files?access_token=$DROPBOX_ACCESS_TOKEN" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

```bash
# 2. Transfer selected files (use path_display from the list response)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/upload/dropbox/transfer" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "access_token": "'$DROPBOX_ACCESS_TOKEN'",
    "file_paths": ["/Videos/conference_talk.mp4"],
    "file_names": ["conference_talk.mp4"]
  }'
```

---

### Option C — Hugging Face

No OAuth popup needed — provide a Hugging Face access token directly (optional for public repos).

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/upload/huggingface/transfer" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "token": "'$HF_TOKEN'",
    "files": [
      {
        "url": "https://huggingface.co/datasets/my-org/my-dataset/resolve/main/clip1.mp4",
        "name": "clip1.mp4"
      }
    ]
  }'
```

> Only `https://huggingface.co` and `https://hf.co` URLs are accepted. The backend processes up to 4 files concurrently.

---

### Option D — S3 Transfer (for existing AWS buckets)

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/transfers" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "source_url": "s3://your-bucket/videos/prefix/"
  }'
```

**Response** (`202 Accepted`):
```json
{
  "success": true,
  "data": {
    "job_id": "transfer_xyz789",
    "status": "initiated",
    "collection_id": "my-first-collection_a1b2c3d4"
  },
  "error": null
}
```

## Step 4 — Wait for Preprocessing

After upload, a Lambda function automatically preprocesses media (splits video into 16-second chunks, normalizes images). This runs in the background — no action needed.

```bash
# Poll until preprocessing_status is "completed" or "partial"
curl "$CREATIVAI_BASE_URL/api/v2/indexing/preprocessing-status/$COLLECTION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "collection_id": "my-first-collection_a1b2c3d4",
    "preprocessing_status": "completed",
    "can_start_indexing": true,
    "total_videos": 3,
    "videos_completed": 3,
    "videos_pending": 0,
    "videos_failed": 0,
    "total_chunks": 120,
    "total_duration_hours": 0.53,
    "total_size_gb": 1.2
  },
  "error": null
}
```

| `preprocessing_status` | `can_start_indexing` | Action |
|---|:---:|---|
| `"processing"` | false | Wait and re-poll (every 15s) |
| `"completed"` | true | Proceed to indexing |
| `"partial"` | true | Proceed — some media is ready |
| `"failed"` | false | Check `failed_videos`; re-upload |
| `"no_videos"` | false | Upload media first |

## Step 5 — Start Indexing

```bash
INDEX=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}')

INDEXING_ID=$(echo $INDEX | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['indexing_id'])")
echo "Indexing job: $INDEXING_ID"
```

**Response** (`202 Accepted`):
```json
{
  "success": true,
  "data": {
    "indexing_id": "idx_xxxxxxxxxx",
    "collection_id": "my-first-collection_a1b2c3d4",
    "status": "initiated",
    "estimated_credits": 12.5,
    "total_chunks": 120
  },
  "error": null
}
```

Poll status:

```bash
curl "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based/$INDEXING_ID/status" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Status response:**
```json
{
  "success": true,
  "data": {
    "indexing_id": "idx_xxxxxxxxxx",
    "status": "completed",
    "total_videos": 3,
    "processed_videos": 3,
    "failed_videos": 0,
    "total_chunks": 120,
    "indexed_chunks": 120,
    "credits_used": 12.5,
    "completed_at": "2026-05-26T10:08:32Z"
  },
  "error": null
}
```

Keep polling until `status` is `"completed"`, `"partial"`, or `"failed"`. Typical interval: 15 seconds.

## Step 6 — Search

Search is **asynchronous**. `POST /search` returns `202` with a `search_job_id`; poll `GET /search/jobs/{id}` until the job reports `status: "completed"`, at which point the response carries the first page of bucketed results.

```bash
# Submit the search
SUBMIT=$(curl -sf -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "text_query": "person walking into a room",
    "search_type": "hybrid",
    "page_size": 20
  }')
SEARCH_JOB_ID=$(echo "$SUBMIT" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['search_job_id'])")

# Poll until completed
while true; do
  RESP=$(curl -sf "$CREATIVAI_BASE_URL/api/v2/search/jobs/$SEARCH_JOB_ID" \
    -H "X-API-Key: $CREATIVAI_API_KEY")
  STATUS=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['status'])")
  [ "$STATUS" = "completed" ] && break
  [ "$STATUS" = "failed" ]    && { echo "$RESP" | python3 -m json.tool; exit 1; }
  sleep 2
done
echo "$RESP" | python3 -m json.tool
```

> **Narrow the search.** Add `tags: ["lobby"]` or a typed `meta_filter` (`{"op": "and", "clauses": [{"key": "region", "cmp": "==", "value": "eu"}]}`) to restrict results to media already carrying those labels — declared at upload time on `confirm-upload`. See [indexing-and-search.md](indexing-and-search.md#filter-by-tags-and-metadata).

**Response:**
```json
{
  "success": true,
  "data": {
    "search_id": "srch_xxxxxxxxxx",
    "collection_id": "my-first-collection_a1b2c3d4",
    "query": "person walking into a room",
    "total_results": 15,
    "high": [
      {
        "segment_id": "seg_abc123",
        "video_url": "https://cdn.../chunk.mp4",
        "video_s3_uri": "s3://bucket/col_xxx/uploads/sample.mp4",
        "start_time": 32.0,
        "end_time": 48.0,
        "thumbnail_url": "https://cdn.../thumb.jpg",
        "score": 0.94,
        "tags": []
      }
    ],
    "medium": [ "..." ],
    "low": [ "..." ]
  },
  "error": null
}
```

Save the `search_id` — you'll need it to create a data plate.

## Step 7 — Create a Data Plate

A data plate is a curated subset of search results that becomes the basis for all AI analysis. Think of it as a named spreadsheet of video segments — each row is a clip, each column is an AI-generated answer.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/create" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "search_id": "'$SEARCH_ID'",
    "top_k": 50,
    "levels": ["high", "medium"],
    "name": "Person Entry Scenes"
  }'
```

**Response** (`202 Accepted`):
```json
{
  "success": true,
  "data": {
    "job_id": "plate_job_xxx",
    "status": "initiated"
  },
  "error": null
}
```

Poll `GET /api/v2/data-plates/jobs/{job_id}` until `status == "completed"`, then use the returned `plate_id`.

### Filtering Plate Segments

Once knowledge extraction has populated columns, filter segments by column value when fetching the plate:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/get" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "page": 1,
    "page_size": 50,
    "filters": {
      "Is anyone wearing a safety vest?": "No",
      "How many people are visible?": "2"
    }
  }'
```

Filters are case-insensitive substring matches across any extracted column.

### Sub-Plates (Split Annotation Work)

When a plate is large, split it across annotators using sub-plates:

```bash
# Auto-distribute: creates a task, splits the plate, and assigns sub-plates in one call
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/auto-distribute" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "task_title": "Verify Q1 Security Incidents",
    "mode": "segment_wise",
    "distribution": "equal",
    "assignees": ["user_alice", "user_bob", "user_charlie"]
  }'
```

See [data-plates.md](data-plates.md) for sub-plate modes (`filter`, `segment_wise`, `column_wise`) and the per-segment verification workflow.

---

## Step 8 — Extract Knowledge

Ask questions about every segment in your plate:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/knowledge-extraction/columns/add" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "question": "How many people are visible?",
    "model_version": "base"
  }'
```

**Response** (`202 Accepted`):
```json
{
  "success": true,
  "data": {
    "job_id": "ke_job_xxxxxxxxxx",
    "status": "initiated",
    "question": "How many people are visible?",
    "total_segments": 50
  },
  "error": null
}
```

Poll `GET /api/v2/knowledge-extraction/jobs/{job_id}` until `status == "completed"`.

## Step 9 — Agentic Chat (SSE)

The agent reasons over your **entire collection** autonomously — it can search, create data plates, run knowledge extraction, browse the web, search YouTube, and synthesise a final answer, all from a single natural-language message. Responses stream as Server-Sent Events (SSE).

```bash
# 1. Create a persistent chat session
SESSION=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'", "title": "My first analysis"}')

SESSION_ID=$(echo $SESSION | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['session_id'])")

# 2. Send a message — response streams as SSE
curl -N -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "What is happening in most of the footage?"}'
```

### SSE Event Stream

```
event: thinking
data: "Planning the search strategy..."

event: plan
data: [{"step": "refine_and_search", ...}, {"step": "create_plate", ...}]

event: node_enter
data: {"node": "refine_and_search"}

event: answer_delta
data: "Based on the indexed footage, the most common activity is..."

event: answer
data: "Based on the indexed footage, the most common activity is..."

event: complete
data: {}
```

### Reconnecting Mid-Stream

If the browser disconnects while the agent is running, reconnect by sending an empty message — all buffered events are replayed:

```bash
curl -N -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": ""}'
```

See [agentic-chat.md](agentic-chat.md) for the full event schema, interrupt handling, and session management.

---

## Step 10 — Share Your Collection

Invite team members with fine-grained roles:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/invite" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "target_email": "alice@example.com",
    "role": "read_write",
    "plate_access": "all"
  }'
```

| Role | Capabilities |
|---|---|
| `admin` | Full control — manage members, delete collection, manage tasks |
| `read_write` | Upload, index, search, create/edit plates, run KE |
| `read_only` | Read and search only |

To restrict a member to specific plates only, use `"plate_access": "restricted"` with a `plate_permissions` map.  
See [sharing-and-rbac.md](sharing-and-rbac.md) for groups, per-plate permissions, and invitation management.

---

## Step 11 — Task Management

Tasks are work items for annotation, review, or verification of video segments. Use them to coordinate team workflows on large collections.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/create" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "title": "Annotate PPE compliance — Q1 footage",
    "task_type": "verification",
    "priority": "high",
    "assigned_users": ["user_alice", "user_bob"],
    "due_date": "2026-07-01T00:00:00Z"
  }'
```

Assignees receive FCM push notifications and can list their tasks via `GET /api/v2/tasks/my-tasks`.  
See [tasks.md](tasks.md) for auto-distribution, activity tracking, and sub-plate assignment.

---

---

## Common Errors

| Code | Meaning | Fix |
|------|---------|-----|
| `UNAUTHORIZED` | Invalid or missing API key | Check `X-API-Key` header and key value |
| `TIER_LIMIT` | Plan limit reached | Upgrade plan or delete unused data |
| `BAD_REQUEST: Cannot start indexing` | Preprocessing not done | Wait for `can_start_indexing: true` |
| `FORBIDDEN` | Not collection owner/admin | Check your role on the collection |
| `NOT_FOUND` | Invalid ID | Verify `collection_id`, `plate_id` |
| `INSUFFICIENT_CREDITS` | Out of credits | Add credits or use estimate endpoint |

---

## What's Next

| Goal | Guide |
|------|-------|
| Google Drive / Dropbox / Hugging Face upload flow | [upload-integrations.md](upload-integrations.md) |
| Deep dive into collections & media management | [collections.md](collections.md) |
| Indexing, cost estimation, and search options | [indexing-and-search.md](indexing-and-search.md) |
| Data plates: filters, sub-plates, CSV export | [data-plates.md](data-plates.md) |
| Knowledge extraction: columns, reference images, chat | [knowledge-extraction.md](knowledge-extraction.md) |
| Agentic chat: SSE events, interrupts, visualization | [agentic-chat.md](agentic-chat.md) |
| Invite team members, set roles and plate permissions | [sharing-and-rbac.md](sharing-and-rbac.md) |
| Create, assign, and track annotation tasks | [tasks.md](tasks.md) |
| Organize with organizations & projects | [organizations-and-projects.md](organizations-and-projects.md) |
| Real-time stream analysis | [live-stream-guide.md](live-stream-guide.md) |
| YouTube and web ingestion | [online-and-youtube-search.md](online-and-youtube-search.md) |
| Full endpoint list | [../reference/endpoint-registry.md](../reference/endpoint-registry.md) |
