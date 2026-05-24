#!/usr/bin/env bash
# 01_collections.sh — Collection, Media Upload, and Organization management
# Usage: export CREATIVAI_BASE_URL=... CREATIVAI_API_KEY=... && bash 01_collections.sh

set -euo pipefail
BASE="${CREATIVAI_BASE_URL:?Set CREATIVAI_BASE_URL}"
KEY="${CREATIVAI_API_KEY:?Set CREATIVAI_API_KEY}"

# ─── Helpers ─────────────────────────────────────────────────────────────────
json_field() { python3 -c "import sys,json; print(json.load(sys.stdin)['data']['$1'])"; }

echo "=== 1. Verify authentication ==="
curl -sf "$BASE/api/v2/users/api-key-check" -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 2. Get user info ==="
curl -sf "$BASE/api/v2/users/me/info" -H "X-API-Key: $KEY" | python3 -m json.tool

# ─── Organizations & Projects ─────────────────────────────────────────────────
echo "=== 3. Create organization ==="
ORG=$(curl -sf -X POST "$BASE/api/v2/organizations" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"organization_name": "Demo Corp"}')
echo "$ORG" | python3 -m json.tool
ORG_ID=$(echo "$ORG" | json_field organization_id)

echo "=== 4. Create project ==="
curl -sf -X POST "$BASE/api/v2/organizations/$ORG_ID/projects" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"project_name": "Security Analysis"}' | python3 -m json.tool

# ─── Collections ─────────────────────────────────────────────────────────────
echo "=== 5. Create collection (InternVideo2 — video only) ==="
COL=$(curl -sf -X POST "$BASE/api/v2/collections" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_name\": \"demo-internvideo2\",
    \"description\": \"InternVideo2 demo collection\",
    \"model\": \"default\"
  }")
echo "$COL" | python3 -m json.tool
COL_ID=$(echo "$COL" | json_field collection_id)
echo "Collection ID: $COL_ID"

echo "=== 6. Create collection (Qwen3-VL — multimodal) ==="
QWEN_COL=$(curl -sf -X POST "$BASE/api/v2/collections" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_name\": \"demo-qwen3vl\",
    \"description\": \"Multimodal collection for videos+images+PDFs\",
    \"model\": \"qwen\"
  }")
echo "$QWEN_COL" | python3 -m json.tool
QWEN_COL_ID=$(echo "$QWEN_COL" | json_field collection_id)

echo "=== 7. List all collections ==="
curl -sf "$BASE/api/v2/collections" -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 8. Get collection details ==="
curl -sf "$BASE/api/v2/collections/$COL_ID" -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 9. Update collection ==="
curl -sf -X PATCH "$BASE/api/v2/collections/$COL_ID" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"collection_name": "demo-updated", "description": "Updated description"}' \
  | python3 -m json.tool

# ─── File Upload (presigned URL) ──────────────────────────────────────────────
echo "=== 10. Get single upload URL ==="
UPLOAD=$(curl -sf -X POST "$BASE/api/v2/collections/$COL_ID/upload-url" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"filename": "sample.mp4", "content_type": "video/mp4"}')
echo "$UPLOAD" | python3 -m json.tool
UPLOAD_URL=$(echo "$UPLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['upload_url'])")
echo "Upload URL (PUT directly to S3):"
echo "  curl -X PUT '$UPLOAD_URL' -H 'Content-Type: video/mp4' --data-binary @sample.mp4"

echo "=== 11. Get batch upload URLs ==="
curl -sf -X POST "$BASE/api/v2/collections/$COL_ID/upload-urls" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{
    "files": [
      {"filename": "lobby.mp4",    "content_type": "video/mp4"},
      {"filename": "entrance.mp4", "content_type": "video/mp4"}
    ]
  }' | python3 -m json.tool

# ─── Multipart Upload (large files) ──────────────────────────────────────────
echo "=== 12. Initiate multipart upload ==="
MP_INIT=$(curl -sf -X POST "$BASE/api/v2/collections/uploads/initiate" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COL_ID\",
    \"files\": [{\"filename\": \"large-4k.mp4\", \"file_size\": 524288000, \"content_type\": \"video/mp4\"}]
  }")
echo "$MP_INIT" | python3 -m json.tool
MP_UPLOAD_ID=$(echo "$MP_INIT" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['upload_id'])")

echo "  Upload each part with: curl -X PUT <part_url> --data-binary @<chunk>"
echo "  Then complete with /collections/uploads/$MP_UPLOAD_ID/complete"

# ─── S3 Transfer ──────────────────────────────────────────────────────────────
echo "=== 13. Start S3 transfer ==="
# (Replace with actual S3 source)
echo "  POST $BASE/api/v2/transfers"
echo "  Body: {\"collection_id\": \"$COL_ID\", \"source_url\": \"s3://your-bucket/videos/\"}"

# ─── Cleanup ─────────────────────────────────────────────────────────────────
echo "=== 14. List media in collection ==="
curl -sf "$BASE/api/v2/collections/$COL_ID/media" -H "X-API-Key: $KEY" | python3 -m json.tool

echo ""
echo "Collection IDs created:"
echo "  InternVideo2: $COL_ID"
echo "  Qwen3-VL:     $QWEN_COL_ID"
