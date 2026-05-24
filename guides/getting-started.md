# Getting Started

This guide walks you through the complete CreativAI workflow — from first API call to a running AI-powered search and analysis pipeline. Follow this guide top-to-bottom the first time you integrate.

## Architecture Overview

```
Your App
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

## Prerequisites

```bash
export CREATIVAI_BASE_URL="https://creativai-apis.com"
export CREATIVAI_API_KEY="your_api_key_here"
```

## Step 1 — Verify Authentication

```bash
curl "$CREATIVAI_BASE_URL/api/v2/users/api-key-check" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Expected: `{"success": true, "data": {"valid": true}}`

Get your info (credits, usage):

```bash
curl "$CREATIVAI_BASE_URL/api/v2/users/me/info" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

## Step 2 — Create a Collection

Collections are namespaced workspaces for your media. Choose the right embedding model upfront — it cannot be changed after creation.

| Model | `model` value | Best For |
|---|---|---|
| InternVideo2 (default) | `"default"` | Video-only, 512-dim vision + 1024-dim subtitle vectors |
| Qwen3-VL | `"qwen"` | Videos, images, PDFs — unified 4096-dim multimodal |

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

## Step 3 — Upload Media

### Option A — Single File (presigned URL)

```bash
# 1. Request a presigned upload URL
UPLOAD=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/upload-url" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"filename": "sample.mp4", "content_type": "video/mp4"}')

UPLOAD_URL=$(echo $UPLOAD | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['upload_url'])")

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

# 2. Upload each 25 MB chunk:
#    PUT to part_upload_urls[i] with the binary slice
#    Collect the ETag from each response header

# 3. Complete
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

## Step 4 — Wait for Preprocessing

After upload, a Lambda function automatically preprocesses media (splits video into 16-second chunks, normalizes images/PDFs). This runs in the background.

```bash
# Poll until preprocessing_status is "completed" or "partial"
curl "$CREATIVAI_BASE_URL/api/v2/indexing/preprocessing-status/$COLLECTION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Response fields:
- `preprocessing_status`: `"processing"` | `"completed"` | `"partial"` | `"failed"` | `"no_videos"`
- `can_start_indexing`: `true` when ready to proceed
- `total_videos`, `videos_completed`, `videos_pending`, `videos_failed`

## Step 5 — Start Indexing

```bash
INDEX=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}')

INDEXING_ID=$(echo $INDEX | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['indexing_id'])")
echo "Indexing job: $INDEXING_ID"
```

Poll status:

```bash
curl "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based/$INDEXING_ID/status" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Keep polling until `status` is `"completed"` or `"failed"`.

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

Save the `search_id` from the response for creating data plates.

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

## Step 8 — Extract Knowledge

Ask questions about the segments in your plate:

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

## Common Errors

| Error Code | Meaning | Fix |
|---|---|---|
| `UNAUTHORIZED` | Invalid or missing API key | Check header name and key value |
| `TIER_LIMIT` | Plan limit reached | Upgrade plan or delete unused data |
| `BAD_REQUEST` | Preprocessing not done | Wait for `can_start_indexing: true` |
| `FORBIDDEN` | Not collection owner/admin | Check role on shared collection |
| `NOT_FOUND` | Invalid ID | Verify collection_id, plate_id |
| `INSUFFICIENT_CREDITS` | Out of credits | Add credits or use estimate endpoint |

## What's Next

| Goal | Guide |
|---|---|
| Organize with orgs & projects | [organizations-and-projects.md](organizations-and-projects.md) |
| Multipart upload deep dive | [indexing-and-search.md](indexing-and-search.md) |
| Collaborate on collections | [sharing-and-rbac.md](sharing-and-rbac.md) |
| Real-time stream analysis | [live-stream-guide.md](live-stream-guide.md) |
| YouTube ingestion | [online-and-youtube-search.md](online-and-youtube-search.md) |
| Full endpoint list | [../reference/endpoint-registry.md](../reference/endpoint-registry.md) |
