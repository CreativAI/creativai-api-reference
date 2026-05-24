#!/usr/bin/env bash
# 03_data_plates_and_ke.sh — Data Plates, Segments, CSV Export & Knowledge Extraction
# Usage: export CREATIVAI_BASE_URL=... CREATIVAI_API_KEY=... COL_ID=... && bash 03_data_plates_and_ke.sh

set -euo pipefail
BASE="${CREATIVAI_BASE_URL:?Set CREATIVAI_BASE_URL}"
KEY="${CREATIVAI_API_KEY:?Set CREATIVAI_API_KEY}"
COL_ID="${COL_ID:?Set COL_ID}"

json_field() { python3 -c "import sys,json; print(json.load(sys.stdin)['data']['$1'])"; }
json_list_field() { python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['$1'])"; }

poll_job() {
  local URL=$1 INTERVAL=${2:-10}
  while true; do
    RESP=$(curl -sf "$URL" -H "X-API-Key: $KEY")
    STATUS=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['status'])")
    echo "  Status: $STATUS"
    case $STATUS in completed|failed) break ;; esac
    sleep "$INTERVAL"
  done
  echo "$RESP" | python3 -m json.tool
}

# ─── Create Plate from Search ─────────────────────────────────────────────────
echo "=== 1. Create plate from search results ==="
PLATE=$(curl -sf -X POST "$BASE/api/v2/data-plates/create" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"plate_name\": \"PPE Violations Q1\",
    \"search_query\": \"person not wearing hard hat on construction site\",
    \"top_k\": 50
  }")
echo "$PLATE" | python3 -m json.tool
JOB_ID=$(echo "$PLATE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'].get('job_id',''))")
if [ -n "$JOB_ID" ]; then
  echo "  Polling plate creation job $JOB_ID..."
  poll_job "$BASE/api/v2/data-plates/jobs/$JOB_ID" 5
fi
PLATE_ID=$(echo "$PLATE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data'].get('plate_id',''))")
echo "Plate ID: $PLATE_ID"

echo "=== 2. Create plate from entire collection ==="
curl -sf -X POST "$BASE/api/v2/data-plates/create-from-collection" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"plate_name\": \"All Footage Q1\"
  }" | python3 -m json.tool

echo "=== 3. List plates ==="
curl -sf -X POST "$BASE/api/v2/data-plates/list" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COL_ID\"}" | python3 -m json.tool

echo "=== 4. Get plate details ==="
curl -sf -X POST "$BASE/api/v2/data-plates/get" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COL_ID\", \"plate_id\": \"$PLATE_ID\"}" \
  | python3 -m json.tool

# ─── Segment Management ───────────────────────────────────────────────────────
echo "=== 5. Add segments manually ==="
curl -sf -X POST "$BASE/api/v2/data-plates/segments/add" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"plate_id\": \"$PLATE_ID\",
    \"segments\": [
      {\"chunk_id\": \"chunk_001\", \"start_time\": 0.0, \"end_time\": 16.0}
    ]
  }" | python3 -m json.tool

echo "=== 6. Remove segments ==="
curl -sf -X POST "$BASE/api/v2/data-plates/segments/remove" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"plate_id\": \"$PLATE_ID\",
    \"chunk_ids\": [\"chunk_001\"]
  }" | python3 -m json.tool

echo "=== 7. Locate segment in source video ==="
curl -sf -X POST "$BASE/api/v2/data-plates/segments/locate" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"plate_id\": \"$PLATE_ID\",
    \"chunk_id\": \"chunk_002\"
  }" | python3 -m json.tool

# ─── Sub-Plates ───────────────────────────────────────────────────────────────
echo "=== 8. Create sub-plate (filter mode) ==="
curl -sf -X POST "$BASE/api/v2/data-plates/sub-plates/create" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"plate_id\": \"$PLATE_ID\",
    \"sub_plate_name\": \"High Severity Only\",
    \"mode\": \"filter\",
    \"filters\": {
      \"column_name\": \"severity\",
      \"value\": \"high\"
    }
  }" | python3 -m json.tool

echo "=== 9. Create sub-plate (segment wise) ==="
curl -sf -X POST "$BASE/api/v2/data-plates/sub-plates/create" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"plate_id\": \"$PLATE_ID\",
    \"sub_plate_name\": \"First 20 Segments\",
    \"mode\": \"segment_wise\",
    \"segment_range\": {\"start\": 0, \"end\": 20}
  }" | python3 -m json.tool

# ─── CSV Export ───────────────────────────────────────────────────────────────
echo "=== 10. Generate CSV export ==="
CSV_JOB=$(curl -sf -X POST "$BASE/api/v2/data-plates/generate-csv" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COL_ID\", \"plate_id\": \"$PLATE_ID\"}")
echo "$CSV_JOB" | python3 -m json.tool
CSV_ID=$(echo "$CSV_JOB" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['csv_id'])" 2>/dev/null || echo "")
echo "CSV ID: $CSV_ID"
echo "  Download: GET $BASE/api/v2/data-plates/export-csv/$COL_ID/$CSV_ID"

# ─── Columns (lists) ─────────────────────────────────────────────────────────
echo "=== 11. List data plate columns ==="
curl -sf -X POST "$BASE/api/v2/data-plates/columns/list" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COL_ID\", \"plate_id\": \"$PLATE_ID\"}" \
  | python3 -m json.tool

# ─── Knowledge Extraction ─────────────────────────────────────────────────────
echo "=== 12. Add KE column (single question) ==="
KE_COL=$(curl -sf -X POST "$BASE/api/v2/knowledge-extraction/columns/add" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"plate_id\": \"$PLATE_ID\",
    \"column_name\": \"PPE Violations\",
    \"question\": \"What PPE violations are visible in this segment?\",
    \"model_version\": \"base\"
  }")
echo "$KE_COL" | python3 -m json.tool
KE_JOB=$(echo "$KE_COL" | json_field job_id)
echo "KE job: $KE_JOB"
poll_job "$BASE/api/v2/knowledge-extraction/jobs/$KE_JOB" 10

echo "=== 13. Add KE column (multi-question in one call) ==="
curl -sf -X POST "$BASE/api/v2/knowledge-extraction/columns/add" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"plate_id\": \"$PLATE_ID\",
    \"column_name\": \"Site Audit\",
    \"question\": [
      \"How many workers are in the scene?\",
      \"Are workers wearing PPE?\",
      \"Is any heavy machinery operating?\"
    ],
    \"model_version\": \"pro\"
  }" | python3 -m json.tool

echo "=== 14. Add KE column with image references (Qwen only) ==="
# First upload reference images
UPLOAD_RESP=$(curl -sf -X POST "$BASE/api/v2/knowledge-extraction/chat/upload-images" \
  -H "X-API-Key: $KEY" \
  -F "files=@reference_ppe.jpg" \
  -F "collection_id=$COL_ID")
echo "$UPLOAD_RESP" | python3 -m json.tool
IMG_KEY=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['image_keys'][0])" 2>/dev/null || echo "")

if [ -n "$IMG_KEY" ]; then
  curl -sf -X POST "$BASE/api/v2/knowledge-extraction/columns/add" \
    -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
    -d "{
      \"collection_id\": \"$COL_ID\",
      \"plate_id\": \"$PLATE_ID\",
      \"column_name\": \"PPE Match\",
      \"question\": \"Does the worker's equipment match the reference PPE shown in the image?\",
      \"model_version\": \"pro\",
      \"image_keys\": [\"$IMG_KEY\"]
    }" | python3 -m json.tool
fi

echo "=== 15. List KE columns ==="
curl -sf -X POST "$BASE/api/v2/knowledge-extraction/columns/list" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COL_ID\", \"plate_id\": \"$PLATE_ID\"}" \
  | python3 -m json.tool

echo "=== 16. KE Chat query (conversational Q&A over plate) ==="
curl -sf -X POST "$BASE/api/v2/knowledge-extraction/chat/query" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"plate_id\": \"$PLATE_ID\",
    \"message\": \"Summarize the most common safety violations across all segments.\",
    \"aggregate_segments\": true
  }" | python3 -m json.tool

echo "=== 17. Get charts ==="
curl -sf -X POST "$BASE/api/v2/knowledge-extraction/charts/plate" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COL_ID\", \"plate_id\": \"$PLATE_ID\"}" \
  | python3 -m json.tool
