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

poll_search() {
  local JOB=$1
  echo "  Polling search job $JOB ..."
  while true; do
    RESP=$(curl -sf "$BASE/api/v2/search/jobs/$JOB" -H "X-API-Key: $KEY")
    STATUS=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['status'])")
    echo "    Status: $STATUS"
    case $STATUS in completed|failed) break ;; esac
    sleep 2
  done
  echo "$RESP"
}

# ─── Preprocessing Status ─────────────────────────────────────────────────────
echo "=== 1. Check preprocessing status ==="
# After confirm-upload, preprocessing runs automatically (splits videos into 16s chunks)
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
# Tags are NOT accepted here — declare them on POST /collections/{id}/confirm-upload instead.
# To change tags on already-indexed media use the async job at
#   POST /api/v2/collections/{id}/tags        (add/remove deltas)
#   GET  /api/v2/collections/{id}/tags/jobs/{job_id}
INDEXING_JOB=$(curl -sf -X POST "$BASE/api/v2/indexing/chunk-based" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COL_ID\"}")
echo "$INDEXING_JOB" | python3 -m json.tool
INDEXING_ID=$(echo "$INDEXING_JOB" | json_field indexing_id)
echo "Indexing job: $INDEXING_ID"

poll_indexing "$INDEXING_ID"

# ─── Search (async: submit → poll) ────────────────────────────────────────────
echo "=== 5. Basic semantic search ==="
SUBMIT=$(curl -sf -X POST "$BASE/api/v2/search" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"text_query\": \"person entering restricted area without badge\",
    \"page_size\": 5
  }")
SEARCH_JOB_ID=$(echo "$SUBMIT" | json_field search_job_id)
SEARCH=$(poll_search "$SEARCH_JOB_ID")
echo "$SEARCH" | python3 -m json.tool
SEARCH_ID=$(echo "$SEARCH" | json_field search_id)

echo "=== 6. Search restricted by tags (OR semantics) ==="
SUBMIT=$(curl -sf -X POST "$BASE/api/v2/search" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"text_query\": \"safety equipment missing\",
    \"page_size\": 10,
    \"tags\": [\"lobby\", \"entrance\"]
  }")
poll_search "$(echo "$SUBMIT" | json_field search_job_id)" | python3 -m json.tool

echo "=== 7. Search with typed metadata filter ==="
# Discover the available keys with GET /api/v2/collections/$COL_ID/metadata-schema
SUBMIT=$(curl -sf -X POST "$BASE/api/v2/search" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"text_query\": \"a crosswalk\",
    \"meta_filter\": {
      \"op\": \"and\",
      \"clauses\": [
        {\"key\": \"duration\", \"cmp\": \"<\",  \"value\": 30},
        {\"key\": \"region\",   \"cmp\": \"in\", \"value\": [\"eu\"]}
      ]
    }
  }")
poll_search "$(echo "$SUBMIT" | json_field search_job_id)" | python3 -m json.tool

echo "=== 8. Search with LLM query planner (splits text_query into visual + metadata) ==="
SUBMIT=$(curl -sf -X POST "$BASE/api/v2/search" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"text_query\": \"clips under 30 seconds showing a crosswalk, collected in the EU\",
    \"plan_metadata\": true
  }")
poll_search "$(echo "$SUBMIT" | json_field search_job_id)" | python3 -m json.tool

echo "=== 9. Vision-only search ==="
SUBMIT=$(curl -sf -X POST "$BASE/api/v2/search" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"text_query\": \"someone climbing over fence\",
    \"search_type\": \"vision\",
    \"page_size\": 5
  }")
poll_search "$(echo "$SUBMIT" | json_field search_job_id)" | python3 -m json.tool

echo "=== 10. Paginated search (uses stored search_id — synchronous 200) ==="
curl -sf -X POST "$BASE/api/v2/search" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"search_id\": \"$SEARCH_ID\",
    \"page_number\": 2,
    \"page_size\": 5
  }" | python3 -m json.tool

echo ""
echo "Search complete. Indexing ID: $INDEXING_ID"
