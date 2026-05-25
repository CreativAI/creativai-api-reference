# Getting Started

This guide walks you through the complete CreativAI workflow — from first API call to a running AI-powered search and analysis pipeline. Follow this guide top-to-bottom the first time you integrate.

## Architecture Overview

```
Your App
  │
  ├── 0. Get API Key (dashboard → Settings → API Keys)
  │
  ├── 1. Create Collection (choose embedding model)
  │
  ├── 2. Upload Media (presigned S3 URLs → direct upload)
  │       Videos (.mp4, .mov, .avi), Images (.jpg, .png, .webp), PDFs
  │
  ├── 3. Preprocessing (automatic Lambda, ~1–3 min/video)
  │
  ├── 4. Index (embeds media → Milvus vector store)
  │
  ├── 5. Search (semantic hybrid, vision, or audio search)
  │
  ├── 6. Data Plates (curated result sets for analysis)
  │
  ├── 7. Knowledge Extraction (AI answers questions about segments)
  │
  └── 8. Agentic Chat (multi-step AI agent over your data)
```

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

```bash
curl "$CREATIVAI_BASE_URL/api/v2/users/api-key-check" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": { "valid": true },
  "error": null
}
```

Get your account info (credits, usage):

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
    "total_indexed_hours": 0.0,
    "search_requests": 0,
    "total_clips_analyzed": 0
  },
  "error": null
}
```

## Step 2 — Create a Collection

Collections are namespaced workspaces for your media. Choose the right embedding model upfront — it cannot be changed after creation.

| Model | `model` value | Best For |
|---|---|---|
| InternVideo2 (default) | `"default"` | Video-only, 512-dim vision + 1024-dim subtitle vectors |
| Qwen3-VL | `"qwen"` | Videos, images, PDFs — unified 4096-dim multimodal |

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection_name` | string | Yes | Unique name for this collection |
| `description` | string | No | Human-readable description |
| `model` | string | No | `"default"` (InternVideo2) or `"qwen"` (Qwen3-VL). Default: `"default"` |
| `organization_id` | string | No | Scope the collection to an org |
| `project_name` | string | No | Scope the collection to a project within the org |

```bash
RESPONSE=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/collections" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "my-first-collection",
    "description": "Getting started test collection",
    "model": "default"
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
    "model": "internvideo2",
    "status": "active",
    "organization_id": "org_abc123",
    "project_name": "Default Project",
    "created_at": "2026-05-26T10:00:00Z"
  },
  "error": null
}
```

> **Tier limit:** If you've reached your plan's collection limit, you'll get error code `TIER_LIMIT`. Delete unused collections or upgrade your plan.

## Step 3 — Upload Media

### Option A — Single File (presigned URL)

**Request body for** `POST /api/v2/collections/{collection_id}/upload-url`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filename` | string | Yes | File name including extension |
| `content_type` | string | Yes | MIME type (`video/mp4`, `image/jpeg`, `application/pdf`) |

```bash
# 1. Request a presigned upload URL
UPLOAD=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/upload-url" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"filename": "sample.mp4", "content_type": "video/mp4"}')

UPLOAD_URL=$(echo $UPLOAD | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['upload_url'])")
```

**Response:**
```json
{
  "success": true,
  "data": {
    "upload_url": "https://s3.amazonaws.com/bucket/collections/col_xxx/uploads/sample.mp4?X-Amz-Signature=...",
    "s3_uri": "s3://bucket/collections/col_xxx/uploads/sample.mp4",
    "media_key": "collections/col_xxx/uploads/sample.mp4",
    "expires_in": 3600
  },
  "error": null
}
```

```bash
# 2. Upload directly to S3 (no API key needed — the URL is pre-signed)
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: video/mp4" \
  --data-binary @/path/to/sample.mp4
```

### Option B — Large Files (multipart, for files >100 MB)

```bash
# 1. Initiate multipart
INIT=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/collections/uploads/initiate" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "filename": "large-video.mp4",
    "content_type": "video/mp4",
    "total_parts": 4
  }')

UPLOAD_ID=$(echo $INIT | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['upload_id'])")
```

**Multipart initiate response:**
```json
{
  "success": true,
  "data": {
    "upload_id": "upload_abc123",
    "part_upload_urls": [
      "https://s3.amazonaws.com/...?partNumber=1&...",
      "https://s3.amazonaws.com/...?partNumber=2&...",
      "https://s3.amazonaws.com/...?partNumber=3&...",
      "https://s3.amazonaws.com/...?partNumber=4&..."
    ],
    "s3_uri": "s3://bucket/collections/col_xxx/uploads/large-video.mp4"
  },
  "error": null
}
```

```bash
# 2. Upload each 25 MB chunk via PUT to part_upload_urls[i]
#    Collect the ETag from each response header

# 3. Complete the multipart upload
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/uploads/$UPLOAD_ID/complete" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "parts": [
      {"part_number": 1, "etag": "\"abc123\""},
      {"part_number": 2, "etag": "\"def456\""}
    ]
  }'
```

### Option C — S3 Transfer (for existing S3 data)

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

After upload, a Lambda function automatically preprocesses media (splits video into 16-second chunks, normalizes images/PDFs). This runs in the background — no action needed.

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

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "text_query": "person walking into a room",
    "search_type": "hybrid",
    "page_size": 20
  }'
```

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

A data plate is a curated subset of search results that becomes the basis for AI analysis.

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

## Step 9 — Agentic Chat

For multi-step AI reasoning across your entire collection:

```bash
# Create a chat session
SESSION=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}')

SESSION_ID=$(echo $SESSION | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['session_id'])")

# Send a message (SSE streaming response)
curl -N -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "What is happening in most of the footage?"}'
```

The response streams as Server-Sent Events. See [agentic-chat.md](agentic-chat.md) for the full event schema.

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
| Organize with orgs & projects | [organizations-and-projects.md](organizations-and-projects.md) |
| Multipart upload deep dive | [collections.md](collections.md) |
| Collaborate on collections | [sharing-and-rbac.md](sharing-and-rbac.md) |
| Real-time stream analysis | [live-stream-guide.md](live-stream-guide.md) |
| YouTube ingestion | [online-and-youtube-search.md](online-and-youtube-search.md) |
| Full endpoint list | [../reference/endpoint-registry.md](../reference/endpoint-registry.md) |
