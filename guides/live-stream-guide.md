# Live Stream Guide

CreativAI Live Stream lets you ingest real-time video, index it continuously, and run AI analysis on live footage. It supports multiple ingestion protocols via MediaMTX, and automatically triggers knowledge extraction on arriving segments.

## Architecture

```
Camera / Source
    │
    ├── RTSP  ─────┐
    ├── RTMP  ─────┤
    ├── SRT   ─────┤──→ MediaMTX ──→ S3 Segments ──→ Lambda Preprocessing
    ├── HLS   ─────┤                                        │
    ├── WebRTC─────┤                                        ▼
    └── YouTube ───┘                              Periodic Indexing (5 min)
                                                            │
                                                            ▼
                                                    Live Data Plate
                                                    (real-time KE)
```

---

## Quick Start: RTSP Camera

```bash
# 1. Create a session
SESSION=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "lobby-live",
    "name": "Lobby Camera",
    "user_query": "Detect unusual activity or unauthorized persons",
    "model": "internvideo2",
    "periodic_indexing": 5
  }')

SESSION_ID=$(echo $SESSION | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['session_id'])")

# 2. Start RTSP stream
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/rtsp" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "source_url": "rtsp://192.168.1.100:554/stream1",
    "collection_id": "'$COLLECTION_ID'"
  }'
```

---

## Session Management

### Create a Session

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Front Door Camera",
    "user_query": "Alert me to any people carrying bags",
    "collection_name": "front-door-live",
    "model": "internvideo2",
    "periodic_indexing": 5
  }'
```

**Parameters**:
| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | string | null | Human-readable stream name |
| `user_query` | string | null | Natural language query for live KE |
| `collection_name` | string | null | Create a new collection (mutually exclusive with collection_id) |
| `collection_id` | string | null | Use an existing collection |
| `model` | string | `"internvideo2"` | `"internvideo2"` or `"qwen"` |
| `periodic_indexing` | int | `5` | Index every N minutes (null to disable) |

**Response** includes `session_id`, `status: "WAITING"`.

### List / Get Sessions

```bash
# List all sessions
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Filter by collection
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions?collection_id=$COLLECTION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Get specific session (includes WHIP/WHEP URLs)
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### Stop / Delete Session

```bash
# Stop active stream
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/stop" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Delete permanently
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### Check Worker Status

```bash
# MediaMTX readiness
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/mediamtx-status" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Qwen worker readiness
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/worker-status" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Protocol-Specific Stream Endpoints

All protocol endpoints share common parameters:

| Parameter | Type | Description |
|---|---|---|
| `session_id` | string | Existing live-stream session ID |
| `collection_id` | string | Target collection |
| `source_url` | string | Pull URL for the stream source |
| `name` | string | Stream name |
| `max_fps` | int | Max FPS cap (1–60, default 30) |
| `periodic_indexing` | int | Index every N minutes |

### RTSP (IP Cameras)

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/rtsp" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "collection_id": "'$COLLECTION_ID'",
    "source_url": "rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101",
    "name": "Hikvision Lobby Camera"
  }'
```

Supports: `rtsp://` and `rtsps://` (TLS)

### RTMP (OBS, encoders, streaming software)

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/rtmp" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "collection_id": "'$COLLECTION_ID'",
    "name": "OBS Stream"
  }'
```

The response includes `rtmp_url` — configure your encoder to push to this URL.
Supports: `rtmp://` and `rtmps://`

### SRT (Low-latency, satellite)

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/srt" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "collection_id": "'$COLLECTION_ID'",
    "source_url": "srt://192.168.1.50:7001"
  }'
```

### HLS / HTTP Sources (phones, DroidCam, MJPEG)

```bash
# DroidCam / IP Webcam app
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/hls" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "collection_id": "'$COLLECTION_ID'",
    "source_url": "http://192.168.1.9:4747/video"
  }'

# HLS stream
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/hls" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "collection_id": "'$COLLECTION_ID'",
    "source_url": "https://example.com/live/stream.m3u8"
  }'
```

### WebRTC (browser, native WebRTC apps)

```bash
# 1. Start WebRTC stream (get WHIP URL)
RESULT=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/webrtc" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "collection_id": "'$COLLECTION_ID'",
    "name": "Browser Webcam"
  }')

WHIP_URL=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['whip_url'])")
WHEP_URL=$(echo $RESULT | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['whep_url'])")
```

**WHIP** (publish from browser):
```javascript
// Use a WHIP client library (e.g. @eyevinn/whip-web-client)
const client = new WHIPClient();
await client.publish(whipUrl, stream, { token: apiKey });
```

**WHEP** (playback in browser):
```javascript
const pc = new RTCPeerConnection();
// Standard WHEP negotiation with the whep_url
```

**Note**: WebRTC signaling endpoints accept the API key as a `?token=` query param since browser WebRTC cannot set custom headers.

### YouTube Live / VOD

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/youtube" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "collection_name": "youtube-analysis",
    "source_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "name": "YouTube Conference Recording",
    "periodic_indexing": 10
  }'
```

For age-restricted or private videos, provide cookies in Netscape format:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream/youtube" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "collection_id": "'$COLLECTION_ID'",
    "source_url": "https://www.youtube.com/watch?v=PRIVATE_ID",
    "cookies": "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tFALSE\t0\tSID\t..."
  }'
```

### Auto-Detected Protocol

Let the server detect the protocol from the source URL:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/stream" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "collection_id": "'$COLLECTION_ID'",
    "source_url": "rtsp://192.168.1.100:554/stream",
    "name": "Auto-detected camera"
  }'
```

Supports auto-detection for: RTSP/RTSPS, RTMP/RTMPS, HLS (.m3u8), SRT, HTTP/MJPEG, WebRTC, YouTube URLs.

---

## MediaMTX Monitoring

```bash
# Health check
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/mediamtx/health"

# List all active streams
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/mediamtx/streams" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Get specific stream
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/mediamtx/streams/live/$STREAM_PATH" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Connection summary
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/mediamtx/connections/summary" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Indexing Jobs

```bash
# Get indexing status for a live session
curl "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/indexing-jobs" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

With `periodic_indexing` set, a new indexing job is triggered every N minutes automatically. You can also trigger indexing manually via the standard indexing endpoint at any time.

---

## Add Analysis Questions Mid-Stream

Add or change the analysis questions while a stream is live:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/live-stream/sessions/$SESSION_ID/add-questions" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "questions": [
      "Are there any safety hazards visible?",
      "How many people are present?"
    ]
  }'
```

---

## Common Source URL Examples

| Source | Example URL |
|---|---|
| Hikvision IP camera | `rtsp://admin:pass@192.168.1.100:554/Streaming/Channels/101` |
| Dahua IP camera | `rtsp://admin:pass@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0` |
| DroidCam (Android) | `http://192.168.1.9:4747/video` |
| IP Webcam (Android) | `http://192.168.1.10:8080/video` |
| OBS (push) | Use the `rtmp_url` from the RTMP start response |
| YouTube live | `https://www.youtube.com/watch?v=VIDEO_ID` |
| YouTube Shorts | `https://youtu.be/SHORT_ID` |
| Generic HLS | `https://streaming.example.com/live/index.m3u8` |

---

## Tier Limits

Live streaming is gated by plan tier:
- Free plan: Live streaming not available
- Pro+: Limited concurrent streams (check `TIER_LIMIT` error for your limit)
- Enterprise: Unlimited concurrent streams

---

## Internal Webhooks

These are called by MediaMTX itself — not for external use:

| Webhook | Trigger |
|---|---|
| `POST /internal/stream-ready` | Publisher connected |
| `POST /internal/stream-not-ready` | Publisher disconnected |
| `POST /internal/segment-recorded` | 16s segment saved to S3 |
| `POST /internal/live-plate-updated` | Qwen worker completed extraction |
