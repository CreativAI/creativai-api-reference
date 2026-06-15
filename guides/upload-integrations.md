# Upload Integrations — Google Drive, Dropbox & Hugging Face

CreativAI supports importing media from three external providers without requiring you to download files first. The backend fetches the files directly from the provider and uploads them into your collection using the same multipart S3 pipeline as any other media.

> **No local upload required.** Your users never have to wait for a large video to travel through their browser. Files go from the provider's servers straight into your collection.

---

## How It Works

```
User (browser)                  CreativAI Backend              Provider
      │                                │                           │
      │── 1. OAuth login ──────────────►│                           │
      │◄─ access_token ────────────────│                           │
      │                                │                           │
      │── 2. List files ───────────────►│── GET file list ─────────►│
      │◄─ file list ───────────────────│◄─ file metadata ──────────│
      │                                │                           │
      │── 3. Select & transfer ────────►│                           │
      │                                │── Download file ──────────►│
      │                                │◄─ file bytes ─────────────│
      │                                │── Upload to S3 ────────────►
      │◄─ per-file results ────────────│
```

1. Your app initiates the OAuth flow and receives an `access_token`.
2. Your app calls the **list** endpoint to display the user's files.
3. User selects files — your app calls the **transfer** endpoint.
4. The backend downloads from the provider and uploads to the collection.
5. Your app reads `results[].status` per file to show progress.

---

## Authentication

All upload integration endpoints require your CreativAI API key:

```
X-API-Key: <YOUR_CREATIVAI_API_KEY>
```

The provider OAuth token (`access_token` for Google Drive/Dropbox, `token` for Hugging Face) is passed in the **request body or query string** — it is the user's token for that provider, not your CreativAI key.

---

## Google Drive

### Prerequisites

Set up a Google Cloud project and enable the **Google Drive API**. Configure an OAuth 2.0 client for your app's redirect URI. When the user completes the OAuth flow, you receive an `access_token` (and optionally a `refresh_token` for long sessions).

**Required OAuth scope:** `https://www.googleapis.com/auth/drive.readonly`

### List Drive Files

```bash
GET /api/v2/upload/google-drive/files
```

Lists the user's Google Drive video files (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.mpeg`).

**Query parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `access_token` | string | Yes | Google Drive OAuth access token |
| `page_token` | string | No | Pagination token from a previous response |

```bash
# First page
curl "$CREATIVAI_BASE_URL/api/v2/upload/google-drive/files?access_token=$GOOGLE_ACCESS_TOKEN" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Next page
curl "$CREATIVAI_BASE_URL/api/v2/upload/google-drive/files?access_token=$GOOGLE_ACCESS_TOKEN&page_token=$NEXT_PAGE_TOKEN" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
        "name": "interview.mp4",
        "mimeType": "video/mp4",
        "size": "104857600",
        "createdTime": "2024-01-15T10:30:00.000Z",
        "modifiedTime": "2024-01-15T10:30:00.000Z",
        "webViewLink": "https://drive.google.com/file/d/.../view",
        "thumbnailLink": "https://..."
      }
    ],
    "next_page_token": "token_for_next_page_or_null"
  },
  "error": null
}
```

| Field | Type | Description |
|---|---|---|
| `files[].id` | string | Drive file ID — pass this to the transfer endpoint |
| `files[].name` | string | Display filename |
| `files[].size` | string | File size in bytes (string) |
| `next_page_token` | string \| null | Use as `page_token` to load the next page |

### Transfer Drive Files to a Collection

```bash
POST /api/v2/upload/google-drive/transfer
```

Downloads selected Drive files and uploads them into a collection. Files are processed sequentially.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/upload/google-drive/transfer" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "access_token": "'$GOOGLE_ACCESS_TOKEN'",
    "file_ids": [
      "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
      "2CyjtWUt1SB6oGNLeW7cAajnvVrqumvw85PhWF3vquns"
    ],
    "file_names": ["interview.mp4", "keynote.mp4"]
  }'
```

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `collection_id` | string | Yes | Target collection ID |
| `access_token` | string | Yes | Google Drive OAuth token |
| `file_ids` | string[] | Yes | Drive file IDs to import |
| `file_names` | string[] | Yes | Display names — must match `file_ids` order |

**Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "file_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
        "status": "ok",
        "video_id": "vid_abc123"
      },
      {
        "file_id": "2CyjtWUt1SB6oGNLeW7cAajnvVrqumvw85PhWF3vquns",
        "status": "failed",
        "error": "Drive download failed: File not found"
      }
    ]
  },
  "error": null
}
```

> **Important:** The endpoint returns `200` even when individual files fail. Always check `results[].status` for every file — do **not** rely solely on the HTTP status code.

| Field | Type | Description |
|---|---|---|
| `results[].file_id` | string | The Drive file ID from the request |
| `results[].status` | `"ok"` \| `"failed"` | Transfer outcome for this file |
| `results[].video_id` | string | New video ID in the collection (`status == "ok"` only) |
| `results[].error` | string | Human-readable reason (`status == "failed"` only) |

---

## Dropbox

### Prerequisites

Register a Dropbox app at [dropbox.com/developers](https://www.dropbox.com/developers). Enable the `files.content.read` permission. When the user completes OAuth, you receive an `access_token`.

> **App credentials:** The Dropbox app key is `42gvfdsq96oi0sd`. This is the shared app used by CreativAI's backend for token validation. You still need your own OAuth redirect URI.

### List Dropbox Files

```bash
GET /api/v2/upload/dropbox/files
```

Lists the user's Dropbox video files.

**Query parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `access_token` | string | Yes | Dropbox OAuth access token |
| `cursor` | string | No | Pagination cursor from a previous response |

```bash
# First page
curl "$CREATIVAI_BASE_URL/api/v2/upload/dropbox/files?access_token=$DROPBOX_ACCESS_TOKEN" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Next page (when has_more: true)
curl "$CREATIVAI_BASE_URL/api/v2/upload/dropbox/files?access_token=$DROPBOX_ACCESS_TOKEN&cursor=$CURSOR" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": "id:abc123xyz",
        "name": "conference_talk.mp4",
        "path": "/Videos/conference_talk.mp4",
        "size": 52428800
      }
    ],
    "cursor": "AAH4...",
    "has_more": false
  },
  "error": null
}
```

| Field | Type | Description |
|---|---|---|
| `files[].id` | string | Dropbox file ID |
| `files[].name` | string | Display filename |
| `files[].path` | string | Dropbox `path_display` — pass this to the transfer endpoint |
| `files[].size` | number \| null | File size in bytes |
| `cursor` | string \| null | Use as `cursor` for the next page |
| `has_more` | boolean | Whether more files exist |

### Transfer Dropbox Files to a Collection

```bash
POST /api/v2/upload/dropbox/transfer
```

Downloads selected Dropbox files and uploads them into a collection. Files are processed sequentially.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/upload/dropbox/transfer" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "access_token": "'$DROPBOX_ACCESS_TOKEN'",
    "file_paths": [
      "/Videos/conference_talk.mp4",
      "/Archive/panel_discussion.mp4"
    ],
    "file_names": ["conference_talk.mp4", "panel_discussion.mp4"]
  }'
```

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `collection_id` | string | Yes | Target collection ID |
| `access_token` | string | Yes | Dropbox OAuth token |
| `file_paths` | string[] | Yes | Dropbox `path_display` values from the list response |
| `file_names` | string[] | Yes | Display names — must match `file_paths` order |

**Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "results": [
      { "path": "/Videos/conference_talk.mp4", "status": "ok", "video_id": "vid_xyz" },
      { "path": "/Archive/broken.mp4", "status": "failed", "error": "Download failed" }
    ]
  },
  "error": null
}
```

| Field | Type | Description |
|---|---|---|
| `results[].path` | string | The Dropbox path from the request |
| `results[].status` | `"ok"` \| `"failed"` | Transfer outcome |
| `results[].video_id` | string | New video ID in the collection (on success) |
| `results[].error` | string | Failure reason (on failure) |

---

## Hugging Face

Hugging Face is used to import videos from dataset or model repositories. No OAuth popup is required — you provide a Hugging Face access token (or omit it for public repos).

### Transfer Hugging Face Files to a Collection

```bash
POST /api/v2/upload/huggingface/transfer
```

Downloads files from a Hugging Face repo and uploads them into a collection. Up to **4 files are processed concurrently**.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/upload/huggingface/transfer" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "token": "'$HF_TOKEN'",
    "files": [
      {
        "url": "https://huggingface.co/datasets/my-org/my-dataset/resolve/main/clip1.mp4",
        "name": "clip1.mp4"
      },
      {
        "url": "https://huggingface.co/datasets/my-org/my-dataset/resolve/main/clip2.mp4",
        "name": "clip2.mp4"
      }
    ]
  }'
```

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `collection_id` | string | Yes | Target collection ID |
| `token` | string | No | HF access token — required for private repos, optional for public |
| `files` | object[] | Yes | Files to import |
| `files[].url` | string | Yes | Direct download URL — must be a `huggingface.co` or `hf.co` HTTPS URL |
| `files[].name` | string | Yes | Display filename used inside the collection |

> **Security:** Only `https://huggingface.co` and `https://hf.co` URLs are accepted. Any other URL returns `200` with `status: "failed"` per file (SSRF guard, not a top-level error).

**Response (`200 OK`):**
```json
{
  "success": true,
  "data": {
    "results": [
      { "name": "clip1.mp4", "status": "ok", "video_id": "vid_abc" },
      { "name": "clip2.mp4", "status": "failed", "error": "Download failed: HTTP 404" }
    ]
  },
  "error": null
}
```

| Field | Type | Description |
|---|---|---|
| `results[].name` | string | The filename from the request |
| `results[].status` | `"ok"` \| `"failed"` | Transfer outcome |
| `results[].video_id` | string | New video ID in the collection (on success) |
| `results[].error` | string | Failure reason (on failure) |

### Building the File URL

Hugging Face file URLs follow this pattern:

```
https://huggingface.co/{owner}/{repo}/resolve/{branch}/{path/to/file.mp4}
```

**Example — dataset:**
```
https://huggingface.co/datasets/my-org/surveillance-dataset/resolve/main/videos/cam1.mp4
```

**Example — model repo (for video model outputs):**
```
https://huggingface.co/my-org/my-model/resolve/main/samples/output.mp4
```

To browse available files, use the [Hugging Face Hub API](https://huggingface.co/docs/hub/api) or the web UI to get the correct branch and path.

---

## After Import — What Happens Next

Once files are transferred (any provider), they enter the standard preprocessing pipeline:

```
Transfer complete
      ↓
Preprocessing (Lambda, auto) — ~1–3 min/video
      ↓  Poll: GET /api/v2/indexing/preprocessing-status/{collection_id}
Indexing (you trigger)
      ↓  POST /api/v2/indexing/chunk-based
Searchable
```

See [indexing-and-search.md](indexing-and-search.md) for how to check preprocessing status, estimate indexing cost, and start the indexing job.

---

## Error Reference

| HTTP Status | When It Happens | Recommended Action |
|---|---|---|
| `401` | Missing or invalid CreativAI API key | Redirect to login |
| `401` | Provider token expired (message contains "expired") | Re-trigger OAuth for that provider |
| `403` | No write access to the collection | Show permission error |
| `400` | Missing required field | Show field-level validation error |
| `500` | Unexpected server error | Show generic error, retry once |

> **Partial success:** Transfer endpoints always return `200`. A request with 5 files where 2 fail still returns `200`. Always iterate over `results` and surface per-file failures.

---

## Operational Notes

### Access tokens are short-lived

Google Drive and Dropbox tokens expire in ~1 hour. If a list or transfer call returns `401` with a detail containing "expired", re-run the OAuth flow to obtain a fresh token before retrying.

### Transfer requests can be slow

File transfers involve downloading from the provider and uploading to S3:

| File Size | Approximate Time |
|---|---|
| < 50 MB | 5–15 seconds |
| 50–500 MB | 30 seconds – 3 minutes |
| > 500 MB | Several minutes |

Show a per-file progress indicator and do not set a short client-side timeout.

### API Gateway timeout (Hugging Face)

When hitting the production endpoint via `creativai-apis.com` (API Gateway), requests are hard-killed after **29 seconds**. For large Hugging Face files (> ~5 MB), the backend may still be processing after the gateway times out. If you receive a `504`, **retry the request** — the file may complete on the retry. Retry up to 3 times with a short delay.

### All plans support external upload

The `upload_s3_dropbox_gdrive` feature is available on all plans (Free, Plus, Pro, Education, Enterprise). There is no tier restriction on which plan can use Google Drive, Dropbox, or Hugging Face transfers.

---

## Next Steps

After your media is transferred:

1. [indexing-and-search.md](indexing-and-search.md) — preprocess and index your imported media
2. [data-plates.md](data-plates.md) — create curated plates from search results
3. [knowledge-extraction.md](knowledge-extraction.md) — extract structured AI answers from segments
4. [agentic-chat.md](agentic-chat.md) — run multi-step AI analysis over your collection
