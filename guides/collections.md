# Collections

A collection is the top-level container for all your media and AI data. Everything — uploads, indexes, searches, data plates, and chat sessions — lives inside a collection.

## Embedding Models

Choose the model when creating the collection. **This cannot be changed later.**

| Model | `model` param | Vector dimensions | Accepts |
|---|---|---|---|
| InternVideo2 (default) | `"default"` | 512 (vision) + 1024 (subtitles) | Video only |
| Qwen3-VL | `"qwen"` | 4096 (unified multimodal) | Video, images, PDFs |

Use `"qwen"` when you need to index images or PDFs, or want image-based search.

---

## Create a Collection

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "security-footage-q1",
    "description": "Q1 2026 lobby and entrance cameras",
    "model": "default"
  }'
```

With organization/project scope:
```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "security-footage-q1",
    "description": "Q1 2026 lobby cameras",
    "model": "default",
    "organization_id": "org_abc123",
    "project_name": "Campus Security"
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "collection_id": "col_xxxxxxxxxxx",
    "collection_name": "security-footage-q1",
    "description": "Q1 2026 lobby and entrance cameras",
    "model": "internvideo2",
    "status": "active",
    "created_at": "2026-05-25T10:00:00Z"
  }
}
```

**Tier limits**: Your plan enforces a maximum number of collections. If the limit is reached you receive error code `TIER_LIMIT`. Delete unused collections or upgrade your plan.

---

## List Collections

```bash
# All collections owned by you
curl "$CREATIVAI_BASE_URL/api/v2/collections" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Filter by organization
curl "$CREATIVAI_BASE_URL/api/v2/collections?organization_id=org_abc123" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Response includes pre-computed stats (video count, total duration, storage GB) so this endpoint is fast even with large collections.

---

## Get Collection Details

```bash
curl "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Returns all media in the collection with their preprocessing status.

---

## List Collections by Organization / Project

```bash
# By organization
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/by-organization" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"organization_id": "org_abc123"}'

# By project
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/by-project" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"organization_id": "org_abc123", "project_name": "Campus Security"}'
```

---

## Update a Collection

Only `collection_name` and `description` can be updated. Requires admin/owner role.

```bash
curl -X PATCH "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "security-footage-q1-archive",
    "description": "Archived Q1 2026 footage"
  }'
```

---

## Delete a Collection

**Irreversible.** Deletes all media, indexes, plates, and extracted data.

```bash
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Restore a Suspended Collection

If your subscription lapses, collections may be suspended. Restore after re-subscribing:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/restore" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Collection Status Values

| Status | Meaning |
|---|---|
| `active` | Normal operation |
| `suspended` | Access restricted (billing issue) |
| `deleted` | Soft-deleted, pending cleanup |

---

## Media Management

### List Media

```bash
curl "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/media" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Returns all media with `preprocessing_status`, `indexing_status`, `media_type`, duration, and file size.

### Remove Media

```bash
# By S3 URIs
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/media" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "media_urls_list": [
      "s3://your-bucket/collections/col_xxx/uploads/video1.mp4",
      "s3://your-bucket/collections/col_xxx/uploads/video2.mp4"
    ]
  }'
```

**Guard**: Cannot delete media while an indexing job is in progress. You will receive `BAD_REQUEST: Cannot delete media while indexing is in progress`.

---

## Upload Workflows

### Single File

```bash
# Step 1: Get presigned URL
UPLOAD=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/upload-url" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"filename": "lobby.mp4", "content_type": "video/mp4"}')

UPLOAD_URL=$(echo $UPLOAD | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['upload_url'])")

# Step 2: PUT directly to S3
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: video/mp4" \
  --data-binary @lobby.mp4
```

Supported content types: `video/mp4`, `video/quicktime`, `video/x-msvideo`, `image/jpeg`, `image/png`, `image/webp`, `application/pdf`.

### Batch Files

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/upload-urls" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {"filename": "lobby.mp4", "content_type": "video/mp4"},
      {"filename": "entrance.mp4", "content_type": "video/mp4"}
    ]
  }'
```

Returns a list of `{filename, upload_url, s3_key}` objects.

### Large Files — Multipart Upload

For files over 100 MB, use the multipart upload API (maximum part size: 25 MB each).

```bash
# 1. Initiate
INIT=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/collections/uploads/initiate" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "files": [{"filename": "4k-footage.mp4", "file_size": 524288000, "content_type": "video/mp4"}]
  }')

UPLOAD_ID=$(echo $INIT | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['upload_id'])")
# Each upload has its own part_upload_urls list

# 2. Upload each part (split file into 25 MB slices)
# Save the ETag from each HTTP response header

# 3. Complete
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/uploads/$UPLOAD_ID/complete" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "parts": [
      {"part_number": 1, "etag": "\"etag_from_part_1\""},
      {"part_number": 2, "etag": "\"etag_from_part_2\""},
      {"part_number": 3, "etag": "\"etag_from_part_3\""}
    ]
  }'
```

### S3 Bucket Transfer

Transfer videos from an existing S3 bucket or a list of presigned/public URLs:

```bash
# From S3 prefix (lists bucket contents automatically)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/transfers" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "source_url": "s3://my-archive-bucket/footage/2026/"
  }'

# From a list of presigned URLs
curl -X POST "$CREATIVAI_BASE_URL/api/v2/transfers" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "source_urls": [
      "https://s3.amazonaws.com/bucket/video1.mp4?AWSAccessKeyId=...",
      "https://s3.amazonaws.com/bucket/video2.mp4?AWSAccessKeyId=..."
    ]
  }'
```

Poll the returned `job_id`:
```bash
curl "$CREATIVAI_BASE_URL/api/v2/transfers/$JOB_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Organizations & Projects

See [organizations-and-projects.md](organizations-and-projects.md) for how to structure collections across organizations and projects.

## Sharing & Collaboration

See [sharing-and-rbac.md](sharing-and-rbac.md) for inviting team members, managing roles, and per-plate access scoping.

A **Collection** is the top-level container for your media (video, image, PDF). Every downstream operation — indexing, search, data plates, chat — is scoped to a collection.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v2/collections` | Create collection |
| GET | `/api/v2/collections` | List your collections |
| POST | `/api/v2/collections/by-organization` | List collections by org |
| POST | `/api/v2/collections/by-project` | List collections by project |
| GET | `/api/v2/collections/{collection_id}` | Get collection + all media |
| PATCH | `/api/v2/collections/{collection_id}` | Update name / description |
| DELETE | `/api/v2/collections/{collection_id}` | Delete collection (admin) |
| POST | `/api/v2/collections/{collection_id}/restore` | Restore soft-deleted collection |
| GET | `/api/v2/collections/{collection_id}/media` | List media in collection |
| DELETE | `/api/v2/collections/{collection_id}/media` | Remove specific media files |
| POST | `/api/v2/collections/{collection_id}/upload-url` | Get presigned S3 URL (single file) |
| POST | `/api/v2/collections/{collection_id}/upload-urls` | Get presigned URLs (batch) |

### Multipart Uploads (large files)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v2/collections/uploads/initiate` | Initiate multipart upload |
| POST | `/api/v2/collections/uploads/{upload_id}/complete` | Complete multipart upload |
| DELETE | `/api/v2/collections/uploads/{upload_id}` | Abort multipart upload |
| POST | `/api/v2/collections/uploads/{upload_id}/regenerate-urls` | Regenerate expired part URLs |

### S3 / External URL Transfers

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v2/transfers` | Start async transfer from S3 bucket or external URL |
| GET | `/api/v2/transfers/{job_id}` | Poll transfer job status |
| POST | `/api/v2/transfers/validate` | Validate source URL accessibility |

---

## Model Selection

Each collection is bound to one embedding model at creation time and cannot be changed later.

| Model | Value | Supports |
|-------|-------|----------|
| InternVideo2 | `"default"` | Video only |
| Qwen3-VL | `"qwen"` | Video, images, PDFs |

---

## cURL Examples

### Create a collection

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "my-video-library",
    "description": "Marketing footage Q1 2026",
    "model": "default"
  }'
```

### List your collections

```bash
curl -X GET "$CREATIVAI_BASE_URL/api/v2/collections" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### Get a presigned upload URL

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/upload-url" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"file_name": "campaign.mp4", "content_type": "video/mp4"}'
```

Use the returned `upload_url` to PUT the file directly to S3 — no proxying through the API.

```bash
curl -X PUT "$UPLOAD_URL" \
  -H "Content-Type: video/mp4" \
  --data-binary @campaign.mp4
```

### Batch presigned URLs

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/upload-urls" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {"file_name": "video1.mp4", "content_type": "video/mp4"},
      {"file_name": "video2.mp4", "content_type": "video/mp4"}
    ]
  }'
```

### Transfer from an external URL or S3

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/transfers" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'"$COLLECTION_ID"'",
    "source_urls": ["https://cdn.example.com/video1.mp4"]
  }'
```

Poll until `status` is `completed`:

```bash
curl -X GET "$CREATIVAI_BASE_URL/api/v2/transfers/$JOB_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### List media in a collection

```bash
curl -X GET "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/media" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### Delete specific media files

```bash
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/media" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"media_file_keys": ["uploads/campaign.mp4"]}'
```

### Delete a collection

```bash
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Python Example

```python
import os, requests

BASE = os.environ["CREATIVAI_BASE_URL"]
KEY  = os.environ["CREATIVAI_API_KEY"]
headers = {"X-API-Key": KEY}

# Create
resp = requests.post(f"{BASE}/api/v2/collections",
    headers=headers,
    json={"collection_name": "my-library", "model": "default"})
resp.raise_for_status()
collection_id = resp.json()["data"]["collection_id"]

# Request a presigned upload URL
resp = requests.post(
    f"{BASE}/api/v2/collections/{collection_id}/upload-url",
    headers=headers,
    json={"file_name": "demo.mp4", "content_type": "video/mp4"})
resp.raise_for_status()
upload_url = resp.json()["data"]["upload_url"]
file_key   = resp.json()["data"]["file_key"]

# Upload directly to S3
with open("demo.mp4", "rb") as f:
    requests.put(upload_url, data=f, headers={"Content-Type": "video/mp4"}).raise_for_status()

print("Uploaded:", file_key)
```

---

## Common Workflow

```
Create collection → Get upload URL → PUT file to S3 → (optional) verify preprocessing → Start indexing
```

See `indexing-and-search.md` for the next steps after upload.
