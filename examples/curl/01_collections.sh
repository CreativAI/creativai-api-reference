#!/usr/bin/env bash
# 01_collections.sh — Collection, Media Upload, and Organization management
# Usage: export CREATIVAI_BASE_URL=... CREATIVAI_API_KEY=... && bash 01_collections.sh

set -euo pipefail
BASE="${CREATIVAI_BASE_URL:?Set CREATIVAI_BASE_URL}"
KEY="${CREATIVAI_API_KEY:?Set CREATIVAI_API_KEY}"

# ─── Helpers ─────────────────────────────────────────────────────────────────
json_field() { python3 -c "import sys,json; print(json.load(sys.stdin)['data']['$1'])"; }

echo "=== 1. Verify authentication ==="
curl -sf "$BASE/api/v2/users/get_users_info" -H "X-API-Key: $KEY" | python3 -m json.tool

# ─── Organizations & Projects ─────────────────────────────────────────────────
echo "=== 2. Create organization ==="
ORG=$(curl -sf -X POST "$BASE/api/v2/organizations" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"organization_name": "Demo Corp"}')
echo "$ORG" | python3 -m json.tool
ORG_ID=$(echo "$ORG" | json_field organization_id)

echo "=== 3. Create project ==="
curl -sf -X POST "$BASE/api/v2/organizations/$ORG_ID/projects" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"project_name": "Security Analysis"}' | python3 -m json.tool

# ─── Collections ─────────────────────────────────────────────────────────────
echo "=== 4. Create collection (InternVideo2 — video only) ==="
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

echo "=== 5. Create collection (Qwen3-VL — multimodal) ==="
MULTIMODAL_COL=$(curl -sf -X POST "$BASE/api/v2/collections" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"collection_name\": \"demo-multimodal\",
    \"description\": \"Multimodal collection for videos and images\",
    \"model\": \"multimodal\"
  }")
echo "$MULTIMODAL_COL" | python3 -m json.tool
MULTIMODAL_COL_ID=$(echo "$MULTIMODAL_COL" | json_field collection_id)

echo "=== 6. List all collections ==="
curl -sf "$BASE/api/v2/collections" -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 7. Get collection details ==="
curl -sf "$BASE/api/v2/collections/$COL_ID" -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 8. Update collection ==="
curl -sf -X PATCH "$BASE/api/v2/collections/$COL_ID" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"collection_name": "demo-updated", "description": "Updated description"}' \
  | python3 -m json.tool

# ─── File Upload (presigned URL) ──────────────────────────────────────────────
echo "=== 9. Get single upload URL ==="
UPLOAD=$(curl -sf -X POST "$BASE/api/v2/collections/$COL_ID/upload-url" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"filename": "sample.mp4", "content_type": "video/mp4"}')
echo "$UPLOAD" | python3 -m json.tool
UPLOAD_URL=$(echo "$UPLOAD" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['upload_url'])")
echo "Upload URL (PUT directly to S3):"
echo "  curl -X PUT '$UPLOAD_URL' -H 'Content-Type: video/mp4' --data-binary @sample.mp4"

echo "=== 10. Get batch upload URLs ==="
curl -sf -X POST "$BASE/api/v2/collections/$COL_ID/upload-urls" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{
    "files": [
      {"filename": "lobby.mp4",    "content_type": "video/mp4"},
      {"filename": "entrance.mp4", "content_type": "video/mp4"}
    ]
  }' | python3 -m json.tool

# ─── Confirm-upload (async: registers media, kicks off preprocessing,
#     attaches tags & typed metadata) ───────────────────────────────────────
echo "=== 10b. Confirm upload with tags + metadata ==="
CONFIRM=$(curl -sf -X POST "$BASE/api/v2/collections/$COL_ID/confirm-upload" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen 2>/dev/null || python3 -c 'import uuid;print(uuid.uuid4())')" \
  -d "{
    \"media_ids\": [
      \"s3://your-bucket/collections/$COL_ID/uploads/lobby.mp4\",
      \"s3://your-bucket/collections/$COL_ID/uploads/entrance.mp4\"
    ],
    \"tags\": {
      \"*\": [\"q1-2026\", \"security\"],
      \"s3://your-bucket/collections/$COL_ID/uploads/lobby.mp4\": [\"lobby\", \"camera-1\"]
    },
    \"metadata\": {
      \"*\": {
        \"region\": {\"datatype\": \"enum\", \"value\": \"eu\"}
      },
      \"s3://your-bucket/collections/$COL_ID/uploads/lobby.mp4\": {
        \"duration\": {\"datatype\": \"number\", \"value\": 24.5},
        \"cameras\":  {\"datatype\": \"list\",   \"value\": [\"front\", \"rear\"]}
      }
    },
    \"metadata_schema\": {
      \"region\": {\"type\": \"enum\", \"values\": [\"eu\", \"us\", \"apac\"]}
    }
  }")
echo "$CONFIRM" | python3 -m json.tool
CONFIRM_JOB=$(echo "$CONFIRM" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['job_id'])")

echo "=== 10c. Poll confirm-upload job ==="
curl -sf "$BASE/api/v2/collections/$COL_ID/confirm-upload/jobs/$CONFIRM_JOB" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

# ─── Tags: vocabulary + async delta updates ──────────────────────────────────
echo "=== 10d. List the collection's tag vocabulary ==="
curl -sf "$BASE/api/v2/collections/$COL_ID/tags" -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 10e. Update tags on specific media (async job) ==="
TAG_JOB=$(curl -sf -X POST "$BASE/api/v2/collections/$COL_ID/tags" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"add\":    [\"reviewed\"],
    \"remove\": [\"draft\"],
    \"media_ids\": [\"s3://your-bucket/collections/$COL_ID/uploads/lobby.mp4\"]
  }")
echo "$TAG_JOB" | python3 -m json.tool
TAG_JOB_ID=$(echo "$TAG_JOB" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['job_id'])")
curl -sf "$BASE/api/v2/collections/$COL_ID/tags/jobs/$TAG_JOB_ID" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

# ─── Metadata: read schema, declare enums, update values ─────────────────────
echo "=== 10f. Read the learned metadata schema ==="
curl -sf "$BASE/api/v2/collections/$COL_ID/metadata-schema" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

echo "=== 10g. Declare (or widen) an enum key ==="
curl -sf -X POST "$BASE/api/v2/collections/$COL_ID/metadata-schema/enums" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{
    "metadata_schema": {
      "region": {"type": "enum", "values": ["eu", "us", "apac", "latam"]}
    }
  }' | python3 -m json.tool

echo "=== 10h. Set/unset metadata on existing media (async job) ==="
META_JOB=$(curl -sf -X POST "$BASE/api/v2/collections/$COL_ID/metadata" \
  -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d "{
    \"set\": {
      \"reviewed\": {\"datatype\": \"bool\", \"value\": true}
    },
    \"unset\": [\"draft\"],
    \"media_ids\": [\"s3://your-bucket/collections/$COL_ID/uploads/entrance.mp4\"]
  }")
echo "$META_JOB" | python3 -m json.tool
META_JOB_ID=$(echo "$META_JOB" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['job_id'])")
curl -sf "$BASE/api/v2/collections/$COL_ID/metadata/jobs/$META_JOB_ID" \
  -H "X-API-Key: $KEY" | python3 -m json.tool

# ─── Multipart Upload (large files) ──────────────────────────────────────────
echo "=== 11. Initiate multipart upload ==="
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
echo "=== 12. Start S3 transfer ==="
# (Replace with actual S3 source)
echo "  POST $BASE/api/v2/transfers"
echo "  Body: {\"collection_id\": \"$COL_ID\", \"source_url\": \"s3://your-bucket/videos/\"}"

# ─── Cleanup ─────────────────────────────────────────────────────────────────
echo "=== 13. List media in collection ==="
curl -sf "$BASE/api/v2/collections/$COL_ID/media" -H "X-API-Key: $KEY" | python3 -m json.tool

echo ""
echo "Collection IDs created:"
echo "  InternVideo2: $COL_ID"
echo "  Qwen3-VL:     $QWEN_COL_ID"
