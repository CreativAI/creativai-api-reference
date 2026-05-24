# Online & YouTube Search

CreativAI provides two ways to discover and index YouTube content into your collections:

1. **Online Search** (`/api/v2/online-search/`) — Server-side YouTube discovery using the YouTube API. Fully automated, no browser extension needed.
2. **YouTube Search V1/V2** (`/api/v2/yt-search/`, `/api/v2/yt-search-v2/`) — Browser extension-assisted search. The extension searches YouTube in the user's browser, then sends results back to the API for transcript fetching and indexing.

Both flows require a **Qwen3-VL collection** (model: `"qwen"`). YouTube videos are processed through HLS streaming and indexed like regular uploads.

---

## Flow Comparison

| | Online Search | YT Search V1/V2 (Extension) |
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

`query` must be 3–2000 characters. The LLM converts it into optimized YouTube search queries.

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

## YouTube Search V1 (`/api/v2/yt-search/`)

This flow works with the CreativAI Chrome extension. The extension runs the YouTube search in the browser, then submits results to the API.

### Step 1: Server-side search (optional)

```bash
JOB=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search/search" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "query": "security camera footage person entering building"
  }')
JOB_ID=$(echo $JOB | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['job_id'])")
```

### Step 1 (alternative): Refine query, then search with extension

```bash
# Get LLM-optimized queries for the extension to use
REFINED=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search/refine-query" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "query": "Find videos about AI in healthcare"
  }')
JOB_ID=$(echo $REFINED | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['job_id'])")
# Returns list of refined_queries for the extension to search
```

### Step 2: Submit extension results

The browser extension searches YouTube using the refined queries and submits the raw results:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search/$JOB_ID/submit-results" \
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

### Step 3: Poll status

```bash
curl "$CREATIVAI_BASE_URL/api/v2/yt-search/$JOB_ID/status" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### Step 4: Review candidates

```bash
curl "$CREATIVAI_BASE_URL/api/v2/yt-search/$JOB_ID/candidates" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### Step 5: Trim candidates (keep only what you want)

```bash
# Keep only specific videos
curl -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search/$JOB_ID/candidates/trim" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"keep_ids": ["abc123", "def456"]}'

# Or remove individual candidates
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/yt-search/$JOB_ID/candidates/$VIDEO_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### Step 6: Search more (append results)

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search/$JOB_ID/search-more" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning hospital diagnosis 2025"}'
```

### Step 7: Confirm & index

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search/$JOB_ID/confirm" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'
```

---

## YouTube Search V2 (`/api/v2/yt-search-v2/`)

V2 is a streamlined version with the same extension-based flow but with an extra endpoint for confirming only selected videos:

```bash
# Confirm only selected videos (not all candidates)
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

All other endpoints match V1.

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

The Agentic Chat agent can automatically trigger YouTube searches when it determines external video data would help answer a question. It then presents a `youtube_search_candidates_ready` interrupt for you to review and confirm.

Example prompt that triggers YouTube search:
```
"Find YouTube videos about autonomous vehicle accidents from the last year and compare with my collection footage"
```

See [agentic-chat.md](agentic-chat.md) for handling YouTube candidate interrupts.
