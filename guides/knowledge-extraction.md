# Knowledge Extraction

> **Version note:** All Knowledge Extraction endpoints use **`/api/v3/knowledge-extraction/...`**. Use v3 for all new integrations.

Knowledge Extraction uses AI to answer questions about every video segment in a data plate, producing a structured spreadsheet of AI-generated answers. It also includes a conversational chat interface for synthesizing insights from plate data.

## How It Works

1. **Add a Column** — Ask a question about every segment (e.g. "How many people are visible?")
2. **AI Processing** — The model analyzes each segment's video frames and answers the question
3. **Chat Query** — Ask follow-up questions; AI synthesizes answers from existing columns
4. **Export** — Download results as CSV

---

## Add a Column (Extract Information)

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/columns/add" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "question": "How many people are visible in this segment?",
    "model_version": "base"
  }'
```

Returns `202 Accepted` with `job_id`. Poll for completion.

### Add Multiple Questions at Once (concurrent)

Pass a list to process multiple questions in a single LLM call per segment:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/columns/add" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "question": [
      "How many people are visible?",
      "Is anyone wearing a safety vest?",
      "Describe the environment"
    ],
    "model_version": "base"
  }'
```

### With Reference Images

Provide reference images to help the model identify specific people or objects:

```bash
# Step 1: Upload reference images
IMG=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/chat/upload-images" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"count": 2, "content_type": "image/jpeg"}')

# PUT each image to its presigned upload_url...

# Step 2: Add column with image context
curl -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/columns/add" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "question": "Is the person in the reference image visible in this segment?",
    "model_version": "pro",
    "image_keys": ["uploads/session_xyz/img_0.jpg", "uploads/session_xyz/img_1.jpg"]
  }'
```

Maximum 10 reference images.

### Model Versions

| `model_version` | Speed | Accuracy | Best For |
|---|---|---|---|
| `"base"` | Fast (~2–5s/segment) | Good | High-volume extraction, simple questions |
| `"pro"` | Slower (~5–15s/segment) | Best | Complex visual reasoning, fine-grained details |

---

## Poll Extraction Job Status

```bash
curl "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/jobs/$JOB_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Response:
```json
{
  "success": true,
  "data": {
    "job_id": "ke_job_xxxxxxxxxx",
    "plate_id": "plt_xxx",
    "status": "completed",
    "question": "How many people are visible?",
    "total_segments": 50,
    "processed_segments": 50,
    "failed_segments": 0,
    "created_at": "2026-05-25T10:00:00Z",
    "completed_at": "2026-05-25T10:04:22Z"
  }
}
```

**Status values**: `"initiated"` → `"processing"` → `"completed"` / `"failed"`

---

## List Columns in a Plate

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/columns/list" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'"
  }'
```

---

## Remove a Column

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/columns/remove" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "column_name": "How many people are visible?"
  }'
```

---

## Chat Query (AI Synthesis)

Chat with your plate data using natural language. The AI:
1. Analyzes which columns already exist
2. Decides whether to reuse existing data or run new extraction
3. Synthesizes a comprehensive answer

### Upload Images for Chat

Attach images to provide visual context in a chat query:

```bash
# Step 1: Get presigned upload URLs
IMG=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/chat/upload-images" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 1,
    "content_type": "image/jpeg",
    "session_id": "optional-existing-session-id"
  }')

# Response includes list of {key, upload_url} objects
IMAGE_KEY=$(echo $IMG | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['uploads'][0]['key'])")
UPLOAD_URL=$(echo $IMG | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['uploads'][0]['upload_url'])")

# Step 2: Upload image directly to S3
curl -X PUT "$UPLOAD_URL" -H "Content-Type: image/jpeg" --data-binary @person.jpg
```

Supported MIME types: `image/jpeg`, `image/png`, `image/webp`, `image/gif`, `image/heic`

### Run a Chat Query

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/chat/query" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "query": "What percentage of segments show more than 2 people?",
    "model_version": "base",
    "aggregate_segments": true
  }'
```

Continue a previous conversation:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/chat/query" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "query": "Break that down by camera location",
    "model_version": "base",
    "chat_session_id": "'$CHAT_SESSION_ID'",
    "aggregate_segments": true
  }'
```

### Chat with Image Reference

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/chat/query" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "query": "In how many segments does this person appear?",
    "image_keys": ["'$IMAGE_KEY'"],
    "model_version": "pro"
  }'
```

### `aggregate_segments` Parameter

When `true` (default), consecutive segments from the same video with identical answers are merged during synthesis, removing duplication and improving statistical accuracy. Set to `false` for raw per-segment answers.

---

## Charts

Knowledge Extraction automatically generates chart-ready summaries:

```bash
# Charts for a specific plate
curl -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/charts/plate" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "limit": 50
  }'

# Charts across all plates in a collection
curl -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/charts/collection" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "limit": 100
  }'
```

---

## Chat Session Management

```bash
# List chat sessions for a plate
curl -X POST "$CREATIVAI_BASE_URL/api/v2/chat/sessions/list" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'", "plate_id": "'$PLATE_ID'"}'

# Get session with full message history
curl -X POST "$CREATIVAI_BASE_URL/api/v2/chat/sessions/get" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "'$CHAT_SESSION_ID'"}'

# Delete session
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/chat/sessions/$CHAT_SESSION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Update session title
curl -X POST "$CREATIVAI_BASE_URL/api/v2/chat/sessions/update-title" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "'$CHAT_SESSION_ID'", "title": "People Count Analysis"}'
```

---

## Practical Example: Full Extraction Workflow

```bash
# 1. Add multiple columns
JOB=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/columns/add" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "question": [
      "How many people are visible?",
      "Is anyone wearing personal protective equipment (PPE)?",
      "What is the approximate time of day based on lighting?"
    ],
    "model_version": "base"
  }')
JOB_ID=$(echo $JOB | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['job_id'])")

# 2. Poll until complete
while true; do
  STATUS=$(curl -s "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/jobs/$JOB_ID" \
    -H "X-API-Key: $CREATIVAI_API_KEY" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['status'])")
  echo "Status: $STATUS"
  [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] && break
  sleep 10
done

# 3. Query the results
curl -X POST "$CREATIVAI_BASE_URL/api/v3/knowledge-extraction/chat/query" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "query": "What percentage of segments have PPE compliance issues?",
    "model_version": "base"
  }'
```

---

## Next Steps

- Automate analysis with an AI agent → [agentic-chat.md](agentic-chat.md)
- Export results as CSV → [data-plates.md#csv-export](data-plates.md)
