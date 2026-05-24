#!/usr/bin/env bash
# 05_live_stream.sh — Live Streaming with all protocols (RTSP, RTMP, SRT, HLS, WebRTC, YouTube)
# Usage: export CREATIVAI_BASE_URL=... CREATIVAI_API_KEY=... COL_ID=... && bash 05_live_stream.sh

set -euo pipefail
BASE="${CREATIVAI_BASE_URL:?Set CREATIVAI_BASE_URL}"
KEY="${CREATIVAI_API_KEY:?Set CREATIVAI_API_KEY}"
COL_ID="${COL_ID:?Set COL_ID}"

json_field() { python3 -c "import sys,json; print(json.load(sys.stdin)['data']['$1'])"; }

echo "=== 1. Auto-detect protocol (recommended) ==="
# Supply any source URL — the server auto-detects the protocol
SESSION=$(curl -sf -X POST "$BASE/api/v2/live-stream/stream" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"source_url\": \"rtsp://192.168.1.100:554/stream\",
    \"name\": \"Lobby Camera\",
    \"periodic_indexing\": 5
  }")
echo "$SESSION" | python3 -m json.tool
SESSION_ID=$(echo "$SESSION" | json_field session_id)
echo "Session ID: $SESSION_ID"

# ─── Protocol-specific endpoints ─────────────────────────────────────────────
echo ""
echo "=== Protocol examples (reference) ==="

echo "--- RTSP ---"
curl -sf -X POST "$BASE/api/v2/live-stream/stream/rtsp" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"source_url\": \"rtsp://user:pass@192.168.1.50:554/Streaming/Channels/101\",
    \"name\": \"Gate Camera (RTSP)\",
    \"periodic_indexing\": 10
  }" | python3 -m json.tool

echo "--- RTMP ---"
curl -sf -X POST "$BASE/api/v2/live-stream/stream/rtmp" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"source_url\": \"rtmp://live.example.com/app/stream_key\",
    \"name\": \"Broadcast Feed\"
  }" | python3 -m json.tool

echo "--- SRT ---"
curl -sf -X POST "$BASE/api/v2/live-stream/stream/srt" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"source_url\": \"srt://192.168.1.75:9000\",
    \"name\": \"Production Floor SRT\"
  }" | python3 -m json.tool

echo "--- HLS ---"
curl -sf -X POST "$BASE/api/v2/live-stream/stream/hls" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"source_url\": \"https://live.cdn.example.com/master.m3u8\",
    \"name\": \"CDN HLS Feed\"
  }" | python3 -m json.tool

echo "--- YouTube Live ---"
curl -sf -X POST "$BASE/api/v2/live-stream/stream/youtube" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"source_url\": \"https://www.youtube.com/watch?v=LIVE_VIDEO_ID\",
    \"name\": \"Conference Keynote\",
    \"periodic_indexing\": 5
  }" | python3 -m json.tool

# ─── WebRTC (WHIP/WHEP) ───────────────────────────────────────────────────────
echo "=== 2. Create WebRTC session ==="
WEBRTC_SESSION=$(curl -sf -X POST "$BASE/api/v2/live-stream/stream/webrtc" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"name\": \"Browser Camera Feed\"
  }")
echo "$WEBRTC_SESSION" | python3 -m json.tool
WS_SESSION_ID=$(echo "$WEBRTC_SESSION" | json_field session_id)
WS_TOKEN=$(echo "$WEBRTC_SESSION" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'].get('token',''))" 2>/dev/null || echo "")

echo "WHIP endpoint (push from browser):"
echo "  POST $BASE/api/v2/live-stream/sessions/$WS_SESSION_ID/whip?token=$WS_TOKEN"
echo "  Body: SDP offer (Content-Type: application/sdp)"
echo ""
echo "WHEP endpoint (pull the stream):"
echo "  POST $BASE/api/v2/live-stream/sessions/$WS_SESSION_ID/whep?token=$WS_TOKEN"
echo "  Body: SDP offer (Content-Type: application/sdp)"

# ─── Session Management ───────────────────────────────────────────────────────
echo "=== 3. List all sessions ==="
curl -sf "$BASE/api/v2/live-stream/sessions" -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 4. Get session details ==="
curl -sf "$BASE/api/v2/live-stream/sessions/$SESSION_ID" -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 5. Get indexing jobs for session ==="
curl -sf "$BASE/api/v2/live-stream/sessions/$SESSION_ID/indexing-jobs" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 6. Get worker status ==="
curl -sf "$BASE/api/v2/live-stream/sessions/$SESSION_ID/worker-status" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 7. Add focus questions to a running session ==="
curl -sf -X POST "$BASE/api/v2/live-stream/sessions/$SESSION_ID/add-questions" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{
    "questions": [
      "How many people entered in the last segment?",
      "Were any safety incidents detected?"
    ]
  }' | python3 -m json.tool

# ─── MediaMTX Health Monitoring ──────────────────────────────────────────────
echo "=== 8. MediaMTX server health ==="
curl -sf "$BASE/api/v2/live-stream/mediamtx/health" -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 9. Active streams ==="
curl -sf "$BASE/api/v2/live-stream/mediamtx/streams" -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 10. Active connections summary ==="
curl -sf "$BASE/api/v2/live-stream/mediamtx/connections/summary" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

# ─── Stop / Resume / Delete ───────────────────────────────────────────────────
echo "=== 11. Stop session ==="
curl -sf -X POST "$BASE/api/v2/live-stream/sessions/$SESSION_ID/stop" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 12. Resume session ==="
curl -sf -X POST "$BASE/api/v2/live-stream/sessions/$SESSION_ID/resume" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

echo ""
echo "=== Common source URL patterns ==="
cat << 'EOF'
IP Cameras (RTSP):
  rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101
  rtsp://user:pass@camera.local/stream1

RTMP Push (OBS → Server):
  rtmp://yourmediamtx.example.com/live/stream_key

SRT:
  srt://192.168.1.75:9000?passphrase=secret

YouTube Live:
  https://www.youtube.com/watch?v=VIDEO_ID

HLS (CDN):
  https://live.cdn.example.com/hls/stream/playlist.m3u8

Webcam via FFMPEG → RTMP:
  ffmpeg -f avfoundation -i "0:0" -c:v libx264 -f flv rtmp://server/live/stream
EOF
