#!/usr/bin/env bash
# 02_indexing_and_search.sh — Preprocessing, Indexing, and Search
# Usage: export CREATIVAI_BASE_URL=... CREATIVAI_API_KEY=... COL_ID=... && bash 02_indexing_and_search.sh

set -euo pipefail
BASE="${CREATIVAI_BASE_URL:?Set CREATIVAI_BASE_URL}"
KEY="${CREATIVAI_API_KEY:?Set CREATIVAI_API_KEY}"
COL_ID="${COL_ID:?Set COL_ID}"

# ─── Helpers ─────────────────────────────────────────────────────────────────
json_field() { python3 -c "import sys,json; print(json.load(sys.stdin)['data']['$1'])"; }

poll_indexing() {
  local JOB=$1
  echo "  Polling indexing job $JOB ..."
  while true; do
    RESP=$(curl -sf "$BASE/api/v2/indexing/chunk-based/$JOB/status" -H "X-API-Key: $KEY")
    STATUS=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['status'])")
    echo "    Status: $STATUS"
    case $STATUS in completed|partial|failed) break ;; esac
    sleep 15
  done
  echo "$RESP" | python3 -m json.tool
}

# ─── Preprocessing Status ─────────────────────────────────────────────────────
echo "=== 1. Check preprocessing status ==="
# After upload, Lambda auto-preprocesses media (splits videos into 16s chunks)
curl -sf "$BASE/api/v2/indexing/preprocessing-status/$COL_ID" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

echo "  Wait for 'completed' before indexing."
echo "  Poll GET /api/v2/indexing/preprocessing-status/$COL_ID until can_start_indexing = true"

echo "=== 2. List preprocessed media ==="
curl -sf "$BASE/api/v2/indexing/preprocessed-videos/$COL_ID" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

# ─── Cost Estimation ─────────────────────────────────────────────────────────
echo "=== 3. Estimate indexing cost ==="
curl -sf -X POST "$BASE/api/v2/indexing/chunk-based/estimate-cost" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COL_ID\"}" | python3 -m json.tool

# ─── Basic Indexing ───────────────────────────────────────────────────────────
echo "=== 4. Start indexing (all preprocessed media) ==="
INDEXING_JOB=$(curl -sf -X POST "$BASE/api/v2/indexing/chunk-based" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COL_ID\"}")
echo "$INDEXING_JOB" | python3 -m json.tool
INDEXING_ID=$(echo "$INDEXING_JOB" | json_field indexing_id)
echo "Indexing job: $INDEXING_ID"

poll_indexing "$INDEXING_ID"

# ─── Indexing with Tags ───────────────────────────────────────────────────────
echo "=== 5. Index specific files with per-file tags ==="
TAGGED_JOB=$(curl -sf -X POST "$BASE/api/v2/indexing/chunk-based" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"uris\": [
      \"s3://your-bucket/lobby.mp4\",
      \"s3://your-bucket/entrance.mp4\"
    ],
    \"tags\": {
      \"s3://your-bucket/lobby.mp4\": [\"lobby\", \"ground-floor\"],
      \"s3://your-bucket/entrance.mp4\": [\"entrance\", \"outdoor\"]
    }
  }")
echo "$TAGGED_JOB" | python3 -m json.tool

echo "=== 6. Index with wildcard tags (all files get same tags) ==="
curl -sf -X POST "$BASE/api/v2/indexing/chunk-based" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"tags\": {\"*\": [\"2025-q1\", \"review-batch\"]}
  }" | python3 -m json.tool

# ─── Search ───────────────────────────────────────────────────────────────────
echo "=== 7. Basic semantic search ==="
SEARCH=$(curl -sf -X POST "$BASE/api/v2/search" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"query\": \"person entering restricted area without badge\",
    \"top_k\": 5
  }")
echo "$SEARCH" | python3 -m json.tool
SEARCH_ID=$(echo "$SEARCH" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['search_id'])")

echo "=== 8. Search with filters ==="
curl -sf -X POST "$BASE/api/v2/search" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"query\": \"safety equipment missing\",
    \"top_k\": 10,
    \"search_type\": \"hybrid\",
    \"filters\": {
      \"tags\": [\"lobby\", \"entrance\"]
    }
  }" | python3 -m json.tool

echo "=== 9. Vision-only search ==="
curl -sf -X POST "$BASE/api/v2/search" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"query\": \"someone climbing over fence\",
    \"search_type\": \"vision\",
    \"top_k\": 5
  }" | python3 -m json.tool

echo "=== 10. Image-based search (Qwen collections only) ==="
# Encode a reference image and use it as the search query
if command -v base64 &>/dev/null && [ -f sample_query.jpg ]; then
  IMG_B64=$(base64 -i sample_query.jpg)
  curl -sf -X POST "$BASE/api/v2/search" \
    -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
    -d "{
      \"collection_id\": \"$COL_ID\",
      \"image_base64\": \"$IMG_B64\",
      \"top_k\": 5
    }" | python3 -m json.tool
else
  echo "  (Skipped — no sample_query.jpg found)"
fi

echo "=== 11. Paginated search ==="
NEXT_PAGE=$(curl -sf -X POST "$BASE/api/v2/search" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"query\": \"safety equipment missing\",
    \"top_k\": 5,
    \"search_id\": \"$SEARCH_ID\",
    \"page_number\": 2
  }")
echo "$NEXT_PAGE" | python3 -m json.tool

echo ""
echo "Search complete. Indexing ID: $INDEXING_ID"
