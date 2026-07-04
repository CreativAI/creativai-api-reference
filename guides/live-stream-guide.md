# Live Stream

CreativAI Live Stream lets you ingest real-time video from any source — IP cameras, OBS, browsers, YouTube — index it continuously as it arrives, and run AI-powered knowledge extraction on live footage. Every live stream automatically creates a **Live Data Plate**, giving you a growing structured table of AI answers in real time.

**Typical use cases:**
- Security: monitor CCTV cameras for suspicious activity, alert when conditions are met
- Sports & events: capture live broadcasts for post-game analysis
- Industrial: real-time PPE compliance, safety monitoring
- Content: auto-summarize live meetings, webinars, YouTube streams
- Research: record and analyze behavioral studies frame by frame

---

## Architecture

```
Camera / Source
    │
    ├── RTSP  ─────┐
    ├── RTMP  ─────┤
    ├── SRT   ─────┤──→ MediaMTX (media server) ──→ S3 (16s segments) ──→ Indexing Pipeline
    ├── HLS   ─────┤                                                               │
    ├── WebRTC─────┤                                                               ▼
    └── YouTube ───┘                                                    Live Data Plate (real-time KE)
                                                                                   │
                                                                        ┌──────────┘
                                                                        ▼
                                                             Your App polls /sessions/{id}
                                                             or /data-plates/{plate_id}
```

**How it works:**
1. You create a **session** — a persistent logical container for the stream.
2. You start a stream on the session using one of the protocol endpoints.
3. MediaMTX (a media server) receives the stream, records it in 16-second segments, and uploads each segment to S3.
4. The backend preprocesses segments and queues them for **indexing** (embedding) every N minutes.
5. A live Qwen worker runs **knowledge extraction** on each segment in real time, writing answers to the Live Data Plate.
6. Your app polls the session or data plate to show results.

---

## Concepts

### Session Lifecycle

A session is the central resource. Its `status` field drives the UI:

| Status | Meaning |
|--------|---------|
| `waiting` | Session created; waiting for the media server and AI worker to start |
| `streaming` | Publisher connected, segments arriving, KE running |
| `paused` | Publisher disconnected (stream interrupted); session is preserved |
| `stopped` | Intentionally stopped via the API; all resources released |
| `error` | Fatal error — inspect `stop_reason` for details |

A paused session can be **resumed** — it retains its history, collection, and plate.

### Stream Protocols

| Protocol | Push or Pull | Best for |
|----------|-------------|----------|
| RTMP | Push (client → server) | OBS Studio, mobile encoders, ffmpeg push |
| RTSP | Pull (server → camera) | IP cameras, NVRs, DVRs |
| SRT | Both | Low-latency or unreliable networks, satellite |
| HLS | Pull | Phones (DroidCam, IP Webcam), existing HLS streams |
| WebRTC (WHIP) | Push (browser → server) | Browser webcam, lowest latency |
| YouTube | Pull | YouTube Live, VOD, Shorts |
| Auto-detect | Both | Let the server infer from the source URL |

### Live Data Plate

Every session has exactly one **Live Data Plate** — a structured table where each row is a 16-second video segment and each column is one of your AI analysis questions. The plate is populated in real time as segments arrive. You can:
- Query the plate via the standard Data Plates API
- Add new questions mid-stream with optional backfill of past segments
- Use the plate as the source for downstream search and analysis workflows

### Embedding Models

Choose a model when creating the collection — you cannot change it afterwards.

| `model` value | What it indexes | Best for |
|---------------|-----------------|----------|
| `"video_only"` (default) | Video frames + audio subtitles | CCTV, dashcam, surveillance |
| `"multimodal"` | Unified video + image embeddings | YouTube, mixed-media, content analysis |

### Two-Worker Readiness

Live streaming requires two cloud workers before frames can flow:

1. **MediaMTX server** — media ingest server (~30–60 s cold start)
2. **Qwen AI worker** — GPU inference pod that runs knowledge extraction (~3–5 min cold start)

Poll `GET /sessions/{id}/mediamtx-status`. Proceed only when `all_ready: true` — this means both workers are up **and** the publish/playback URLs are active.

---

## Quick Start: End-to-End in 4 Steps

```bash
export CREATIVAI_BASE_URL="https://creativai-apis.com"
export CREATIVAI_API_KEY="sk_live_..."

# Step 1: Start an RTSP stream (creates session + collection automatically)
RESULT=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/rtsp" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "lobby-camera-live",
    "source_url": "rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101",
    "name": "Lobby Camera",
    "user_query": "Detect unusual activity or unauthorized persons",
    "periodic_indexing": 5
  }')

SESSION_ID=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['session_id'])")
PLATE_ID=$(echo $RESULT  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['plate_id'])")
echo "Session: $SESSION_ID  Plate: $PLATE_ID"

# Step 2: Poll until both workers are ready (typically 3–5 min first time)
while true; do
  ALL_READY=$(curl -s \
    "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/mediamtx-status" \
    -H "X-API-Key: $CREATIVAI_API_KEY" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['all_ready'])")
  echo "Ready: $ALL_READY"
  [ "$ALL_READY" = "True" ] && break
  sleep 10
done

# Step 3: Check session status — should now be "streaming"
curl -s "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['status'], d['plate_id'])"

# Step 4: Stop the stream when done
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/stop" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

> **Tip:** The protocol stream endpoints (`POST /stream/rtsp`, `/stream/rtmp`, etc.) create a session and start the stream in a single call. You do **not** need to call `POST /sessions` separately unless you want to pre-create a session before the source is ready.

---

## Session Management

### Create Session

`POST /api/v2/live-stream/sessions`

Creates a session in `waiting` status. Useful when you want to pre-create a session and warm up the workers before the stream source is ready. For most integrations, use a protocol stream endpoint instead — they create the session in one call.

**Request body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | null | Human-readable label (e.g. `"Front Door Camera"`) |
| `user_query` | string | null | Natural-language query auto-refined into analysis questions |
| `collection_name` | string | null | Create a new collection — mutually exclusive with `collection_id` |
| `collection_id` | string | null | Use an existing collection — mutually exclusive with `collection_name` |
| `model` | string | `"video_only"` | Embedding model: `"video_only"` or `"multimodal"` |
| `periodic_indexing` | int\|null | `5` | Index every N minutes; `null` disables periodic indexing |

**cURL:**
```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Front Door Camera",
    "user_query": "Alert me to people carrying bags",
    "collection_name": "front-door-live",
    "model": "video_only",
    "periodic_indexing": 5
  }'
```

**TypeScript:**
```typescript
const response = await fetch(`${BASE_URL}/api/v2/live-stream/sessions`, {
  method: "POST",
  headers: { "X-API-Key": API_KEY, "Content-Type": "application/json" },
  body: JSON.stringify({
    name: "Front Door Camera",
    user_query: "Alert me to people carrying bags",
    collection_name: "front-door-live",
    model: "video_only",
    periodic_indexing: 5,
  }),
});
const { data } = await response.json();
const sessionId = data.session_id; // "sess_abc123"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "name": "Front Door Camera",
    "status": "waiting",
    "query": "Alert me to people carrying bags",
    "collection_id": "col_xyz789",
    "segment_duration": 16.0,
    "periodic_indexing_minutes": 5
  },
  "error": null
}
```

---

### List Sessions

`GET /api/v2/live-stream/sessions`

Returns all live-stream sessions for the authenticated user, ordered newest first. Optionally filter by collection.

**Query parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `collection_id` | string | Filter to sessions for a specific collection |

**cURL:**
```bash
# All sessions
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Filter by collection
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions?collection_id=$COLLECTION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "session_id": "sess_abc123",
        "name": "Front Door Camera",
        "status": "streaming",
        "query": ["Are any persons approaching?", "Are bags visible?"],
        "collection_id": "col_xyz789",
        "total_segments": 42,
        "created_at": "2026-07-04T08:00:00Z"
      }
    ]
  },
  "error": null
}
```

---

### Get Session

`GET /api/v2/live-stream/sessions/{session_id}`

Returns full session details including playback URLs, plate ID, and the last 50 segment records.

**cURL:**
```bash
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "name": "Front Door Camera",
    "status": "streaming",
    "query": ["Are any persons approaching?", "Are bags visible?"],
    "total_segments": 42,
    "created_at": "2026-07-04T08:00:00Z",
    "stream_started_at": "2026-07-04T08:02:15Z",
    "hls_playback_url": "https://mediamtx.creativai.io/live/sess_abc123/index.m3u8",
    "whip_url": "https://creativai-apis.com/api/v2/live-stream/sessions/sess_abc123/whip?token=sk_live_...",
    "whep_url": "https://creativai-apis.com/api/v2/live-stream/sessions/sess_abc123/whep?token=sk_live_...",
    "plate_id": "plate_def456",
    "live_data_plate": true,
    "stop_reason": null,
    "segments": [
      {
        "segment_id": "seg_001",
        "session_id": "sess_abc123",
        "segment_name": "chunk_00001.mp4",
        "duration_seconds": 16.0,
        "frame_count": 480,
        "start_time": "2026-07-04T08:02:15Z",
        "end_time": "2026-07-04T08:02:31Z",
        "status": "indexed",
        "analysis_result": null,
        "error": null
      }
    ]
  },
  "error": null
}
```

> The `whip_url` and `whep_url` include your API key as a `?token=` query parameter — safe to use directly in browser WebRTC clients that cannot send custom headers.

---

### Stop Session

`POST /api/v2/live-stream/sessions/{session_id}/stop`

Stops an active stream. The session transitions to `stopped`. The collection, indexed segments, and data plate are preserved — you can still search and query the content.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/stop" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "status": "stopped",
    "total_segments": 42
  },
  "error": null
}
```

---

### Resume Session

`POST /api/v2/live-stream/sessions/{session_id}/resume`

Resumes a `paused`, `waiting`, or `stopped` session. A fresh MediaMTX path is generated and the media server restarts. The session transitions back to `waiting`. Once the publisher reconnects, it moves to `streaming`. Segment numbering and the data plate continue from where they left off.

**When to use:**
- The stream source went offline and reconnected after the session paused
- You intentionally stopped a session and want to restart without losing history
- The MediaMTX server restarted and the session needs to re-register its path

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/resume" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**TypeScript:**
```typescript
const res = await fetch(
  `${BASE_URL}/api/v2/live-stream/sessions/${sessionId}/resume`,
  { method: "POST", headers: { "X-API-Key": API_KEY } }
);
const { data } = await res.json();
// data.status === "waiting"
// Poll /mediamtx-status until all_ready === true, then reconnect your source
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "path": "live/new-path-456",
    "status": "waiting",
    "hls_playback_url": null,
    "total_segments": 42,
    "plate_id": "plate_def456",
    "live_data_plate": true,
    "worker_ready": false,
    "worker_message": "Live worker is starting. GPU pod is loading the model (~3-5 min)."
  },
  "error": null
}
```

> After resuming, poll `/sessions/{id}/mediamtx-status` until `all_ready: true` before directing the source to publish again.

---

### Delete Session

`DELETE /api/v2/live-stream/sessions/{session_id}`

Permanently deletes a session, stops all active resources, and removes session records. **This action is irreversible.** The collection and its indexed content are **not** deleted — only the live session record and its raw segments.

```bash
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "status": "deleted",
    "total_segments_removed": 42
  },
  "error": null
}
```

---

### Add Analysis Questions

`POST /api/v2/live-stream/sessions/{session_id}/add-questions`

Adds new AI analysis questions to an active session. New columns are added to the Live Data Plate immediately.

- **Default behavior (`backfill: false`):** Only future segments will answer the new questions; past segments are marked as `"skipped"`.
- **With `backfill: true`:** Past segments are also processed (they show `"generating"` while the KE pipeline runs).

Duplicate questions (already present in the session) are silently ignored.

**Request body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `questions` | string[] | required | New analysis questions to add |
| `backfill` | boolean | `false` | If true, process existing segments for the new questions |

```bash
# Add questions — future segments only
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/add-questions" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "questions": [
      "Are there any safety hazards visible?",
      "How many people are present?",
      "Is PPE (hard hat, vest) being worn?"
    ]
  }'

# Add a question and apply it retroactively to all past segments
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/add-questions" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "questions": ["Is a forklift visible?"],
    "backfill": true
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "query": ["Are any persons approaching?", "Are bags visible?", "Are there any safety hazards visible?"],
    "plate_id": "plate_def456",
    "message": "Questions updated — 3 total"
  },
  "error": null
}
```

---

### Indexing Job Status

`GET /api/v2/live-stream/sessions/{session_id}/indexing-jobs`

Returns the current indexing state for a session: segment count, last indexing job ID, and periodic schedule. With `periodic_indexing` set, a new job triggers every N minutes to embed all unindexed segments. You can also trigger indexing manually via `POST /api/v2/indexing/chunk-based` using the session's `collection_id`.

```bash
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/indexing-jobs" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "collection_id": "col_xyz789",
    "last_indexing_id": "idx_ghi012",
    "periodic_indexing_minutes": 5,
    "segment_count": 42,
    "status": "streaming"
  },
  "error": null
}
```

---

## Readiness Polling

When a stream starts, two workers need to be ready before video can flow. Poll these endpoints to know when to start the source.

### Worker Status

`GET /api/v2/live-stream/sessions/{session_id}/worker-status`

Returns the readiness of the Qwen GPU worker (the AI inference pod). Cold-start is approximately 3–5 minutes the first time. Poll every 10 seconds while `worker_ready` is `false`.

```bash
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/worker-status" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response (starting):**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "worker_ready": false,
    "whip_url": null,
    "whep_url": null,
    "plate_id": "plate_def456",
    "hls_playback_url": null,
    "estimated_wait": "3-5 minutes",
    "message": "Live worker is starting. GPU pod is loading the model (~3-5 min)."
  }
}
```

**Response (ready):**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "worker_ready": true,
    "whip_url": "https://creativai-apis.com/api/v2/live-stream/sessions/sess_abc123/whip?token=sk_live_...",
    "whep_url": "https://creativai-apis.com/api/v2/live-stream/sessions/sess_abc123/whep?token=sk_live_...",
    "plate_id": "plate_def456",
    "hls_playback_url": "https://mediamtx.creativai.io/live/sess_abc123/index.m3u8",
    "estimated_wait": null,
    "message": "Live worker is ready."
  }
}
```

---

### MediaMTX Status

`GET /api/v2/live-stream/sessions/{session_id}/mediamtx-status`

The **primary readiness endpoint.** Returns readiness of both the MediaMTX server and the AI worker. `all_ready: true` means both workers are up **and** the publish/playback URLs are active. Only proceed when `all_ready` is `true`.

```bash
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/mediamtx-status" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response (starting):**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "mediamtx_ready": false,
    "worker_ready": false,
    "all_ready": false,
    "mediamtx_api_url": null,
    "mediamtx_public_ip": null,
    "mediamtx_task_arn": null,
    "hls_playback_url": null,
    "whip_url": null,
    "whep_url": null,
    "estimated_wait": "30-60 seconds",
    "message": "MediaMTX server is starting up (~30-60 sec)."
  }
}
```

**Response (all ready):**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "mediamtx_ready": true,
    "worker_ready": true,
    "all_ready": true,
    "mediamtx_api_url": "http://10.0.1.50:9997",
    "mediamtx_public_ip": "34.100.200.50",
    "mediamtx_task_arn": "arn:aws:ecs:us-east-1:123456789:task/...",
    "hls_playback_url": "https://mediamtx.creativai.io/live/sess_abc123/index.m3u8",
    "whip_url": "https://creativai-apis.com/api/v2/live-stream/sessions/sess_abc123/whip?token=sk_live_...",
    "whep_url": "https://creativai-apis.com/api/v2/live-stream/sessions/sess_abc123/whep?token=sk_live_...",
    "estimated_wait": null,
    "message": "MediaMTX server is ready."
  }
}
```

### Readiness Polling — TypeScript Pattern

```typescript
async function waitUntilReady(
  sessionId: string,
  apiKey: string,
  timeoutMs = 10 * 60 * 1000 // 10 minutes max
): Promise<{ hlsPlaybackUrl: string; whipUrl: string; whepUrl: string }> {
  const BASE_URL = "https://creativai-apis.com";
  const INTERVAL_MS = 10_000;
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const res = await fetch(
      `${BASE_URL}/api/v2/live-stream/sessions/${sessionId}/mediamtx-status`,
      { headers: { "X-API-Key": apiKey } }
    );
    const { data } = await res.json();

    console.log(
      `[readiness] mediamtx=${data.mediamtx_ready} worker=${data.worker_ready} all=${data.all_ready}`
    );

    if (data.all_ready) {
      return {
        hlsPlaybackUrl: data.hls_playback_url,
        whipUrl: data.whip_url,
        whepUrl: data.whep_url,
      };
    }
    await new Promise((r) => setTimeout(r, INTERVAL_MS));
  }
  throw new Error(`Timed out waiting for session ${sessionId} to become ready`);
}
```

---

## Protocol-Specific Stream Endpoints

All stream endpoints accept the following parameters. A new session and MediaMTX path are created automatically unless `session_id` is provided.

### Common Parameters

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `collection_name` | string | — | Create a new collection (mutually exclusive with `collection_id`) |
| `collection_id` | string | — | Use an existing collection (mutually exclusive with `collection_name`) |
| `name` | string | null | Human-readable stream name |
| `user_query` | string | null | Natural-language query auto-refined into analysis questions |
| `model` | string | `"video_only"` | `"video_only"` or `"multimodal"` |
| `periodic_indexing` | int\|null | `5` | Index every N minutes; `null` disables |
| `source_url` | string | null | Pull URL for the stream source (leave empty for push protocols) |
| `max_fps` | int | `30` | FPS cap 1–60 — reduce for low-bandwidth sources |
| `session_id` | string | null | Associate with an existing session instead of creating a new one |
| `cookies` | string | null | Netscape-format cookies for YouTube authenticated content |

### Common Response Fields

| Field | Description |
|-------|-------------|
| `session_id` | Use to poll readiness and manage the session |
| `collection_id` | The collection receiving indexed segments |
| `path` | MediaMTX stream path (e.g. `live/abc123`) |
| `protocol` | Detected/used protocol (`rtmp`, `rtsp`, etc.) |
| `publish_url` | URL to push to (RTMP/SRT push streams) — `null` for pull |
| `hls_playback_url` | HLS playback URL — `null` until server is ready |
| `whip_url` | WebRTC publish URL — `null` until server is ready |
| `whep_url` | WebRTC playback URL — `null` until server is ready |
| `plate_id` | Live Data Plate ID |
| `live_data_plate` | Always `true` |
| `status` | Session status (`"waiting"` initially) |
| `worker_ready` | Whether the AI worker is immediately ready |
| `worker_message` | Human-readable worker state description |

---

### Auto-Detect Protocol

`POST /api/v2/live-stream/stream`

Infers the protocol from `source_url`. If no URL is provided, defaults to RTMP push.

**Protocol detection rules:**
- `rtmp://` / `rtmps://` → RTMP
- `rtsp://` / `rtsps://` → RTSP
- `srt://` → SRT
- URL ending in `.m3u8` or `.ts` → HLS
- `youtube.com` / `youtu.be` → YouTube
- Any other `http://` or `https://` → HLS (auto-bridged via ffmpeg)
- Bare IP or hostname without scheme → RTSP
- No URL provided → RTMP push

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "auto-stream",
    "source_url": "rtsp://192.168.1.100:554/stream",
    "name": "Auto-detected camera",
    "user_query": "Detect people and vehicles"
  }'
```

---

### RTMP — OBS, Encoders, ffmpeg Push

`POST /api/v2/live-stream/stream/rtmp`

Returns a `publish_url`. Configure your encoder to push to this URL. RTMPS (`rtmps://`) is also supported.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/rtmp" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "obs-recordings",
    "name": "OBS Studio Stream",
    "user_query": "Identify key events and speakers"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "collection_id": "col_xyz789",
    "path": "live/sess_abc123",
    "protocol": "rtmp",
    "publish_url": "rtmp://34.100.200.50:1935/live/sess_abc123",
    "hls_playback_url": null,
    "plate_id": "plate_def456",
    "live_data_plate": true,
    "status": "waiting",
    "worker_ready": false,
    "worker_message": "Live worker is starting. GPU pod is loading the model (~3-5 min)."
  }
}
```

**OBS Studio setup:**
1. Settings → Stream → Service: `Custom...`
2. Server: `rtmp://34.100.200.50:1935/live/`
3. Stream Key: `sess_abc123` (everything after the last `/` in `publish_url`)
4. Click **Start Streaming** only after `all_ready: true`

**ffmpeg:**
```bash
ffmpeg -re -i input.mp4 -c copy -f flv rtmp://34.100.200.50:1935/live/sess_abc123
```

---

### RTSP — IP Cameras, NVRs

`POST /api/v2/live-stream/stream/rtsp`

Provide `source_url` pointing to your camera — the server pulls the stream. HTTP/MJPEG sources (e.g. phone cameras via DroidCam) are automatically detected and bridged via ffmpeg.

```bash
# Hikvision IP camera
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/rtsp" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "lobby-cams",
    "source_url": "rtsp://admin:Password123@192.168.1.100:554/Streaming/Channels/101",
    "name": "Hikvision Lobby Camera",
    "user_query": "Is there any suspicious activity?"
  }'

# DroidCam (Android phone camera)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/rtsp" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "phone-cam",
    "source_url": "http://192.168.1.9:4747/video",
    "name": "DroidCam Phone"
  }'
```

> For push mode, omit `source_url` — the response includes an RTSP URL the client pushes to. RTSPS (`rtsps://`) is supported for encrypted pull.

---

### SRT — Low-Latency / Broadcast

`POST /api/v2/live-stream/stream/srt`

SRT (Secure Reliable Transport) is ideal for broadcast ingest over unstable networks or satellite uplinks.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/srt" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "broadcast-feed",
    "source_url": "srt://192.168.1.50:7001",
    "name": "Stadium SRT Feed"
  }'
```

**ffmpeg SRT push:**
```bash
ffmpeg -re -i input.mp4 \
  -c:v libx264 -preset veryfast -c:a aac \
  -f mpegts "srt://34.100.200.50:8890?streamid=publish:live/sess_abc123"
```

---

### HLS / HTTP Sources

`POST /api/v2/live-stream/stream/hls`

For existing HLS streams, MJPEG sources, or any HTTP video URL. The server pulls and re-segments the stream.

```bash
# Existing HLS stream
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/hls" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "conference-live",
    "source_url": "https://streaming.example.com/live/event.m3u8",
    "name": "Live Conference"
  }'

# IP Webcam app (Android)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/hls" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "android-cam",
    "source_url": "http://192.168.1.10:8080/video",
    "name": "IP Webcam Android"
  }'
```

---

### WebRTC — Browser Camera (WHIP)

`POST /api/v2/live-stream/stream/webrtc`

Lowest-latency option. The browser publishes via WebRTC WHIP using `getUserMedia()`. No `source_url` needed. Response includes `whip_url` (publish) and `whep_url` (playback).

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/webrtc" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "webcam-session",
    "name": "Browser Webcam",
    "user_query": "Track presenter activity and any slides visible on screen"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "protocol": "webrtc",
    "whip_url": "https://creativai-apis.com/api/v2/live-stream/sessions/sess_abc123/whip?token=sk_live_...",
    "whep_url": "https://creativai-apis.com/api/v2/live-stream/sessions/sess_abc123/whep?token=sk_live_...",
    "hls_playback_url": null,
    "plate_id": "plate_def456",
    "status": "waiting",
    "worker_ready": false
  }
}
```

**Browser publisher (JavaScript):**
```javascript
// 1. Start the stream
const { data: session } = await (await fetch(`${BASE_URL}/api/v2/live-stream/stream/webrtc`, {
  method: "POST",
  headers: { "X-API-Key": API_KEY, "Content-Type": "application/json" },
  body: JSON.stringify({ collection_name: "webcam", name: "My Webcam" }),
})).json();

// 2. Poll until ready, then fetch the active WHIP URL
await waitUntilReady(session.session_id, API_KEY); // see Readiness Polling section
const { data: live } = await (await fetch(
  `${BASE_URL}/api/v2/live-stream/sessions/${session.session_id}`,
  { headers: { "X-API-Key": API_KEY } }
)).json();

// 3. Capture the camera
const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });

// 4. Create peer connection and publish via WHIP
const pc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] });
stream.getTracks().forEach((track) => pc.addTrack(track, stream));

const offer = await pc.createOffer();
await pc.setLocalDescription(offer);

// Wait for all ICE candidates before sending offer
await new Promise((resolve) => {
  if (pc.iceGatheringState === "complete") return resolve();
  pc.addEventListener("icegatheringstatechange", () => {
    if (pc.iceGatheringState === "complete") resolve();
  });
});

const whipRes = await fetch(live.whip_url, {
  method: "POST",
  headers: { "Content-Type": "application/sdp" },
  body: pc.localDescription.sdp,
});
const answerSdp = await whipRes.text();
await pc.setRemoteDescription({ type: "answer", sdp: answerSdp });
console.log("Publishing WebRTC stream!");
```

**Browser viewer (WHEP playback):**
```javascript
const pc = new RTCPeerConnection({ iceServers: [{ urls: "stun:stun.l.google.com:19302" }] });
pc.addTransceiver("video", { direction: "recvonly" });
pc.addTransceiver("audio", { direction: "recvonly" });

pc.ontrack = (event) => {
  document.getElementById("live-video").srcObject = event.streams[0];
};

const offer = await pc.createOffer();
await pc.setLocalDescription(offer);

await new Promise((resolve) => {
  if (pc.iceGatheringState === "complete") return resolve();
  pc.addEventListener("icegatheringstatechange", () => {
    if (pc.iceGatheringState === "complete") resolve();
  });
});

const whepRes = await fetch(live.whep_url, {
  method: "POST",
  headers: { "Content-Type": "application/sdp" },
  body: pc.localDescription.sdp,
});
const answerSdp = await whepRes.text();
await pc.setRemoteDescription({ type: "answer", sdp: answerSdp });
```

---

### YouTube Live / VOD

`POST /api/v2/live-stream/stream/youtube`

Resolves the YouTube URL via yt-dlp (no YouTube API key required for public videos) and ingests through MediaMTX. Works with live streams, VODs, and Shorts. `source_url` is required.

```bash
# Public YouTube video (no cookies needed)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/youtube" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "youtube-conference",
    "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "name": "Conference Recording",
    "user_query": "Summarize key topics and identify speakers",
    "periodic_indexing": 10
  }'

# Age-restricted or private video (provide Netscape-format cookies)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/youtube" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "private-recordings",
    "source_url": "https://www.youtube.com/watch?v=PRIVATE_VIDEO_ID",
    "cookies": "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tFALSE\t0\tSID\tABC123..."
  }'
```

**Supported URL formats:**
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/live/VIDEO_ID`

> **Cookies:** Export cookies from your YouTube-authenticated browser session using a browser extension (e.g. "cookies.txt for YouTube"). Provide the full Netscape-format cookie file content as the `cookies` string.

---

## WebRTC Signaling Proxy (WHIP / WHEP)

The WHIP and WHEP proxy endpoints let browsers publish and view WebRTC streams through the CreativAI API server over TLS. Your browser never makes plain HTTP requests to MediaMTX directly. The `whip_url` and `whep_url` returned by all session endpoints already point to these proxy endpoints with your API key embedded as `?token=`.

> **Authentication:** These endpoints use `?token=YOUR_API_KEY` because browsers cannot send custom headers during WebRTC SDP exchange.

### WHIP — Publish (Browser → Server)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v2/live-stream/sessions/{session_id}/whip?token=KEY` | Send SDP offer; receive SDP answer + `Location` header with resource ID |
| `PATCH` | `/api/v2/live-stream/sessions/{session_id}/whip/{resource_id}?token=KEY` | Send trickle ICE candidates |
| `DELETE` | `/api/v2/live-stream/sessions/{session_id}/whip/{resource_id}?token=KEY` | Teardown (stop publishing) |

### WHEP — Playback (Server → Browser)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v2/live-stream/sessions/{session_id}/whep?token=KEY` | Send SDP offer; receive SDP answer + `Location` header |
| `PATCH` | `/api/v2/live-stream/sessions/{session_id}/whep/{resource_id}?token=KEY` | Send trickle ICE candidates |
| `DELETE` | `/api/v2/live-stream/sessions/{session_id}/whep/{resource_id}?token=KEY` | Teardown (stop viewing) |

> These follow the standard WHIP/WHEP protocol. Any WHIP/WHEP-compatible library works out of the box with the `whip_url` / `whep_url` values from the session response.

---

## MediaMTX Management

Endpoints for inspecting and monitoring the MediaMTX media server.

### Health Check

`GET /api/v2/live-stream/mediamtx/health`

No authentication required. Returns HTTP 503 if MediaMTX is unreachable.

```bash
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/mediamtx/health"
```

**Response:**
```json
{ "success": true, "data": { "status": "healthy" } }
```

---

### MediaMTX Configuration

`GET /api/v2/live-stream/mediamtx/config`

Returns current MediaMTX endpoint configuration: API port, RTMP/RTSP/SRT/WebRTC/HLS URLs. Useful for debugging connectivity.

```bash
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/mediamtx/config" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

### List Active Streams

`GET /api/v2/live-stream/mediamtx/streams`

Lists all active paths on the MediaMTX server, annotated with their mapped session IDs.

```bash
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/mediamtx/streams" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "streams": [
      { "path": "live/sess_abc123", "session_id": "sess_abc123", "ready": true, "readers": 2 }
    ]
  }
}
```

---

### Get Stream by Path

`GET /api/v2/live-stream/mediamtx/streams/{path}`

Returns the status of a specific MediaMTX path.

```bash
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/mediamtx/streams/live/sess_abc123" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

### List Connections by Protocol

`GET /api/v2/live-stream/mediamtx/connections/{protocol}`

Lists active connections for a specific protocol. Supported: `rtsp`, `rtmp`, `srt`, `hls`, `webrtc`.

```bash
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/mediamtx/connections/rtmp" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "protocol": "rtmp",
    "connections": [
      { "id": "conn_1", "state": "publish", "path": "live/sess_abc123" }
    ]
  }
}
```

---

### Connection Summary

`GET /api/v2/live-stream/mediamtx/connections/summary`

Aggregated connection counts across all protocols. Useful for monitoring dashboards.

```bash
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/mediamtx/connections/summary" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": { "rtsp": 2, "rtmp": 1, "srt": 0, "hls": 5, "webrtc": 3, "total": 11 }
}
```

---

## Common Source URL Reference

| Source type | Example URL | Recommended endpoint |
|-------------|-------------|----------------------|
| Hikvision IP camera | `rtsp://admin:pass@192.168.1.100:554/Streaming/Channels/101` | `/stream/rtsp` |
| Dahua IP camera | `rtsp://admin:pass@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0` | `/stream/rtsp` |
| Axis camera | `rtsp://root:pass@192.168.1.102/axis-media/media.amp` | `/stream/rtsp` |
| DroidCam (Android) | `http://192.168.1.9:4747/video` | `/stream/rtsp` |
| IP Webcam (Android) | `http://192.168.1.10:8080/video` | `/stream/hls` |
| OBS Studio (push) | _(use `publish_url` from RTMP response)_ | `/stream/rtmp` |
| ffmpeg RTMP push | `rtmp://HOST:1935/live/SESSION_ID` | `/stream/rtmp` |
| ffmpeg SRT push | `srt://HOST:8890?streamid=publish:live/SESSION_ID` | `/stream/srt` |
| YouTube live | `https://www.youtube.com/watch?v=VIDEO_ID` | `/stream/youtube` |
| YouTube Shorts | `https://youtu.be/SHORT_ID` | `/stream/youtube` |
| Generic HLS | `https://example.com/live/index.m3u8` | `/stream/hls` |
| Browser webcam | _(no URL — browser pushes via WHIP)_ | `/stream/webrtc` |

---

## Session State Machine

```
                   POST /stream/* or POST /sessions
                               │
                               ▼
                           WAITING ◄─── POST /sessions/{id}/resume
                               │
                   Publisher connects (runOnReady webhook)
                               │
                               ▼
           ┌──────────── STREAMING ──────────────────────────┐
           │                   │                             │
Publisher disconnects    POST /stop              POST /sessions/{id}/stop
(runOnNotReady webhook)        │                             │
           │                   ▼                             │
           ▼               STOPPED ◄────────────────────────┘
        PAUSED                 │
           │           DELETE /sessions/{id}
           │                   │
POST /sessions/{id}/resume     ▼
           │               (deleted)
           └──────────────────▲
```

| Transition | From → To |
|-----------|-----------|
| Stream endpoint called | — → `waiting` |
| Publisher connects | `waiting` → `streaming` |
| Publisher disconnects | `streaming` → `paused` |
| `POST /stop` | any active → `stopped` |
| `POST /resume` | `stopped` / `paused` / `waiting` → `waiting` |
| `DELETE /sessions/{id}` | any → deleted |

---

## Tier Limits

Live streaming is gated by subscription plan:

| Plan | Concurrent streams | Max duration |
|------|--------------------|--------------|
| Free | 0 — not available | — |
| Pro | Limited (plan-specific) | Plan-specific |
| Enterprise | Unlimited | Unlimited |

**TIER_LIMIT error:**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "TIER_LIMIT",
    "message": "Live streaming is not available on your plan (free). Please upgrade.",
    "details": { "feature": "live_stream_max_streams", "tier": "free" },
    "timestamp": "2026-07-04T10:00:00Z"
  }
}
```

**Concurrent stream limit:**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "TIER_LIMIT",
    "message": "Your plan (pro) allows up to 2 concurrent live streams. Please stop an existing stream or upgrade.",
    "details": { "feature": "live_stream_max_streams", "tier": "pro" },
    "timestamp": "2026-07-04T10:00:00Z"
  }
}
```

**Duration gate:** When a plan-specific maximum duration is exceeded, the server auto-stops the stream. The session's `stop_reason` will be set to `"max_duration_exceeded"`.

---

## Error Reference

| Scenario | HTTP | `error.code` | Fix |
|----------|------|-------------|-----|
| Missing or invalid API key | 401 | `UNAUTHORIZED` | Check `X-API-Key` header |
| Plan does not include live streaming | 403 | `TIER_LIMIT` | Upgrade subscription |
| Too many concurrent streams | 403 | `TIER_LIMIT` | Stop an existing session |
| Session not found | 404 | `NOT_FOUND` | Verify `session_id` |
| Neither `collection_name` nor `collection_id` provided | 422 | `BAD_REQUEST` | Provide one of the two |
| `collection_id` does not exist | 404 | `NOT_FOUND` | Verify the collection ID |
| `collection_id` belongs to another user | 403 | `FORBIDDEN` | Use your own collection |
| MediaMTX server unreachable | 503 | — | Poll `/mediamtx/health`; server may be starting |
| YouTube URL resolution fails | 500 | `INTERNAL_SERVER_ERROR` | Video may be private or geo-restricted; try providing cookies |
| Adding questions to a stopped session | 400 | `BAD_REQUEST` | Resume or create a new session |

---

## Internal Webhooks (Infrastructure Use Only)

These endpoints are called by MediaMTX container scripts and the Qwen worker. **Do not call them from your application.**

| Endpoint | Trigger |
|----------|---------|
| `POST /api/v2/live-stream/internal/stream-ready` | Publisher connected — session transitions to `streaming` |
| `POST /api/v2/live-stream/internal/stream-not-ready` | Publisher disconnected — session transitions to `paused` |
| `POST /api/v2/live-stream/internal/segment-recorded` | 16s segment uploaded to S3 — triggers download, indexing, and KE queueing |
| `POST /api/v2/live-stream/internal/live-plate-updated` | Qwen worker completed extraction — plate updated, notification logged |

---

## Frequently Asked Questions

**Q: How long until the stream goes live after calling a stream endpoint?**  
A: Allow 30–60 seconds for the MediaMTX server, plus 3–5 minutes for the GPU/KE worker on first use. Workers stay warm for a period after use, so subsequent streams in the same session start faster.

**Q: Can I connect the camera before workers are ready?**  
A: No — MediaMTX must be ready for the stream to flow. Always poll `/mediamtx-status` until `all_ready: true` before directing the source to publish.

**Q: What happens if the camera disconnects mid-stream?**  
A: The session transitions to `paused`. If the camera reconnects, it transitions back to `streaming` automatically. Call `POST /resume` if you need to re-register the MediaMTX path (e.g. after a server restart).

**Q: How do I play back the live stream in a browser?**  
A: Use `hls_playback_url` with an HLS player (`hls.js`, `Video.js`, or native `<video>` on Safari/iOS). For sub-second latency, use `whep_url` with WebRTC.

**Q: Can multiple cameras feed the same collection?**  
A: Yes. Pass `collection_id` (not `collection_name`) for the second and subsequent cameras to share the same collection.

**Q: How do I read AI analysis results?**  
A: Poll `GET /api/v2/data-plates/{plate_id}` — each row is a 16-second segment and each column is one of your analysis questions with the AI-generated answer.

**Q: Are segments searchable while the stream is still running?**  
A: Yes. Each periodic indexing cycle embeds all segments since the last run. Indexed segments are immediately searchable via the standard search endpoint.
