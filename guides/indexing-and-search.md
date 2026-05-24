# Indexing & Search

## Overview

Indexing takes your uploaded media, generates AI embeddings, and stores them in the vector database (Milvus) for semantic search.

### Full Pipeline

```
Upload → Preprocessing (Lambda, automatic) → Indexing (you trigger) → Search
```

- **Preprocessing** runs automatically after upload. Lambda splits video into 16-second chunks, normalizes images/PDFs. No action needed.
- **Indexing** you trigger explicitly. Credits are deducted upfront. Runs asynchronously.
- **Search** returns timestamped video segments ranked by relevance.

---

## Preprocessing

### Check Preprocessing Status

Always check before starting indexing:

```bash
curl "$CREATIVAI_BASE_URL/api/v2/indexing/preprocessing-status/$COLLECTION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Response:
```json
{
  "success": true,
  "data": {
    "collection_id": "col_xxx",
    "preprocessing_status": "completed",
    "can_start_indexing": true,
    "total_videos": 12,
    "videos_completed": 12,
    "videos_pending": 0,
    "videos_failed": 0,
    "total_chunks": 480,
    "total_duration_hours": 2.67,
    "total_size_gb": 8.4
  }
}
```

**Status values**:
| Status | `can_start_indexing` | Meaning |
|---|---|---|
| `"processing"` | false | Lambda still preprocessing; wait and re-poll |
| `"completed"` | true | All media ready |
| `"partial"` | true | Some succeeded, some failed — partial indexing allowed |
| `"failed"` | false | All media failed; check `failed_videos` array |
| `"no_videos"` / `"no_media"` | false | Nothing uploaded yet |

For Qwen3-VL collections, the response additionally includes:
```json
{
  "media_breakdown": {"video": 8, "image": 3, "pdf": 1},
  "total_media": 12,
  "media_ready": 12,
  "media_indexed": 0
}
```

### List Ready Media

```bash
curl "$CREATIVAI_BASE_URL/api/v2/indexing/preprocessed-videos/$COLLECTION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Indexing

### Estimate Cost Before Indexing

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based/estimate-cost" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'
```

Response: `estimated_credits`, `total_duration_hours`, `total_chunks`, current credit balance.

### Start Indexing — All Media

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'
```

Returns `202 Accepted` with `indexing_id`. The job runs asynchronously.

### Start Indexing — Specific Files

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "media_s3_uris": [
      "s3://your-bucket/collections/col_xxx/uploads/lobby.mp4",
      "s3://your-bucket/collections/col_xxx/uploads/entrance.mp4"
    ]
  }'
```

### Start Indexing with Tags

Tags are attached to segments at index time and can be used to filter search results.

```bash
# Per-URI tags
curl -X POST "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "tags": {
      "s3://bucket/col_xxx/uploads/lobby.mp4": ["lobby", "camera-1"],
      "s3://bucket/col_xxx/uploads/parking.mp4": ["parking", "outdoor"]
    }
  }'

# Wildcard — same tags for all media
curl -X POST "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "tags": {"*": ["q1-2026", "security"]}
  }'
```

### Poll Indexing Status

```bash
curl "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based/$INDEXING_ID/status" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Response:
```json
{
  "success": true,
  "data": {
    "indexing_id": "idx_xxxxxxxxxx",
    "collection_id": "col_xxx",
    "status": "completed",
    "model": "internvideo2",
    "total_videos": 12,
    "processed_videos": 12,
    "failed_videos": 0,
    "total_chunks": 480,
    "indexed_chunks": 480,
    "credits_used": 26.4,
    "created_at": "2026-05-25T10:00:00Z",
    "completed_at": "2026-05-25T10:08:32Z"
  }
}
```

**Status values**: `initiated` → `processing` → `completed` / `failed` / `partial`

### Model Constraints

| Capability | `internvideo2` (default) | `qwen3-vl` |
|---|---|---|
| Video files | ✅ | ✅ |
| Image files | ❌ — rejected with 400 | ✅ |
| PDF files | ❌ — rejected with 400 | ✅ |
| Vision search | ✅ | ✅ |
| Audio/subtitle search | ✅ | ❌ |
| Image-query search | ❌ | ✅ |

---

## Search

### Basic Search

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "text_query": "person carrying a bag through a doorway",
    "search_type": "hybrid",
    "page_size": 20
  }'
```

### Search Types

| `search_type` | Description |
|---|---|
| `"hybrid"` | Combines vision + audio vectors (recommended) |
| `"vision"` | Pure visual similarity only |
| `"audio"` | Pure subtitle/transcript similarity only |

### All Search Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `collection_id` | string | required | Collection to search |
| `text_query` | string | required | Natural language query |
| `search_type` | string | `"hybrid"` | `hybrid`, `vision`, or `audio` |
| `page_number` | int | `1` | 1-indexed page number |
| `page_size` | int | `100` | Results per page (max ~500) |
| `search_id` | string | null | Re-use results from a prior search (pagination) |
| `video_urls` | list[string] | null | Restrict to specific video S3 URIs |
| `use_weights` | bool | `false` | Enable custom vision/audio weighting |
| `vision_weight` | float | `0.5` | Vision vector weight (when `use_weights: true`) |
| `audio_weight` | float | `0.5` | Audio vector weight (when `use_weights: true`) |
| `refine_query` | bool | `false` | LLM rewrites query for better recall |
| `image_base64` | string | null | Base64 image for multimodal search (Qwen only) |
| `image_key` | string | null | S3 key of uploaded image (Qwen only, preferred) |

### Search Response Structure

```json
{
  "success": true,
  "data": {
    "search_id": "srch_xxxxxxxxxx",
    "collection_id": "col_xxx",
    "query": "person carrying a bag",
    "total_results": 47,
    "page_number": 1,
    "total_pages": 3,
    "high": [
      {
        "segment_id": "seg_abc123",
        "video_url": "https://presigned-cdn-url.../chunk.mp4",
        "video_s3_uri": "s3://bucket/col_xxx/uploads/lobby.mp4",
        "start_time": 32.0,
        "end_time": 48.0,
        "thumbnail_url": "https://presigned-url.../thumb.jpg",
        "score": 0.923,
        "tags": ["lobby", "camera-1"]
      }
    ],
    "medium": [ ... ],
    "low": [ ... ],
    "level_info": {
      "high":   {"count": 8,  "start_page": 1, "end_page": 1},
      "medium": {"count": 23, "start_page": 1, "end_page": 2},
      "low":    {"count": 16, "start_page": 2, "end_page": 3}
    }
  }
}
```

Results bucket into three relevance tiers. `high` = most relevant.

### Pagination

Pass `search_id` to page through results without re-running the search:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "text_query": "person carrying a bag",
    "search_id": "srch_xxxxxxxxxx",
    "page_number": 2,
    "page_size": 20
  }'
```

### Restrict to Specific Videos

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "text_query": "smoke or fire",
    "video_urls": [
      "s3://bucket/col_xxx/uploads/canteen.mp4",
      "s3://bucket/col_xxx/uploads/kitchen.mp4"
    ]
  }'
```

### Image-Based Search (Qwen3-VL Only)

Use an image as the query to find visually similar scenes:

```bash
# Step 1: Get a presigned upload URL for your query image
IMG=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/knowledge-extraction/chat/upload-images" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"count": 1, "content_type": "image/jpeg"}')

IMAGE_KEY=$(echo $IMG | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['uploads'][0]['key'])")
UPLOAD_URL=$(echo $IMG | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['uploads'][0]['upload_url'])")

# Step 2: Upload image directly to S3
curl -X PUT "$UPLOAD_URL" -H "Content-Type: image/jpeg" --data-binary @query.jpg

# Step 3: Search with the image key
curl -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "text_query": "find scenes with this person",
    "image_key": "'$IMAGE_KEY'",
    "search_type": "hybrid"
  }'
```

---

## After Search — Next Steps

- **Data Plates**: Save search results as a named plate for AI analysis → [data-plates.md](data-plates.md)
- **Agentic Chat**: Let the AI agent automatically search and analyze → [agentic-chat.md](agentic-chat.md)
