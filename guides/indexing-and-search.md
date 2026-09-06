# Indexing & Search

## Overview

Indexing takes your uploaded media, generates AI embeddings, and stores them in the vector database (Milvus) for semantic search.

### Full Pipeline

```
Upload → Preprocessing (Lambda, automatic) → Indexing (you trigger) → Search
```

- **Preprocessing** runs automatically after upload. Lambda splits video into 16-second chunks, normalizes images. No action needed.
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
  "media_breakdown": {"video": 8, "image": 3},
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
    "media_ids": [
      "s3://your-bucket/collections/col_xxx/uploads/lobby.mp4",
      "s3://your-bucket/collections/col_xxx/uploads/entrance.mp4"
    ]
  }'
```

> **Tags are no longer accepted here.** They are declared at upload time on `POST /api/v2/collections/{collection_id}/confirm-upload`, because they are written onto the search-index rows the moment preprocessing creates them. Sending `tags` to `/indexing/chunk-based` returns `400`. To change tags on already-indexed media use the async job at `POST /api/v2/collections/{collection_id}/tags` — see [collections.md](collections.md#tags). Metadata is declared the same way — see [collections.md](collections.md#metadata).

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
    "model": "video_only",
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

### Cancel an Indexing Job

Use the unified job cancellation endpoint to stop a running indexing job:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/jobs/cancel" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "indexing-chunk",
    "job_id": "'$INDEXING_ID'"
  }'
```

| `job_type` | When to use |
|---|---|
| `"indexing-chunk"` | Standard `video_only` or `multimodal` indexing job |
| `"indexing-qwen"` | Qwen3-VL indexing job |
| `"indexing-youtube"` | YouTube video indexing job (triggered via YouTube Search) |

Response:
```json
{
  "success": true,
  "data": {
    "job_id": "idx_xxxxxxxxxx",
    "job_type": "indexing-chunk",
    "status": "cancelled",
    "messages_removed": 48
  }
}
```

`messages_removed` is the number of pending queue messages purged. Cancellation removes unprocessed chunks from the queue; any chunks already indexed remain in the collection. Credits are only deducted for work that was completed before cancellation.

> Cancellation is queue-based. A chunk that has already started processing may still finish before the cancellation takes effect.

**Errors**: `400` for an unknown `job_type`, `403` if the job belongs to another user, `404` if the job does not exist.

### Model Constraints

| Capability | `video_only` (default) | `multimodal` |
|---|---|---|
| Video files | ✅ | ✅ |
| Image files | ❌ — rejected with 400 | ✅ |
| PDF files | ❌ — not supported | ❌ |
| Vision search | ✅ | ✅ |
| Audio/subtitle search | ✅ | ❌ |
| Image-query search | ❌ | ✅ |

---

## Search

Search is **asynchronous**. `POST /api/v2/search` returns `202` with a `search_job_id`; poll `GET /api/v2/search/jobs/{job_id}` until `status: "completed"`, at which point the response carries the first page of bucketed results. Pagination on an existing `search_id` skips the async submit and returns `200` with the page directly, because those results already exist.

### Basic Search

```bash
JOB=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "text_query": "person carrying a bag through a doorway",
    "search_type": "hybrid",
    "page_size": 20
  }')

SEARCH_JOB_ID=$(echo $JOB | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['search_job_id'])")

# Poll until completed
while true; do
  RESP=$(curl -s "$CREATIVAI_BASE_URL/api/v2/search/jobs/$SEARCH_JOB_ID" \
    -H "X-API-Key: $CREATIVAI_API_KEY")
  STATUS=$(echo $RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['status'])")
  echo "Search: $STATUS"
  [ "$STATUS" = "completed" ] && break
  [ "$STATUS" = "failed" ] && { echo "$RESP" | python3 -m json.tool; exit 1; }
  sleep 2
done
echo $RESP | python3 -m json.tool
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
| `search_id` | string | null | Re-use results from a prior search (pagination — returns `200` directly, no job needed) |
| `video_urls` | list[string] | null | Restrict to specific video S3 URIs |
| `tags` | list[string] | null | Restrict to media carrying **at least one** of these tags (OR semantics, case-insensitive) — see [filter by tags & metadata](#filter-by-tags-and-metadata) |
| `meta_filter` | object | null | AST filter over metadata keys — see [filter by tags & metadata](#filter-by-tags-and-metadata) |
| `plan_metadata` | bool | `false` | Let an LLM split `text_query` into its visual half and its metadata half (opt-in; costs one extra LLM call) |
| `use_weights` | bool | `false` | Enable custom vision/audio weighting |
| `vision_weight` | float | `0.5` | Vision vector weight (when `use_weights: true`) |
| `audio_weight` | float | `0.5` | Audio vector weight (when `use_weights: true`) |
| `refine_query` | bool | `false` | LLM rewrites query for better recall |
| `min_score` | float | null | Drop hits scoring below this floor. Buckets are still returned (may come back empty); scale is model-dependent (see below) |
| `include_scores` | bool | `false` | Return `scores` — the raw similarity of every hit before bucketing and `min_score` |
| `score_bins` | int | null | Return a `score_histogram` with this many equal-width bins to help calibrate `min_score` |
| `image_base64` | string | null | Base64 image for multimodal search (deprecated — prefer `image_key`) |
| `image_key` | string | null | S3 key of uploaded image (multimodal collections) |
| `video_key` | string | null | S3 key of an uploaded query clip (from `POST /search/upload-url`) — routes the search through the GPU video-query pipeline |
| `top_k` | int | `100` | Max results for a video-query search |

### Search Job Response (completed)

```json
{
  "success": true,
  "data": {
    "status": "completed",
    "search_id": "srch_xxxxxxxxxx",
    "search_job_id": "ssj_xxxxxxxxxx",
    "poll_url": "/api/v2/search/jobs/ssj_xxxxxxxxxx",
    "collection_id": "col_xxx",
    "total_items": 47,
    "page_number": 1,
    "total_pages": 3,
    "items_on_page": 20,
    "level_info": {
      "high":   {"count": 8,  "start_page": 1, "end_page": 1},
      "medium": {"count": 23, "start_page": 1, "end_page": 2},
      "low":    {"count": 16, "start_page": 2, "end_page": 3}
    },
    "high": [
      {
        "segment_id": "seg_abc123",
        "video_url": "https://presigned-cdn-url.../chunk.mp4",
        "video_s3_uri": "s3://bucket/col_xxx/uploads/lobby.mp4",
        "start_time": 32.0,
        "end_time": 48.0,
        "thumbnail_url": "https://presigned-url.../thumb.jpg",
        "score": 0.923,
        "tags": ["lobby", "camera-1"],
        "metadata": {"region": "eu", "duration": 24.5}
      }
    ],
    "medium": [ ],
    "low": [ ],
    "metadata_filter": {
      "applied": {"op": "and", "clauses": [{"key": "region", "cmp": "==", "value": "eu"}]},
      "planned": true,
      "text_query": "a crosswalk"
    }
  }
}
```

Results bucket into three relevance tiers. `high` = most relevant. `metadata_filter` is present only when tags or metadata were in play — see [What actually ran](#what-actually-ran).

### Pagination

Pass `search_id` to page through results without re-running the search — this returns `200` directly, no job polling:

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

### Filter by Tags and Metadata

Use `tags` and `meta_filter` on `POST /search` to narrow the vector search to the media that already match the exact half of the query — durations, regions, camera IDs, tag labels. Both are applied as **pre-filters**, so the vector search runs over the subset. On a `FLAT` vector index this is strictly a compute win and cannot change the ranking of the rows that survive.

**Tags** are OR-semantics: a chunk matches if its media carries at least one of the listed tags. Vocabulary comes from `GET /api/v2/collections/{collection_id}/tags`. Unknown tags simply match nothing — not an error.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "text_query": "person walking through a doorway",
    "tags": ["lobby", "entrance"]
  }'
```

**Metadata filters** are an AST — a group of clauses joined by `and` / `or`. Discover the available keys and their types with `GET /api/v2/collections/{collection_id}/metadata-schema`; a key the collection has never seen is a `400`.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "text_query": "a crosswalk",
    "meta_filter": {
      "op": "and",
      "clauses": [
        {"key": "duration", "cmp": "<",  "value": 30},
        {"key": "region",   "cmp": "in", "value": ["eu"]}
      ]
    }
  }'
```

Comparators depend on the key type:

| Type | Comparators |
|---|---|
| `number` | `== != < <= > >= in not_in between exists missing` |
| `string` | `== != in not_in starts_with ends_with substring not_substring exists missing`, plus `regex not_regex` on newer deployments |
| `bool` | `== != exists missing` |
| `enum` | `== != exists missing` |
| `list` | `contains not_contains contains_any contains_all exists missing` |
| `list` (all-numeric) | the above, plus `< <= > >=` (compare against `min`/`max` of the list) |

- `between` takes exactly two bounds and is inclusive; reversed bounds are swapped rather than rejected.
- `exists` / `missing` compile to `IS NOT NULL` / `IS NULL`.
- String matchers escape a literal `_` in the operand; an operand containing `%` or a backslash is **rejected with a 400** (Milvus `like` would silently over-match).
- On deployments where the Milvus server supports it (`regex` / `not_regex`), matching is partial and case-sensitive (RE2 syntax; lookaround and backreferences are not available).

A clause can also compare against a computed number:

```json
{"left": {"key": "duration"}, "cmp": "<", "right": {"op": "*", "args": [{"key": "reference_duration"}, 2]}}
```

Arithmetic is `number`-only and Milvus allows at most one operation over one key per clause — derived quantities over two different keys must be stored as their own number key at upload.

**Let the planner do it for you:** set `plan_metadata: true` and an LLM splits `text_query` into its visual part and the metadata clauses that fit the collection's registry. It costs one extra LLM call per search — opt-in — and it degrades to a plain search if the plan fails. `meta_filter` supplied explicitly wins over the planner.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "text_query": "clips under 30 seconds showing a crosswalk, collected in the EU",
    "plan_metadata": true
  }'
```

### What actually ran

A completed search that had metadata in play carries a `metadata_filter` block:

```json
"metadata_filter": {
  "applied": { "op": "and", "clauses": [ ... ] },
  "planned": true,
  "text_query": "a crosswalk"
}
```

`applied` is the AST that actually reached Milvus (`null` when nothing filtered). `planned` says whether the planner wrote it. `text_query` is the sentence that was actually embedded. If the planner had to drop a clause (e.g. an unsupported comparator), the operands of the dropped clause are folded back into `text_query` so the search does not silently become about something else.

`metadata_filter` is only present on the poll that completed the search; paginated replays (`search_id`) read stored pages and never see it.

### Score-based filtering

Vector similarity scores are model-dependent — an InternVideo2 hit at `0.35` is a strong match, a Qwen3-VL hit at `0.35` is only lukewarm. To pick a `min_score`, first ask the search to return its score distribution:

```json
{ "collection_id": "col_xxx", "text_query": "...", "score_bins": 10, "include_scores": true }
```

- `include_scores: true` returns `scores` — every hit's raw similarity, highest first, **before** bucketing and before `min_score`. Useful for building a slider.
- `score_bins: N` returns `score_histogram` — N equal-width bins spanning the full observed score range, each `{lower, upper, count}`. Pass a bin's `lower` back as `min_score` on the next request and you get exactly the sum of the counts from that bin upwards.

Reference thresholds (bucket edges):

| Model | Vision `high` / `med` / `low` | Audio `high` / `med` / `low` |
|---|---|---|
| InternVideo2 (`video_only`) | 0.35 / 0.32 / 0.29 | 0.65 / 0.61 / 0.58 |
| Qwen3-VL (`multimodal`) | 0.40 / 0.22 / 0.10 | — |

`min_score` is applied **before results are stored**, so every page you fetch afterwards reflects it.

### Image-Based Search (Multimodal Only)

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

# Step 3: Search with the image key — still async, poll GET /search/jobs/{id}
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

### Video-Query Search (Multimodal Only)

Use a short clip as the query — routed through the GPU video-query pipeline. Upload the clip via `POST /search/upload-url`, then pass the returned `video_key` on `POST /search`. The response is the same async job contract (`vsj_...` id), polled at `GET /search/jobs/{id}`.

```bash
# Step 1: Get a presigned upload URL for the query clip
UP=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/search/upload-url" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}')

VIDEO_KEY=$(echo $UP | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['key'])")
UPLOAD_URL=$(echo $UP | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['upload_url'])")

# Step 2: Upload clip directly to S3
curl -X PUT "$UPLOAD_URL" -H "Content-Type: video/mp4" --data-binary @query.mp4

# Step 3: Submit the video-query search
curl -X POST "$CREATIVAI_BASE_URL/api/v2/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "video_key": "'$VIDEO_KEY'",
    "top_k": 50
  }'
```

---

## After Search — Next Steps

- **Data Plates**: Save search results as a named plate for AI analysis → [data-plates.md](data-plates.md)
- **Agentic Chat**: Let the AI agent automatically search and analyze → [agentic-chat.md](agentic-chat.md)
