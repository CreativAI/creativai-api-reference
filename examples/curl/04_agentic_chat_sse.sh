#!/usr/bin/env bash
# 04_agentic_chat_sse.sh — Agentic Chat with SSE Streaming
# Usage: export CREATIVAI_BASE_URL=... CREATIVAI_API_KEY=... COL_ID=... && bash 04_agentic_chat_sse.sh

set -euo pipefail
BASE="${CREATIVAI_BASE_URL:?Set CREATIVAI_BASE_URL}"
KEY="${CREATIVAI_API_KEY:?Set CREATIVAI_API_KEY}"
COL_ID="${COL_ID:?Set COL_ID}"

json_field() { python3 -c "import sys,json; print(json.load(sys.stdin)['data']['$1'])"; }

# ─── Create a Session ─────────────────────────────────────────────────────────
echo "=== 1. Create agentic chat session ==="
SESSION=$(curl -sf -X POST "$BASE/api/v2/agentic-chat/sessions" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"session_name\": \"Security Analysis Q1 2025\"
  }")
echo "$SESSION" | python3 -m json.tool
SESSION_ID=$(echo "$SESSION" | json_field session_id)
echo "Session ID: $SESSION_ID"

# ─── Chat with SSE Streaming ─────────────────────────────────────────────────
echo "=== 2. Send a message and stream the response ==="
echo "(SSE events will print below — use Ctrl+C to stop)"
echo ""
curl -sN -X POST "$BASE/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d "{
    \"message\": \"Analyze the footage for any unusual activities. Summarize what you find.\",
    \"collection_id\": \"$COL_ID\"
  }" &
CURL_PID=$!

# Capture SSE for 60 seconds or until done
timeout 60 tail -f /dev/stdin 2>/dev/null || true
wait $CURL_PID 2>/dev/null || true

# ─── SSE Event Reference ─────────────────────────────────────────────────────
echo ""
echo "=== SSE event types (reference) ==="
cat << 'EOF'
event: message_delta        — streaming text chunk; event.data.delta = text fragment
event: message_complete     — full message assembled; event.data.message = complete text
event: search_results       — search performed; event.data.results = array of segments
event: tool_call            — tool/action being executed; event.data.tool = tool name
event: interrupt            — needs user input; event.data.interrupt_type = type
event: session_state        — session state change; event.data.state = new state
event: execution_plan       — multi-step plan; event.data.steps = plan array
event: error                — error occurred; event.data.error = error object
event: done                 — stream complete
EOF

# ─── Web Search Query ─────────────────────────────────────────────────────────
echo "=== 3. Query with web search enabled ==="
curl -sN -X POST "$BASE/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d "{
    \"message\": \"Search the web for latest OSHA regulations on hard hat requirements and compare with what I see in my footage.\",
    \"collection_id\": \"$COL_ID\"
  }"

# ─── Handle Interrupts ────────────────────────────────────────────────────────
echo ""
echo "=== 4. Check session status (to detect interrupts) ==="
curl -sf "$BASE/api/v2/agentic-chat/sessions/$SESSION_ID/status" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 5. Respond to a search feedback interrupt ==="
# When interrupt_type = "search_feedback", provide search refinement
curl -sf -X POST "$BASE/api/v2/agentic-chat/sessions/$SESSION_ID/search-feedback" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"feedback\": \"Focus specifically on incidents near the loading dock, not the main entrance\"
  }" | python3 -m json.tool

echo "=== 6. Resume session after interrupt or stop ==="
curl -sN -X POST "$BASE/api/v2/agentic-chat/sessions/$SESSION_ID/resume" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d "{\"collection_id\": \"$COL_ID\"}"

echo "=== 7. Stop a running session ==="
curl -sf -X POST "$BASE/api/v2/agentic-chat/sessions/$SESSION_ID/stop" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

# ─── Session Management ───────────────────────────────────────────────────────
echo "=== 8. List all sessions ==="
curl -sf "$BASE/api/v2/agentic-chat/sessions" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 9. Get session details ==="
curl -sf "$BASE/api/v2/agentic-chat/sessions/$SESSION_ID" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 10. Get message history ==="
curl -sf "$BASE/api/v2/agentic-chat/sessions/$SESSION_ID/messages" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

# ─── Reconnect Pattern ────────────────────────────────────────────────────────
echo ""
echo "=== Reconnect to an ongoing task (empty message) ==="
cat << 'EOF'
# If the connection drops while the agent is running, reconnect with an empty message:
curl -sN -X POST "$BASE/api/v2/agentic-chat/sessions/$SESSION_ID/chat" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"message": "", "collection_id": "'$COL_ID'"}'
# Or use the dedicated stream endpoint:
curl -sN "$BASE/api/v2/agentic-chat/sessions/$SESSION_ID/stream" \
  -H "X-API-Key: $KEY" \
  -H "Accept: text/event-stream"
EOF

echo ""
echo "=== 11. Delete session ==="
read -p "Delete session $SESSION_ID? (y/N) " confirm
if [[ "$confirm" == "y" ]]; then
  curl -sf -X DELETE "$BASE/api/v2/agentic-chat/sessions/$SESSION_ID" \
    -H "X-API-Key: $KEY" | python3 -m json.tool
fi
