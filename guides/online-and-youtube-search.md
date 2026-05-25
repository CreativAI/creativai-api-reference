# Online & YouTube Search

CreativAI provides two ways to discover and index YouTube content into your collections:

1. **Online Search** (`/api/v2/online-search/`) — Server-side YouTube discovery using the YouTube API. Fully automated, no browser extension needed.
2. **YouTube Search v2** (`/api/v2/yt-search-v2/`) — Browser extension-assisted search. The extension searches YouTube in the user's browser, then sends results back to the API for transcript fetching and indexing. **Use v2** — v1 is legacy.

Both flows require a **Qwen3-VL collection** (model: `"qwen"`). YouTube videos are processed through HLS streaming and indexed like regular uploads.

---

## Flow Comparison

| | Online Search | YouTube Search v2 (Extension) |
|---|---|---|
| Search mechanism | YouTube Data API (server-side) | Browser extension (client-side) |
| Browser required | No | Yes (Chrome extension) |
| Result quality | API rate-limited | Full YouTube search results |
| Best for | Automation, CI pipelines | Human-guided curation |

---

## Online Search (`/api/v2/online-search/`)

### Start a Search

```bash
JOB=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/online-search/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "query": "Find videos of construction site safety incidents with PPE violations"
  }')

JOB_ID=$(echo $JOB | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['job_id'])")
echo "Job ID: $JOB_ID"
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection_id` | string | Yes | Must be a Qwen3-VL collection (`model: "qwen"`) |
| `query` | string | Yes | Natural language query (3–2000 characters) |

**Response** (`202 Accepted`):
```json
{
  "success": true,
  "data": {
    "job_id": "os_job_abc123",
    "status": "initiated",
    "collection_id": "col_xxx"
  },
  "error": null
}
```

### Poll Status

```bash
curl "$CREATIVAI_BASE_URL/api/v2/online-search/$JOB_ID/status" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Status progression:
```
initiated → refining_query → searching_youtube → fetching_transcripts → finalizing → completed
```

After confirmation:
```
indexing_initiated → indexing_online_videos → inserting_the_data → indexing_completed
```

### Review Candidates

```bash
curl "$CREATIVAI_BASE_URL/api/v2/online-search/$JOB_ID/candidates" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Response:
```json
{
  "success": true,
  "data": {
    "job_id": "os_job_xxx",
    "total_candidates": 8,
    "candidates": [
      {
        "video_id": "dQw4w9WgXcQ",
        "title": "Construction Site Safety Training",
        "channel": "SafetyFirst Corp",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "thumbnail_url": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        "duration_seconds": 847,
        "has_transcript": true
      }
    ]
  }
}
```

### Remove Unwanted Candidates

```bash
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/online-search/$JOB_ID/candidates/$VIDEO_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### Run Additional Queries

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/online-search/$JOB_ID/search-more" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "OSHA safety violations on construction sites 2024"}'
```

### Confirm & Start Indexing

After reviewing candidates, trigger indexing:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/online-search/$JOB_ID/confirm" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'
```

---

## YouTube Search v2 (`/api/v2/yt-search-v2/`) — Recommended

> **Use v2 for all new integrations.** YouTube Search v1 (`/api/v2/yt-search/`) is legacy.

This flow uses the CreativAI Chrome extension. The extension searches YouTube in the user's browser, then submits results to the API for transcript fetching and indexing.

### Step 1 — Refine Query

```bash
REFINED=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search-v2/refine-query" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "query": "Find videos about AI in healthcare diagnosis"
  }')

JOB_ID=$(echo $REFINED | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['job_id'])")
echo "Job ID: $JOB_ID"
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection_id` | string | Yes | Must be a Qwen3-VL collection |
| `query` | string | Yes | Natural language query for YouTube search |

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "yt_job_abc123",
    "refined_queries": [
      "AI healthcare diagnosis 2025",
      "machine learning hospital patient diagnosis",
      "artificial intelligence radiology imaging"
    ]
  },
  "error": null
}
```

Use the `refined_queries` list in the Chrome extension to search YouTube.

### Step 2 — Submit Extension Results

The browser extension searches YouTube with the refined queries and submits results:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search-v2/$JOB_ID/submit-results" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "videos": [
      {
        "video_id": "abc123",
        "title": "AI in Healthcare: 2025 Advances",
        "url": "https://www.youtube.com/watch?v=abc123",
        "channel": "HealthTech Channel",
        "duration": "12:34",
        "thumbnail_url": "https://img.youtube.com/vi/abc123/maxresdefault.jpg"
      }
    ]
  }'
```

### Step 3 — Poll Status

```bash
curl "$CREATIVAI_BASE_URL/api/v2/yt-search-v2/$JOB_ID/status" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "yt_job_abc123",
    "status": "completed",
    "total_candidates": 8,
    "with_transcripts": 6
  },
  "error": null
}
```

### Step 4 — Review Candidates

```bash
curl "$CREATIVAI_BASE_URL/api/v2/yt-search-v2/$JOB_ID/candidates" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "candidates": [
      {
        "video_id": "abc123",
        "title": "AI in Healthcare: 2025 Advances",
        "channel": "HealthTech Channel",
        "url": "https://www.youtube.com/watch?v=abc123",
        "thumbnail_url": "https://img.youtube.com/vi/abc123/maxresdefault.jpg",
        "duration_seconds": 742,
        "has_transcript": true
      }
    ],
    "total_candidates": 8
  },
  "error": null
}
```

### Step 5 — Trim Candidates (optional)

```bash
# Keep only specific videos
curl -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search-v2/$JOB_ID/trim" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"keep_ids": ["abc123", "def456"]}'

# Or remove individual candidates
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/yt-search-v2/$JOB_ID/candidates/$VIDEO_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### Step 6 — Search More (optional)

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search-v2/$JOB_ID/search-more" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning hospital diagnosis 2025"}'
```

### Step 7 — Confirm and Index

**Option A: Index all remaining candidates**
```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search-v2/$JOB_ID/confirm" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'
```

**Option B: Index only selected URLs (v2 exclusive)**
```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search-v2/$JOB_ID/confirm-selected" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "video_urls": [
      "https://www.youtube.com/watch?v=abc123",
      "https://www.youtube.com/watch?v=def456"
    ]
  }'
```

---

## YouTube via Live Stream

For live/ongoing YouTube streams, use the live stream endpoint instead:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/youtube" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "source_url": "https://www.youtube.com/watch?v=LIVE_STREAM_ID",
    "name": "Conference Keynote",
    "periodic_indexing": 10
  }'
```

See [live-stream-guide.md](live-stream-guide.md) for details.

---

## In Agentic Chat

The Agentic Chat agent can automatically trigger YouTube searches when it determines external video data would help answer a question. It presents a `youtube_search_candidates_ready` interrupt for you to review and confirm.

See [agentic-chat.md](agentic-chat.md) for handling YouTube candidate interrupts.
