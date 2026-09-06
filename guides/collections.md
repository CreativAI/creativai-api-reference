# Collections

A collection is the top-level container for all your media and AI data. Everything — uploads, indexes, searches, data plates, and chat sessions — lives inside a collection.

## Embedding Models

Choose the model when creating the collection. **This cannot be changed later.**

| Model | `model` param | Vector dimensions | Accepts |
|---|---|---|---|
| Video-Only (default) | `"video_only"` | 512 (vision) + 1024 (subtitles) | Video |
| Multimodal | `"multimodal"` | 4096 (unified multimodal) | Video, images |

Use `"multimodal"` when you need to index images alongside video or want image-based semantic search.

---

## Create a Collection

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "security-footage-q1",
    "description": "Q1 2026 lobby and entrance cameras",
    "model": "video_only"
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
    "model": "video_only",
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
    "model": "video_only",
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

Supported content types: `video/mp4`, `video/quicktime`, `video/x-msvideo`, `image/jpeg`, `image/png`, `image/webp`.

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

### Confirm the Upload

After the PUT to S3 succeeds, call `confirm-upload` so the backend registers each media handle, kicks off preprocessing, and records any tags or metadata you want attached. On MinIO / non-AWS storage this is **required** (S3 event notifications are not available to auto-trigger preprocessing); on AWS it is still safe to call because the underlying trigger is idempotent.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/confirm-upload" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "media_ids": [
      "s3://your-bucket/collections/col_xxx/uploads/lobby.mp4",
      "s3://your-bucket/collections/col_xxx/uploads/entrance.mp4"
    ],
    "tags": {
      "*": ["q1-2026", "security"],
      "s3://your-bucket/collections/col_xxx/uploads/lobby.mp4": ["lobby", "camera-1"]
    },
    "metadata": {
      "*": {
        "region": {"datatype": "enum", "value": "eu"}
      },
      "s3://your-bucket/collections/col_xxx/uploads/lobby.mp4": {
        "duration": {"datatype": "number", "value": 24.5},
        "cameras": {"datatype": "list", "value": ["front", "rear"]}
      }
    },
    "metadata_schema": {
      "region": {"type": "enum", "values": ["eu", "us", "apac"]}
    }
  }'
```

`confirm-upload` returns `202 Accepted` with a `job_id` because the per-media fan-out (storage `HEAD`, queue publish, MongoDB write) grew past what a single request could safely hold. Tags, metadata and any inline schema are still validated **on the request thread** — a bad tag, an over-size metadata payload, or an enum value outside its declared set is still a `400`/`409`/`422` and nothing is confirmed.

Response:
```json
{
  "success": true,
  "data": {
    "job_id": "cuj_...",
    "status": "submitted",
    "poll_url": "/api/v2/collections/col_xxx/confirm-upload/jobs/cuj_..."
  }
}
```

Poll the job:
```bash
curl "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/confirm-upload/jobs/$JOB_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

`status` progresses `submitted` → `in_progress` → `completed` / `partial` / `failed`. A `partial` result means one handle failed (e.g. missing from S3) but the rest were confirmed — the failed handles land in `errors: [{media_id, error}, ...]` and the successful ones in `triggered` / `files`. Pass an `Idempotency-Key` header to make network retries safe.

**Wildcard vs. per-handle:** `"*"` is a **base layer applied to every handle** in `media_ids`, and a handle's own entry **overrides only the keys it names** — it is not a fallback that gets replaced by any per-handle value. The merged payload is what gets size-checked before anything is registered.

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

## Tags

Tags are free-text labels (`lobby`, `q1-2026`, `dashcam`, …) attached to a media file so that a semantic search can be narrowed to a subset of the collection. They are declared at **upload time** on `confirm-upload` and can be added/removed afterwards through an **asynchronous update job**.

Tags are stored on every chunk row in the search index. That is why a change is a job, not an inline field update — a 1-hour video is ~225 rows and each has to be rewritten. Re-embedding and index rebuild are **not** part of that cost (both schemas use a `FLAT` index and the vector is copied through unchanged), but the row round-trip is real, which is why the endpoint returns `202` with a `job_id`.

### List the vocabulary

```bash
curl "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/tags" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Response:
```json
{
  "success": true,
  "data": {
    "tags": ["camera-1", "entrance", "lobby", "q1-2026", "security"],
    "tag_counts": {"camera-1": 3, "entrance": 4, "lobby": 5, "q1-2026": 12, "security": 12}
  }
}
```

Use this to populate a tag picker next to the search box. `tags` is the sorted vocabulary; `tag_counts` reports how many media carry each tag so the picker can show the size of a filter before the user commits.

### Update tags on existing media

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/tags" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "add": ["reviewed"],
    "remove": ["draft"],
    "media_ids": [
      "s3://your-bucket/collections/col_xxx/uploads/lobby.mp4"
    ]
  }'
```

Or update every media in the collection:
```json
{ "add": ["archive-2026"], "all_media": true }
```

Response `202`:
```json
{ "success": true, "data": { "job_id": "tuj_...", "status": "submitted", "progress": 0 } }
```

Poll `GET /api/v2/collections/{collection_id}/tags/jobs/{job_id}`:
```json
{
  "job_id": "tuj_...",
  "status": "partial",
  "progress": 100,
  "total_media": 12,
  "processed_media": 12,
  "updated_media": 11,
  "updated_rows": 2431,
  "skipped": [{ "media_id": "s3://.../mid_.../uploads/x.mp4", "reason": "media is busy (indexing)" }],
  "errors": []
}
```

**Semantics:**

- Deltas, not replacement — adding a tag that is already present, or removing one that is absent, is a no-op, so the whole request is safe to retry after a network failure.
- Tags are lower-cased, whitespace-trimmed and de-duplicated. `"Happy"` at upload matches `"happy"` at search.
- Media currently preprocessing or indexing is **skipped**, not failed. The job finishes as `partial`; the skipped handles are listed. Retry once indexing finishes.
- Rewriting is streamed in batches, so peak memory is flat regardless of scope — but wall-clock time is not. A collection-wide retag on a large corpus can run for a while.

Filter search results by tag with the `tags` field on `POST /search` — see [indexing-and-search.md](indexing-and-search.md#filter-by-tags-and-metadata).

---

## Metadata

Metadata is a flat set of typed key/value properties attached to a media file — `{"duration": {"datatype": "number", "value": 24.5}}` — so that the exact half of a query (durations, regions, camera IDs) can be answered exactly instead of being handed to a vector search that cannot answer it.

Where tags are free-text labels with one operation (does this media carry the label?), metadata carries a **type** and with it comparison: less than, between, one of.

### Shape

Every key states its own type in a `{datatype, value}` envelope. `datatype` is **mandatory** — a bare value (`{"duration": 24.5}`) is rejected with `422`.

```json
{
  "duration": {"datatype": "number", "value": 24.5},
  "region":   {"datatype": "enum",   "value": "eu"},
  "cameras":  {"datatype": "list",   "value": ["front", "rear"]},
  "reviewed": {"datatype": "bool",   "value": true},
  "notes":    {"datatype": "string", "value": "front-camera-good"}
}
```

| Datatype | Notes |
|---|---|
| `number` | integers or floats |
| `string` | free text; `values` list closes once past 50 distinct values |
| `bool` | true / false |
| `enum` | must be declared first via `metadata_schema/enums` (or inline `metadata_schema`) |
| `list` | array of strings; numbers in a list are cast to strings |

**Storage ceiling:** 65,536 bytes of metadata per media, checked against the merged form after the `"*"` wildcard is applied. Key count, key length and list length are otherwise unbounded — the caller spends the budget however they like.

**Key normalisation:** case-folded, spaces and dashes become underscores, so `"Camera ID"` and `camera_id` cannot become two entries. Values keep their case.

### Read the learned schema

Metadata is open-ended — keys arrive with each upload rather than being declared up front. The **registry** is how a client discovers what is actually filterable.

```bash
curl "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/metadata-schema" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Response:
```json
{
  "success": true,
  "data": {
    "metadata_schema": {
      "duration": {"type": "number", "min": 3.2, "max": 3600.0, "count": 412},
      "region":   {"type": "string", "values": ["eu", "us", "apac"],
                   "value_counts": {"eu": 250, "us": 150, "apac": 12}, "count": 412},
      "clip_name": {"type": "string", "values": null, "value_counts": null, "count": 9001}
    }
  }
}
```

- `values` and `value_counts` are what make a **dropdown** possible. They become `null` together once the key exceeds 50 distinct values (free text).
- `min` / `max` are what make a **range slider** possible on number keys.
- A declared enum value nobody has uploaded yet reports a count of `0` rather than being absent.
- A key absent from the registry is rejected when referenced in a filter — a typo is a `400`, not a silently empty result set.

### Declare enums

A key's type is learned from the first value that carries it. An enum cannot work that way: its point is that a value outside the set is an error rather than a new member. Enums are **declared**, everything else is learned.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/metadata-schema/enums" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "metadata_schema": {
      "region": {"type": "enum", "values": ["eu", "us", "apac"]}
    }
  }'
```

- Declaring is **idempotent** and applies to the whole collection.
- Values can only be **added, never removed** — media already carry them; a narrower re-declaration is accepted and does nothing.
- A key already stored under another datatype cannot be redeclared as an enum (`409`).
- The same `metadata_schema` object is also accepted inline by `confirm-upload` and the metadata update endpoint, applied before the values in that request — so an enum can be declared and used in one call.

### One key, one type — strictly

A key keeps the datatype it was first given. A later upload declaring a different one for the same key is rejected with `409 Conflict`. There is no coercion: `"30"` is not quietly turned into `30`, because Milvus indexes a JSON path under a single inferred type — a mixed-type key would be **silently skipped** by every filter.

### Update metadata on existing media

Same shape as the tag update endpoint — `set` / `unset` deltas, `media_ids` or `all_media`, returns a `202` job.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/$COLLECTION_ID/metadata" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "set": {
      "reviewed": {"datatype": "bool", "value": true},
      "region":   {"datatype": "enum", "value": "us"}
    },
    "unset": ["draft"],
    "metadata_schema": {
      "region": {"type": "enum", "values": ["eu", "us", "apac", "latam"]}
    },
    "media_ids": [
      "s3://your-bucket/collections/col_xxx/uploads/entrance.mp4"
    ]
  }'
```

Poll `GET /api/v2/collections/{collection_id}/metadata/jobs/{job_id}`. Job states are the same as tag updates.

**Semantics:**

- Type conflicts and out-of-set enum values are collection-wide facts, so they are rejected as a **`400` before the job starts** — not by half-applying it.
- `metadata_schema` on the update body applies enum declarations before the delta, so a new enum member can be declared and used in one request.
- Media currently preprocessing or indexing is **skipped**, not failed. The job finishes as `partial`; retry once indexing finishes.
- When the job finishes, the metadata schema is recomputed from the media documents — a key whose last occurrence was unset disappears from `GET /metadata-schema`.

### What `GET /media` returns

Each item in `GET /api/v2/collections/{collection_id}/media` carries the media's own tags and metadata:

```json
{
  "media_id": "s3://.../lobby.mp4",
  "tags": ["lobby", "camera-1", "q1-2026"],
  "metadata": {
    "duration": 24.5,
    "region": "eu",
    "cameras": ["front", "rear"]
  },
  "indexed": true,
  "..."
}
```

`metadata` is the **read** shape — bare values only, no `{datatype, value}` envelope. Types come from the collection registry. Both fields are always present; an untagged item reports `[]` and an unenriched one reports `{}`.

---

## Organizations & Projects

See [organizations-and-projects.md](organizations-and-projects.md) for how to structure collections across organizations and projects.

## Sharing & Collaboration

See [sharing-and-rbac.md](sharing-and-rbac.md) for inviting team members, managing roles, and per-plate access scoping.

A **Collection** is the top-level container for your media (video, images). Every downstream operation — indexing, search, data plates, chat — is scoped to a collection.

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
| POST | `/api/v2/collections/{collection_id}/confirm-upload` | Confirm presigned uploads and start preprocessing (async, 202); accepts `tags`, `metadata`, `metadata_schema` |
| GET | `/api/v2/collections/{collection_id}/confirm-upload/jobs/{job_id}` | Poll a confirm-upload job |

### Tags

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v2/collections/{collection_id}/tags` | Sorted tag vocabulary + per-tag counts |
| POST | `/api/v2/collections/{collection_id}/tags` | Add/remove tag deltas (async, 202) |
| GET | `/api/v2/collections/{collection_id}/tags/jobs/{job_id}` | Poll a tag update job |

### Metadata

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v2/collections/{collection_id}/metadata-schema` | Learned metadata registry (types, values, ranges, counts) |
| POST | `/api/v2/collections/{collection_id}/metadata-schema/enums` | Declare enum keys and their legal values |
| POST | `/api/v2/collections/{collection_id}/metadata` | Set/unset metadata keys on media (async, 202) |
| GET | `/api/v2/collections/{collection_id}/metadata/jobs/{job_id}` | Poll a metadata update job |

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
| InternVideo2 | `"video_only"` | Video only |
| Multimodal | `"multimodal"` | Video, images |

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
    "model": "video_only"
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
    json={"collection_name": "my-library", "model": "video_only"})
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
