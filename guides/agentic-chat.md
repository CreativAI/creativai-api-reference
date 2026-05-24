# Agentic Chat

Agentic Chat is a multi-step AI agent that reasons over your entire collection. Unlike the plate-level chat (which answers questions about existing data), the agent can autonomously search, create data plates, run knowledge extraction, browse the web, search YouTube, and synthesize answers — all driven by a single natural language message.

## How It Works

```
User Message
    │
    ▼
Agent Plans (execution_plan)
    │
    ├── refine_and_search  → searches your collection
    ├── create_plate       → creates a data plate from results
    ├── extract_knowledge  → runs KE jobs on segments
    ├── web_search         → browses the internet for context
    ├── youtube_search     → finds and indexes YouTube videos
    └── synthesize         → writes the final answer
    │
    ▼
SSE Stream → answer + data plates + charts
```

The agent runs in a persistent background task and streams results as Server-Sent Events (SSE). If the client disconnects, the task keeps running; reconnecting replays all buffered events.

---

## Session Management

### Create a Session

```bash
SESSION=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "title": "Security analysis Q1"
  }')

SESSION_ID=$(echo $SESSION | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['session_id'])")
echo "Session: $SESSION_ID"
```

Sessions are scoped to a collection. All searches, plates, and KE jobs are anchored to that collection.

### List / Get / Delete Sessions

```bash
# List all sessions (optionally filter by collection)
curl "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions?collection_id=$COLLECTION_ID&limit=20" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Get single session
curl "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Delete session
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### Load Chat History + Session State

This is the **only call the frontend needs on page load**:

```bash
curl "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/messages" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Returns:
- `messages` — full chat history (user, bot, interrupt cards)
- `session_state` — agent status, execution plan, context

`session_state.status` values:
| Status | Meaning |
|---|---|
| `"idle"` | Ready for a new message |
| `"running"` | Agent task in progress |
| `"waiting_for_input"` | Agent paused, needs user response |
| `"interrupted"` | Server restart mid-run; can resume |

---

## Chat (SSE Streaming)

```bash
curl -N -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "What are the most common activities captured in my collection?"}'
```

### SSE Event Types

| Event | Data | Description |
|---|---|---|
| `thinking` | string | Agent's internal reasoning step |
| `plan` | JSON | Execution plan created (list of steps) |
| `node_enter` | JSON | Agent entering a step (e.g. `refine_and_search`) |
| `node_exit` | JSON | Agent completed a step with outputs |
| `answer_delta` | string | Streaming answer text token |
| `answer` | string | Final complete answer |
| `search_feedback_required` | JSON | Agent paused; needs search tier guidance |
| `confirmation_required` | JSON | Agent needs user confirmation |
| `youtube_search_candidates_ready` | JSON | YouTube candidates ready for review |
| `visualization_ready` | JSON | Chart plates generated |
| `error` | string | Agent encountered an error |
| `complete` | — | Stream ended |

### Handling SSE in JavaScript

```javascript
const eventSource = new EventSource('/api/v2/agentic-chat/sessions/' + sessionId + '/stream', {
  headers: { 'X-API-Key': apiKey }
});

// Or use fetch for POST:
const response = await fetch(`/api/v2/agentic-chat/sessions/${sessionId}/chat`, {
  method: 'POST',
  headers: {
    'X-API-Key': apiKey,
    'Content-Type': 'application/json',
    'Accept': 'text/event-stream',
  },
  body: JSON.stringify({ message: userMessage }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const text = decoder.decode(value);
  // Parse SSE lines: "event: answer_delta\ndata: hello\n\n"
  for (const line of text.split('\n')) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6);
      console.log(data);
    }
  }
}
```

### Reconnecting to a Running Task

If the client disconnects while the agent is running, reconnect by sending an **empty message**:

```bash
curl -N -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": ""}'
```

This attaches to the live SSE stream and replays all buffered events.

---

## Interrupt Handling

The agent pauses at key decision points and waits for user input.

### Search Feedback Interrupt

After searching, the agent shows result counts and asks which tiers to use for analysis:

```
event: search_feedback_required
data: {"level_counts": {"high": 12, "medium": 34, "low": 89}, "total_segments": 135, "search_id": "srch_xxx"}
```

Respond in natural language:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/search-feedback" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "Use the top 20 high-relevance results"}'
```

Or simply include it in the next chat message — the agent auto-routes to the resume flow:

```bash
curl -N -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "Use top 20 high results"}'
```

### General Resume (after any interrupt)

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/resume" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "search_feedback",
    "message": "Use all high relevance results",
    "levels": ["high"],
    "top_k": 20
  }'
```

`action` values:
- `"search_feedback"` — provide search tier selection
- `"confirmation_response"` — answer a yes/no confirmation
- `"resume"` — resume after `interrupted` status (server restart recovery)

### YouTube Candidates Interrupt

If the agent performs a YouTube search, it pauses after discovering candidates:

```
event: youtube_search_candidates_ready
data: {"job_id": "yt_job_xxx", "total_candidates": 8, "query": "person carrying bag security"}
```

Review the candidates, then confirm to index:

```bash
# Review candidates
curl "$CREATIVAI_BASE_URL/api/v2/yt-search/$JOB_ID/candidates" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Remove unwanted candidates
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/yt-search/$JOB_ID/candidates/$VIDEO_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Confirm remaining candidates (triggers indexing and resumes agent)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/yt-search/$JOB_ID/confirm" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'
```

---

## Stop an Agent

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/stop" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Gracefully stops after the current step completes. The session state becomes `interrupted` and can be resumed later.

---

## Check Agent Status

```bash
curl "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/status" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Chat with Images (Multimodal Queries)

You can attach images to your chat messages (works with Qwen3-VL collections):

```bash
# Step 1: Upload image
IMG=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/knowledge-extraction/chat/upload-images" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"count": 1, "content_type": "image/jpeg", "session_id": "'$SESSION_ID'"}')

IMAGE_KEY=$(echo $IMG | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['uploads'][0]['key'])")
UPLOAD_URL=$(echo $IMG | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['uploads'][0]['upload_url'])")
curl -X PUT "$UPLOAD_URL" -H "Content-Type: image/jpeg" --data-binary @face.jpg

# Step 2: Chat with image reference
curl -N -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "message": "Search for segments where this person appears and tell me what they are doing",
    "user_image_urls": ["'$IMAGE_KEY'"]
  }'
```

---

## Specifying a Data Plate

Direct the agent to work with a specific plate:

```bash
curl -N -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "message": "Analyze the segments in this plate and summarize compliance issues",
    "plate_id": "'$PLATE_ID'",
    "model_version": "pro"
  }'
```

---

## ChatRequest Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `message` | string | required | User message (empty string = reconnect to running task) |
| `plate_id` | string | null | Direct agent to a specific plate |
| `model_version` | string | `"base"` | `"base"` or `"pro"` |
| `image_base64` | string | null | Base64 encoded image (deprecated, use `user_image_urls`) |
| `user_image_urls` | list[string] | null | S3 keys of uploaded images (max 10) |

---

## Full Example: End-to-End Agentic Workflow

```bash
# 1. Create session
SESSION_ID=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['data']['session_id'])")

# 2. Ask question — agent will search, create plate, extract knowledge
curl -N -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "Find all instances of someone entering through the rear entrance and tell me the times and how many people were involved"}' \
  | while IFS= read -r line; do
    if [[ $line == data:* ]]; then
      echo "${line#data: }"
    fi
  done

# 3. When search_feedback_required fires, respond:
curl -N -X POST "$CREATIVAI_BASE_URL/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "Use top 30 high relevance results"}'
```

---

## Web Search in Agentic Chat

The agent can browse the internet to supplement video analysis with factual context. This is automatic — mention web or internet in your query and the agent will decide whether web search is helpful.

Example queries that trigger web search:
- "What are the safety regulations for PPE in construction sites?"
- "Compare what I found in my footage with industry standards"

The agent uses web search results to enrich its final answer with external context.

---

## Notes for Frontend Integration

- On page load, call `GET /sessions/{id}/messages` — do **not** re-subscribe to SSE until the user sends a message
- An empty-string `message` in POST `/chat` means "reconnect to running task" (do not show in UI)
- Status `waiting_for_input` with `interrupt_type: "search_feedback"` should show a result count UI with an input for the user to specify how many results to use
- Status `interrupted` means the server restarted mid-run — show a "Resume" button that calls POST `/resume` with `action: "resume"`
- The `execution_plan` in `session_state` can be used to render a progress indicator
