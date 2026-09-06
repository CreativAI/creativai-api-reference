# CreativAI API — Complete Endpoint Registry

> Last updated: 2026-09-06  
> This document is published as integration reference and intentionally excludes backend implementation details.  
> **Version policy:** Use `/api/v2/` for all client integrations. Some deployments still expose `/api/v3/` aliases for backward compatibility.  
> **Base URL:** `https://creativai-apis.com`  
> **Auth:** `X-API-Key: <KEY>` or `Authorization: Bearer <KEY>`  
> **Response envelope:** `{"success": bool, "data": <payload>, "error": {"code": "...", "message": "...", "details": {}, "timestamp": "..."}}`

---

## Summary

| Module | # Endpoints | Notes |
|--------|-------------|-------|
| Health | 4 | No auth |
| Organizations | 4 | |
| Projects | 4 | |
| Collections | 8 | |
| Media / Videos | 6 | Adds `confirm-upload` (async, tags + metadata) |
| Multipart Uploads | 4 | |
| S3 Transfers | 3 | |
| Indexing | 6 | Async (202) |
| Tags & Metadata | 7 | Vocabulary + async update jobs |
| Search | 5 | POST /search is now async (202); GET /search/jobs/{id} to poll; video-query aliases |
| Data Plates | 17 | Adds `verify` |
| Sub-Plates | 9 | v2 |
| Knowledge Extraction | 9 | Adds `columns/estimate-cost` |
| Chat (Plate Sessions) | 5 | |
| Agentic Chat | 12 | SSE streaming + one-shot structured-query |
| Jobs | 1 | Unified job cancellation |
| Collection Sharing & RBAC | 24 | |
| Collection Tasks | 12 | |
| Live Stream — Sessions | 10 | `video_only` / `multimodal` models |
| Live Stream — Protocol Streams | 7 | |
| Live Stream — MediaMTX | 6 | |
| Live Stream — Internal Webhooks | 4 | Internal only |
| Live Stream — WebRTC Proxy | 4 | `?token=` auth |
| Online Search | 6 | Async |
| YouTube Search | 9 | **v2** (latest) |
| Transactions | 9 | |
| Users | 11 | Adds `api-key-check` |
| Payments | 4 | Adds `checkout` |
| Subscriptions | 15 | Adds admin-only surface |
| Invoices | 3 | |
| Admin Dashboard | 29 | Adds overview, revenue, credits, cloud-costs, user-activity, credit-override |
| Authentication & API Keys | 6 | Firebase-bearer, dashboard-only |
| License | 2 | Deployment entitlements |
| Files | 1 | Presigned GET redirect |
| Upload Integrations | 5 | Google Drive, Dropbox, Hugging Face |
| **Total** | **~271** | |

---

## 1. Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | API root / version info |
| GET | `/health` | No | Health check for load balancers |
| GET | `/health/simple` | No | Minimal ALB liveness probe |
| GET | `/api/v2/health` | No | Versioned health endpoint |

---

## 2. Organizations

Prefix: `/api/v2/organizations`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/organizations` | Yes | Create organization |
| GET | `/api/v2/organizations` | Yes | List user's organizations |
| GET | `/api/v2/organizations/{org_id}` | Yes | Get organization details |
| DELETE | `/api/v2/organizations/{org_id}` | Yes | Delete organization + all contents |

---

## 3. Projects

Prefix: `/api/v2/organizations/{org_id}/projects`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/organizations/{org_id}/projects` | Yes | Create project in org |
| GET | `/api/v2/organizations/{org_id}/projects` | Yes | List projects in org |
| GET | `/api/v2/organizations/{org_id}/projects/{project_name}` | Yes | Get project + its collections |
| DELETE | `/api/v2/organizations/{org_id}/projects/{project_name}` | Yes | Delete project + all collections |

---

## 4. Collections

Prefix: `/api/v2/collections`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/collections` | Yes | Create collection (video-only or multi-modal `model`) |
| GET | `/api/v2/collections` | Yes | List collections (with pre-computed stats) |
| POST | `/api/v2/collections/by-organization` | Yes | List collections by org |
| POST | `/api/v2/collections/by-project` | Yes | List collections by project |
| GET | `/api/v2/collections/{collection_id}` | Yes | Get collection + all media |
| PATCH | `/api/v2/collections/{collection_id}` | Yes | Update name / description (admin) |
| DELETE | `/api/v2/collections/{collection_id}` | Yes | Delete collection (admin, irreversible) |
| POST | `/api/v2/collections/{collection_id}/restore` | Yes | Restore a suspended collection |

---

## 5. Media / Videos

Prefix: `/api/v2/collections/{collection_id}`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/collections/{collection_id}/media` | Yes | List all media with preprocessing status; each item includes `tags: [str]` and `metadata: {key: value}` (bare, no `{datatype, value}` envelope) |
| DELETE | `/api/v2/collections/{collection_id}/media` | Yes | Remove specific media files |
| POST | `/api/v2/collections/{collection_id}/upload-url` | Yes | Get presigned S3 URL (single file) |
| POST | `/api/v2/collections/{collection_id}/upload-urls` | Yes | Get presigned URLs (batch) |
| POST | `/api/v2/collections/{collection_id}/confirm-upload` | Yes | Confirm presigned uploads and start preprocessing (async, 202). Accepts optional `tags` and `metadata` maps keyed by media handle, with `"*"` wildcard applying to every handle. `metadata_schema` may declare enums inline. Idempotency-Key header supported. |
| GET | `/api/v2/collections/{collection_id}/confirm-upload/jobs/{job_id}` | Yes | Poll a confirm-upload job — `triggered`, `files`, `errors` |

---

## 6. Multipart Uploads

Prefix: `/api/v2/collections/uploads`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/collections/uploads/initiate` | Yes | Initiate multipart upload |
| POST | `/api/v2/collections/uploads/{upload_id}/complete` | Yes | Complete multipart upload with ETags |
| DELETE | `/api/v2/collections/uploads/{upload_id}` | Yes | Abort multipart upload |
| POST | `/api/v2/collections/uploads/{upload_id}/regenerate-urls` | Yes | Regenerate expired part URLs |

---

## 7. S3 Transfers

Prefix: `/api/v2/transfers`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/transfers` | Yes | Start async transfer from external S3/URL (202) |
| GET | `/api/v2/transfers/{job_id}` | Yes | Poll transfer job status |
| POST | `/api/v2/transfers/validate` | Yes | Validate source URL accessibility before transfer |

---

## 8. Indexing

Prefix: `/api/v2/indexing`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/indexing/chunk-based` | Yes | Start indexing job (202) |
| GET | `/api/v2/indexing/chunk-based/{indexing_id}/status` | Yes | Poll indexing job status |
| POST | `/api/v2/indexing/chunk-based/estimate-cost` | Yes | Estimate credit cost before indexing |
| GET | `/api/v2/indexing/preprocessing-status/{collection_id}` | Yes | Get preprocessing status for all media |
| GET | `/api/v2/indexing/preprocessed-videos/{collection_id}` | Yes | List media ready for indexing |
| GET | `/api/v2/indexing/video-status` | Yes | Preprocessing status for a specific video |

**Key indexing body params:** `collection_id` (required), `media_ids` (optional list of media handles). Sending `tags` here is now rejected with `400` — tags are declared at upload time on `POST /api/v2/collections/{collection_id}/confirm-upload`, because they are written onto the chunk rows the moment preprocessing creates them.

---

## 9. Tags & Metadata

Per-media labels (`tags`) and typed key/value properties (`metadata`) are declared at upload time on `POST /api/v2/collections/{collection_id}/confirm-upload` and used as filters on `POST /api/v2/search`. Changing them after upload rewrites every chunk row of the affected media, so those endpoints return `202` with a `job_id`.

Prefix: `/api/v2/collections/{collection_id}`

### Tag vocabulary and updates

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/collections/{collection_id}/tags` | Yes | Sorted vocabulary of tags in use; response carries `tags: [str]` and `tag_counts: {tag: count}`. Recomputed after every tag update job — a tag that no longer applies to any media disappears from it. |
| POST | `/api/v2/collections/{collection_id}/tags` | Yes | Add/remove tag deltas across media in the collection (202, background job). Body: `{add?: [str], remove?: [str], media_ids?: [str], all_media?: bool}`. Media that is still preprocessing or currently indexing is **skipped** (not failed) and the job finishes as `partial` — retry once indexing finishes. |
| GET | `/api/v2/collections/{collection_id}/tags/jobs/{job_id}` | Yes | Poll a tag update job — `submitted` → `in_progress` → `completed` / `partial` / `failed` |

### Metadata schema and updates

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/collections/{collection_id}/metadata-schema` | Yes | The collection's learned metadata registry: each key's `type` (`number`, `string`, `bool`, `enum`, `list`), the observed `values` and `value_counts` (nulled once a string key exceeds 50 distinct values), `min`/`max` for numeric keys, and `count`. Feed the chosen keys into `meta_filter` on `POST /search`. |
| POST | `/api/v2/collections/{collection_id}/metadata-schema/enums` | Yes | Declare enum keys and their legal values, e.g. `{"metadata_schema": {"region": {"type": "enum", "values": ["eu", "us", "apac"]}}}`. Declaration only — records nothing on media. Idempotent; values may only be added, never removed. A key already stored under another datatype cannot be redeclared as an enum (`409`). |
| POST | `/api/v2/collections/{collection_id}/metadata` | Yes | Set/unset metadata keys on media in this collection (202, background job). Body: `{set?: {key: {datatype, value}}, unset?: [str], metadata_schema?: {...}, media_ids?: [str], all_media?: bool}`. Enum widenings in `metadata_schema` are applied before the delta so a new member can be declared and used in one request. Type conflicts and out-of-set enum values are rejected before the job starts (`400`). |
| GET | `/api/v2/collections/{collection_id}/metadata/jobs/{job_id}` | Yes | Poll a metadata update job — `submitted` → `in_progress` → `completed` / `partial` / `failed` |

**Metadata envelope on write:** every value carries its type, e.g. `{"duration": {"datatype": "number", "value": 24.5}, "region": {"datatype": "enum", "value": "eu"}, "cameras": {"datatype": "list", "value": ["front", "rear"]}}`. `datatype` is one of `number`, `string`, `bool`, `enum`, `list`. Bare values are rejected with `422`. `GET /media` returns the **read** shape — bare values only, no envelope. Storage ceiling is 65,536 bytes of metadata per media (checked against the merged form after the `"*"` wildcard is applied).

---

## 10. Search

Prefix: `/api/v2/search`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/search` | Yes | Submit a semantic search (hybrid / vision / audio / image / video). Returns `202` with a `search_job_id` for new searches; returns `200` with the page when paginating an existing `search_id`. |
| POST | `/api/v2/search/upload-url` | Yes | Presigned S3 PUT URL for a video-query clip (multimodal collections only). Alias: `/api/v2/search/video/upload-url` |
| POST | `/api/v2/search/estimate` | Yes | Estimate credit cost of a search. Alias: `/api/v2/search/video/estimate` |
| GET | `/api/v2/search/jobs/{job_id}` | Yes | Poll any search job (`ssj_...`, `vsj_...`) — returns `submitted` / `in_progress` until the search finishes, then `completed` with the first page and, when metadata was in play, a `metadata_filter` block naming what actually ran |
| POST | `/api/v2/search/{search_id}/feedback` | Yes | Report result quality on a completed search |

**Request body params:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `collection_id` | string | Yes | |
| `text_query` | string | Yes | Natural language search query |
| `search_type` | string | No | `"hybrid"` (default), `"vision"`, `"audio"` |
| `page_number` | int | No | 1-indexed (default: 1) |
| `page_size` | int | No | Results per page (default: 100, max ~500) |
| `search_id` | string | No | Reuse previous search for pagination (bypasses the async submit path) |
| `video_urls` | list[string] | No | Restrict to specific S3 URIs |
| `tags` | list[string] | No | Restrict to media carrying **at least one** of these tags (OR semantics, case-insensitive). Vocabulary from `GET /collections/{id}/tags`. |
| `meta_filter` | object | No | AST-shaped filter over metadata keys (`{op: and\|or, clauses: [{key, cmp, value}, ...]}`). Comparators depend on the key type — see `guides/indexing-and-search.md`. Referencing a key the collection has never seen is `400`. |
| `plan_metadata` | bool | No | When `true`, an LLM splits `text_query` into its visual part and its metadata part. Opt-in because it costs one extra LLM call on the request path. Ignored when `meta_filter` is supplied explicitly, no-op on collections with no metadata. |
| `refine_query` | bool | No | LLM rewrites query for better recall |
| `min_score` | float | No | Drop hits scoring below this floor (buckets are still returned; scale is model-dependent) |
| `include_scores` | bool | No | Return `scores` array (raw similarities before bucketing and `min_score`) |
| `score_bins` | int | No | Return a `score_histogram` with this many equal-width bins to help calibrate `min_score` |
| `image_base64` | string | No | Base64 image for visual query (multi-modal collections; deprecated in favour of `image_key`) |
| `image_key` | string | No | S3 key of uploaded image (multi-modal collections, preferred) |
| `video_key` | string | No | S3 key of an uploaded query clip (from `POST /search/upload-url`) — routes the search through the GPU video-query pipeline |
| `top_k` | int | No | Max results for a video-query search |

**Job response fields (when completed):**

| Field | Description |
|-------|-------------|
| `high` / `medium` / `low` | Bucketed result arrays |
| `total_items`, `total_pages`, `page_number`, `page_size`, `items_on_page` | Pagination metadata |
| `level_info` | Per-bucket page ranges |
| `search_id`, `search_job_id`, `poll_url` | Job identifiers for pagination and re-poll |
| `metadata_filter` | `{applied, planned, text_query}` — echoes the filter AST that actually ran (planner degrades gracefully; a dropped clause is absent from `applied`, and its wording goes back into `text_query`). `null`/absent when no metadata was in play. |
| `scores`, `score_histogram` | Only when requested via `include_scores` / `score_bins` |

---

## 11. Data Plates

Prefix: `/api/v2/data-plates`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/data-plates/list` | Yes | List plates in a collection |
| POST | `/api/v2/data-plates/get` | Yes | Get plate with paginated segments (supports `filters`) |
| POST | `/api/v2/data-plates/create` | Yes | Create plate from search job (async, 202) |
| POST | `/api/v2/data-plates/create-from-collection` | Yes | Create plate from all indexed segments (async) |
| GET | `/api/v2/data-plates/jobs/{job_id}` | Yes | Poll plate creation job |
| POST | `/api/v2/data-plates/update` | Yes | Update plate name/metadata |
| POST | `/api/v2/data-plates/delete` | Yes | Delete plate + all extracted data |
| POST | `/api/v2/data-plates/verify` | Yes | Relevance-verify a plate (async, 202) — trims segments whose similarity to the plate's `user_query` falls below the cutoff; no knowledge columns created. Poll `GET /knowledge-extraction/jobs/{job_id}`. |
| POST | `/api/v2/data-plates/segments/add` | Yes | Add segments to plate |
| POST | `/api/v2/data-plates/segments/remove` | Yes | Remove segments from plate |
| POST | `/api/v2/data-plates/segments/update-extracted-info` | Yes | Update a single extracted info field |
| POST | `/api/v2/data-plates/segments/update-extracted-info-multiple` | Yes | Update multiple fields at once |
| POST | `/api/v2/data-plates/segments/locate` | Yes | Find which page a segment is on |
| POST | `/api/v2/data-plates/columns/list` | Yes | List extracted columns |
| POST | `/api/v2/data-plates/columns/remove` | Yes | Remove a column from all segments |
| POST | `/api/v2/data-plates/generate-csv` | Yes | Generate + upload CSV to S3 |
| GET | `/api/v2/data-plates/export-csv/{collection_id}/{plate_id}` | Yes | Stream-download CSV |

---

## 12. Sub-Plates

Prefix: `/api/v2/data-plates/sub-plates`

| Method | Path (suffix) | Auth | Description |
|--------|--------------|------|-------------|
| POST | `.../create` | Yes | Create sub-plate (with optional filter) |
| POST | `.../list` | Yes | List direct child sub-plates of a parent |
| POST | `.../hierarchy` | Yes | Get full hierarchy tree |
| POST | `.../delete` | Yes | Delete sub-plate (cascades to children) |
| POST | `.../update` | Yes | Add/remove segments or columns from a verification sub-plate |
| POST | `.../verify` | Yes | Mark a segment as verified or flagged |
| POST | `.../verification-progress` | Yes | Get verification progress summary |
| POST | `.../destructive-warning` | Yes | Check if sub-plate has verified segments before destructive action |
| POST | `.../create-auto` | Yes | Atomically create parent task, sub-plates, and child tasks |

---

## 13. Knowledge Extraction

Prefix: `/api/v2/knowledge-extraction`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/knowledge-extraction/columns/add` | Yes | Add extraction columns (questions) to plate (202) |
| POST | `/api/v2/knowledge-extraction/columns/estimate-cost` | Yes | Estimate credit cost of adding columns before running the job |
| POST | `/api/v2/knowledge-extraction/columns/list` | Yes | List extracted columns in plate |
| POST | `/api/v2/knowledge-extraction/columns/remove` | Yes | Remove extraction column from all segments |
| GET | `/api/v2/knowledge-extraction/jobs/{job_id}` | Yes | Poll extraction job status |
| POST | `/api/v2/knowledge-extraction/chat/upload-images` | Yes | Get presigned URLs for chat image attachments |
| POST | `/api/v2/knowledge-extraction/chat/query` | Yes | Query plate data with AI synthesis |
| POST | `/api/v2/knowledge-extraction/charts/plate` | Yes | Get auto-generated charts for a plate |
| POST | `/api/v2/knowledge-extraction/charts/collection` | Yes | Get charts across all plates in collection |

---

## 14. Chat (Data Plate Sessions)

Prefix: `/api/v2/chat`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/chat/sessions/get` | Yes | Get session with full message history |
| POST | `/api/v2/chat/sessions/list` | Yes | List sessions for a plate |
| DELETE | `/api/v2/chat/sessions/{session_id}` | Yes | Delete session |
| POST | `/api/v2/chat/sessions/update-title` | Yes | Update session title |
| POST | `/api/v2/chat/history` | Yes | Get paginated message history |

---

## 15. Agentic Chat

Prefix: `/api/v2/agentic-chat`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/agentic-chat/sessions` | Yes | Create agentic session (201) |
| GET | `/api/v2/agentic-chat/sessions` | Yes | List sessions (filter by `collection_id`) |
| GET | `/api/v2/agentic-chat/sessions/{session_id}` | Yes | Get session |
| DELETE | `/api/v2/agentic-chat/sessions/{session_id}` | Yes | Delete session |
| GET | `/api/v2/agentic-chat/sessions/{session_id}/messages` | Yes | Get full message history + session state |
| POST | `/api/v2/agentic-chat/sessions/{session_id}/chat` | Yes | **SSE streaming** — send message, stream events |
| POST | `/api/v2/agentic-chat/sessions/{session_id}/search-feedback` | Yes | Respond to `search_feedback_required` interrupt |
| POST | `/api/v2/agentic-chat/sessions/{session_id}/stop` | Yes | Stop agent at current step |
| POST | `/api/v2/agentic-chat/sessions/{session_id}/resume` | Yes | Resume agent after interrupt |
| GET | `/api/v2/agentic-chat/sessions/{session_id}/stream` | Yes | Subscribe to running agent SSE stream (GET) |
| POST | `/api/v2/agentic-chat/structured-query` | Yes | Submit a one-shot structured-output query against a collection (async, 202) — no session, no history; returns a `job_id` |
| GET | `/api/v2/agentic-chat/structured-query/{job_id}` | Yes | Poll a structured-query job — `submitted` → `in_progress` → `completed` / `failed`, then the parsed JSON result |

**SSE chat headers required:** `Accept: text/event-stream`, `Content-Type: application/json`

---

## 16. Jobs

Prefix: `/api/v2/jobs`

A unified endpoint to cancel any running async job by removing its pending messages from the processing queue.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/jobs/cancel` | Yes | Cancel a running indexing, KE, or live-stream job |

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `job_type` | string | Yes | `"indexing-chunk"`, `"indexing-qwen"`, `"indexing-youtube"`, `"knowledge-extraction"`, or `"live-stream"` |
| `job_id` | string | Yes | The job identifier (e.g. `idx_xxx`, `ke_job_xxx`) |

**Response `data`:**

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string | The cancelled job ID |
| `job_type` | string | The job type that was cancelled |
| `status` | string | Always `"cancelled"` |
| `messages_removed` | int | Number of pending queue messages purged |

**Errors:** `400` unknown `job_type` · `403` caller does not own the job · `404` job not found

> Cancellation is queue-based — pending work is purged. Work already in-flight may still complete. For indexing, credits are only charged for chunks that were fully processed before cancellation.

---

## 17. Collection Sharing & RBAC

Prefix: `/api/v2/sharing`

### Invitations

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/sharing/invite` | Yes (admin) | Invite member by email |
| POST | `/api/v2/sharing/invitations/accept` | Yes | Accept invitation |
| POST | `/api/v2/sharing/invitations/decline` | Yes | Decline invitation |
| POST | `/api/v2/sharing/invitations/cancel` | Yes (admin) | Cancel / rescind invitation |
| GET | `/api/v2/sharing/invitations` | Yes | List received invitations |
| GET | `/api/v2/sharing/invitations/sent` | Yes | List sent invitations |

### Members

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/sharing/members` | Yes | List accepted members |
| POST | `/api/v2/sharing/members/history` | Yes (admin) | Invitation audit trail |
| POST | `/api/v2/sharing/members/user-history` | Yes (admin) | Status changes for a user |
| POST | `/api/v2/sharing/members/update` | Yes (admin) | Update role / plate access |
| POST | `/api/v2/sharing/members/remove` | Yes (admin) | Remove member |
| POST | `/api/v2/sharing/transfer-ownership` | Yes (admin) | Transfer collection ownership |
| POST | `/api/v2/sharing/leave` | Yes (non-admin) | Leave shared collection |

### Groups

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/sharing/groups/create` | Yes (admin) | Create group label |
| POST | `/api/v2/sharing/groups/list` | Yes | List groups |
| POST | `/api/v2/sharing/groups/delete` | Yes (admin) | Delete group |
| POST | `/api/v2/sharing/groups/rename` | Yes (admin) | Rename group |
| POST | `/api/v2/sharing/members/assign-groups` | Yes | Assign groups to member |
| POST | `/api/v2/sharing/members/bulk-assign-group` | Yes (admin) | Bulk-assign group to multiple members |
| POST | `/api/v2/sharing/members/remove-groups` | Yes | Remove groups from member |
| POST | `/api/v2/sharing/members/by-group` | Yes | List members by group |
| POST | `/api/v2/sharing/groups/members` | Yes | Alias of `members/by-group` — list members in a group |

### Device Tokens (FCM Push Notifications)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/sharing/device-token` | Yes | Register FCM device token |
| DELETE | `/api/v2/sharing/device-token` | Yes | Unregister FCM device token |

---

## 18. Collection Tasks

Prefix: `/api/v2/tasks`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/tasks/create` | Yes (admin) | Create task; assigned users must be collection members |
| POST | `/api/v2/tasks/update` | Yes (admin) | Update task metadata |
| POST | `/api/v2/tasks/cancel` | Yes (admin) | Cancel / soft-delete task |
| POST | `/api/v2/tasks/delete` | Yes (admin) | Permanently delete task (irreversible) |
| POST | `/api/v2/tasks/update-status` | Yes | Update task status (allowed transitions) |
| POST | `/api/v2/tasks/update-progress` | Yes | Update progress 0–100 |
| POST | `/api/v2/tasks/add-comment` | Yes | Add comment (any assigned member) |
| POST | `/api/v2/tasks/list` | Yes | List tasks (admin sees all; members see assigned) |
| POST | `/api/v2/tasks/get` | Yes | Get task + recent activity |
| POST | `/api/v2/tasks/activity` | Yes | Full activity/comment log |
| POST | `/api/v2/tasks/my-tasks` | Yes | Tasks assigned to the calling user |
| POST | `/api/v2/tasks/auto-distribute` | Yes (admin) | Auto-distribute verification task across members |

---

## 19. Live Stream

Prefix: `/api/v2/live-stream`

### Sessions

Models: `model: "video_only"` (default, video frames + subtitles) or `model: "multimodal"` (unified video + image).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/live-stream/sessions` | Yes | Create session (starts in `waiting` state); use stream endpoints to create session + start stream in one call |
| GET | `/api/v2/live-stream/sessions` | Yes | List sessions; optional `?collection_id=` filter |
| GET | `/api/v2/live-stream/sessions/{session_id}` | Yes | Full session details: status, WHIP/WHEP URLs, plate ID, last 50 segments |
| POST | `/api/v2/live-stream/sessions/{session_id}/stop` | Yes | Stop active session; collection and plate are preserved |
| POST | `/api/v2/live-stream/sessions/{session_id}/resume` | Yes | Resume `paused`/`stopped`/`waiting` session; generates fresh MediaMTX path |
| DELETE | `/api/v2/live-stream/sessions/{session_id}` | Yes | Permanently delete session (irreversible; collection not deleted) |
| POST | `/api/v2/live-stream/sessions/{session_id}/add-questions` | Yes | Add live analysis questions; `backfill: true` retroactively processes past segments |
| GET | `/api/v2/live-stream/sessions/{session_id}/indexing-jobs` | Yes | Indexing status: segment count, last job ID, periodic schedule |
| GET | `/api/v2/live-stream/sessions/{session_id}/worker-status` | Yes | Qwen GPU worker readiness; poll every 10s; `estimated_wait` ~3–5 min cold start |
| GET | `/api/v2/live-stream/sessions/{session_id}/mediamtx-status` | Yes | **Primary readiness endpoint** — `all_ready: true` when both workers up and URLs active |

### Protocol-Specific Streams

All endpoints accept: `collection_name` or `collection_id`, `name`, `user_query`, `model`, `periodic_indexing`, `source_url`, `max_fps` (1–60, default 30), `session_id`, `cookies` (YouTube only).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/live-stream/stream` | Yes | Auto-detect protocol from `source_url`; defaults to RTMP push if no URL provided |
| POST | `/api/v2/live-stream/stream/rtmp` | Yes | RTMP push — OBS, encoders, ffmpeg; returns `publish_url` |
| POST | `/api/v2/live-stream/stream/rtsp` | Yes | RTSP pull — IP cameras, NVRs; HTTP/MJPEG auto-bridged via ffmpeg |
| POST | `/api/v2/live-stream/stream/srt` | Yes | SRT pull/push — low-latency or satellite links |
| POST | `/api/v2/live-stream/stream/hls` | Yes | HLS / HTTP sources — phones (DroidCam), existing HLS streams, MJPEG |
| POST | `/api/v2/live-stream/stream/webrtc` | Yes | WebRTC WHIP — browser webcam; returns `whip_url` + `whep_url` |
| POST | `/api/v2/live-stream/stream/youtube` | Yes | YouTube Live/VOD/Shorts — resolved via yt-dlp; `source_url` required |

### MediaMTX Management

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/live-stream/mediamtx/health` | No | Liveness check — HTTP 503 if unreachable |
| GET | `/api/v2/live-stream/mediamtx/config` | Yes | Active MediaMTX endpoint URLs (API, RTMP, RTSP, SRT, WebRTC, HLS ports) |
| GET | `/api/v2/live-stream/mediamtx/streams` | Yes | All active paths with mapped session IDs |
| GET | `/api/v2/live-stream/mediamtx/streams/{path}` | Yes | Status of a specific path (e.g. `live/sess_abc123`) |
| GET | `/api/v2/live-stream/mediamtx/connections/{protocol}` | Yes | Active connections for `rtsp`/`rtmp`/`srt`/`hls`/`webrtc` |
| GET | `/api/v2/live-stream/mediamtx/connections/summary` | Yes | Per-protocol connection counts + total |

### WebRTC Signaling Proxy

> Auth via `?token=YOUR_API_KEY` query parameter — browsers cannot set custom headers during WebRTC signaling. The `whip_url` / `whep_url` returned by session endpoints already include the token.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST, OPTIONS | `/api/v2/live-stream/sessions/{session_id}/whip` | Token | WHIP: send SDP offer, receive answer + Location header |
| PATCH, DELETE, OPTIONS | `/api/v2/live-stream/sessions/{session_id}/whip/{resource_id}` | Token | WHIP: trickle ICE candidates / teardown publish |
| POST, OPTIONS | `/api/v2/live-stream/sessions/{session_id}/whep` | Token | WHEP: send SDP offer, receive answer + Location header |
| PATCH, DELETE, OPTIONS | `/api/v2/live-stream/sessions/{session_id}/whep/{resource_id}` | Token | WHEP: trickle ICE candidates / teardown viewer |

### Internal Webhooks

> Called by internal infrastructure only — do not invoke from external clients.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/live-stream/internal/stream-ready` | Internal | MediaMTX `runOnReady` — session → `streaming` |
| POST | `/api/v2/live-stream/internal/stream-not-ready` | Internal | MediaMTX `runOnNotReady` — session → `paused` |
| POST | `/api/v2/live-stream/internal/segment-recorded` | Internal | 16s segment uploaded to S3 — download, index, queue KE |
| POST | `/api/v2/live-stream/internal/live-plate-updated` | Internal | Qwen worker wrote new KE answers to Live Data Plate |

---

## 20. Online Search

Prefix: `/api/v2/online-search`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/online-search/search` | Yes | Start a server-side YouTube search job (async) |
| GET | `/api/v2/online-search/{job_id}/status` | Yes | Poll job status |
| GET | `/api/v2/online-search/{job_id}/candidates` | Yes | List candidate videos |
| DELETE | `/api/v2/online-search/{job_id}/candidates/{video_id}` | Yes | Remove a candidate |
| POST | `/api/v2/online-search/{job_id}/search-more` | Yes | Run additional queries for the same job |
| POST | `/api/v2/online-search/{job_id}/confirm` | Yes | Confirm candidates and start indexing |

---

## 21. YouTube Search

> **Use `/api/v2/yt-search-v2/`** — this is the latest version. V1 (`/api/v2/yt-search/`) is legacy.

Prefix: `/api/v2/yt-search-v2`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/yt-search-v2/refine-query` | Yes | Step 1: Refine user query into optimized YouTube search terms |
| POST | `/api/v2/yt-search-v2/{job_id}/submit-results` | Yes | Step 2: Submit results from browser extension |
| GET | `/api/v2/yt-search-v2/{job_id}/status` | Yes | Poll job status |
| GET | `/api/v2/yt-search-v2/{job_id}/candidates` | Yes | List candidate YouTube videos |
| DELETE | `/api/v2/yt-search-v2/{job_id}/candidates/{video_id}` | Yes | Remove a candidate |
| POST | `/api/v2/yt-search-v2/{job_id}/trim` | Yes | Keep only specified candidate IDs |
| POST | `/api/v2/yt-search-v2/{job_id}/search-more` | Yes | Run additional refinement |
| POST | `/api/v2/yt-search-v2/{job_id}/confirm` | Yes | Confirm all candidates and trigger indexing |
| POST | `/api/v2/yt-search-v2/{job_id}/confirm-selected` | Yes | Index only selected video URLs |

---

## 22. Transactions

Prefix: `/api/v2/transactions`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/transactions` | Yes | Paginated transaction history |
| GET | `/api/v2/transactions/summary` | Yes | Credit balance, totals, storage |
| GET | `/api/v2/transactions/breakdown` | Yes | Usage by feature category |
| GET | `/api/v2/transactions/breakdown/collections` | Yes | Usage by collection |
| GET | `/api/v2/transactions/breakdown/plates` | Yes | Usage by data plate |
| GET | `/api/v2/transactions/breakdown/sessions` | Yes | Usage by agentic chat session |
| GET | `/api/v2/transactions/categories` | Yes | Valid filter categories |
| GET | `/api/v2/transactions/timeline` | Yes | Credit usage over time (for charts) |
| GET | `/api/v2/transactions/export` | Yes | Export as CSV download |

---

## 23. Users

Prefix: `/api/v2/users`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/users/me` | Yes | Get current user ID |
| GET | `/api/v2/users/me/uploaded-hours` | Yes | Total uploaded hours + storage |
| GET | `/api/v2/users/me/info` | Yes | Credits, hours, search requests |
| GET | `/api/v2/users/get_users_info` | Yes | Get account info (active alias used by the web app) |
| GET | `/api/v2/users/api-key-check` | Yes | Confirm the caller's API key is active |
| GET | `/api/v2/users/api-key-check/{user_id_param}` | Yes | Admin: check whether a given user has an active API key |
| POST | `/api/v2/users/credits/claim-welcome` | Yes | Claim one-time welcome credits |
| POST | `/api/v2/users/credits/validate-indexing` | Yes | Check credit sufficiency for indexing |
| POST | `/api/v2/users/credits/validate-video-qa` | Yes | Check credit sufficiency for video QA |
| POST | `/api/v2/users/credits/consume-video-qa` | Yes | Consume credits for video QA |
| POST | `/api/v2/users/credits/consume-indexing` | Yes | Consume credits for indexing |

---

## 24. Payments

Prefix: `/api/v2/payments`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/payments/checkout` | Yes | Create a one-off payment checkout session |
| POST | `/api/v2/payments/stripe-webhook` | No (Stripe sig) | Stripe event webhook (called by Stripe, not clients) |
| GET | `/api/v2/payments/status/{payment_id}` | No | Get payment status |
| GET | `/api/v2/payments/verify/{payment_id}` | Yes | Verify payment + confirm credits added |

---

## 25. Subscriptions

Prefix: `/api/v2/subscriptions`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/subscriptions/plans` | No | List all subscription plans (public) |
| GET | `/api/v2/subscriptions/pricing` | No | Pricing info and KE token rates (public) |
| GET | `/api/v2/subscriptions/me` | Yes | Current subscription details |
| GET | `/api/v2/subscriptions/features` | Yes | Feature flags/limits for user's tier |
| GET | `/api/v2/subscriptions/features/all` | No | Feature matrix for all tiers (public) |
| GET | `/api/v2/subscriptions/storage-usage` | Yes | Storage usage + projected cost |
| POST | `/api/v2/subscriptions/checkout` | Yes | Create Stripe checkout session |
| POST | `/api/v2/subscriptions/portal` | Yes | Open Stripe customer portal |
| POST | `/api/v2/subscriptions/cancel` | Yes | Cancel at end of billing period |
| GET | `/api/v2/subscriptions/billing/overdue-status` | Yes | Storage overdue status |

### Admin-only

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/subscriptions/admin/set-tier` | Admin | Force a user onto a specific tier |
| POST | `/api/v2/subscriptions/admin/enterprise` | Admin | Provision an enterprise subscription |
| POST | `/api/v2/subscriptions/admin/reset-free-tier` | Admin | Reset a user back to the free tier |
| POST | `/api/v2/subscriptions/admin/bill-storage` | Admin | Charge overdue storage fees for a user |
| POST | `/api/v2/subscriptions/admin/process-storage-overdue` | Admin | Sweep-and-charge job for all overdue-storage accounts |

---

## 26. Invoices

Prefix: `/api/v2/invoices`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/invoices` | Yes | List invoices |
| GET | `/api/v2/invoices/{invoice_id}` | Yes | Get invoice details |
| GET | `/api/v2/invoices/{invoice_id}/download` | Yes | Download invoice PDF |

---

## 27. Admin Dashboard

> These endpoints require admin-level access and are not available to regular API keys.

Prefix: `/api/v2/admin/dashboard` · credit override at `/api/v2/admin/credits`

### Overview & user analytics

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/admin/dashboard/overview` | Admin | Top-level dashboard cards — users, revenue, credit consumption, alerts |
| GET | `/api/v2/admin/dashboard/users/count` | Admin | Total user count |
| GET | `/api/v2/admin/dashboard/users/new` | Admin | New users within date range |
| GET | `/api/v2/admin/dashboard/users/analytics` | Admin | Paginated user analytics |
| GET | `/api/v2/admin/dashboard/users/activity/segments` | Admin | Active / dormant / churned user segments |
| GET | `/api/v2/admin/dashboard/users/activity/recent-signups` | Admin | Latest sign-ups with first-day engagement |
| GET | `/api/v2/admin/dashboard/users/activity/signup-trend` | Admin | Sign-up trend over time |
| GET | `/api/v2/admin/dashboard/users/activity/retention` | Admin | Cohort retention matrix |

### Platform usage stats

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/admin/dashboard/stats/plates` | Admin | Data plate count |
| GET | `/api/v2/admin/dashboard/stats/collections` | Admin | Collection count |
| GET | `/api/v2/admin/dashboard/stats/credits-used` | Admin | Total credits used |
| GET | `/api/v2/admin/dashboard/stats/recent-plates` | Admin | Recently created plates |
| GET | `/api/v2/admin/dashboard/stats/recent-collections` | Admin | Recently created collections |

### Revenue

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/admin/dashboard/revenue/summary` | Admin | Aggregate revenue summary |
| GET | `/api/v2/admin/dashboard/revenue/trend` | Admin | Revenue trend over time |
| GET | `/api/v2/admin/dashboard/revenue/monthly` | Admin | Monthly revenue breakdown |
| GET | `/api/v2/admin/dashboard/revenue/top-customers` | Admin | Highest-revenue customers |
| GET | `/api/v2/admin/dashboard/revenue/subscriptions` | Admin | Revenue by subscription tier |

### Credit consumption

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/admin/dashboard/credits/top-consumers` | Admin | Users consuming the most credits |
| GET | `/api/v2/admin/dashboard/credits/fast-burn` | Admin | Users burning credits abnormally fast |
| GET | `/api/v2/admin/dashboard/credits/trend` | Admin | Credit consumption trend over time |
| GET | `/api/v2/admin/dashboard/credits/by-operation` | Admin | Credits consumed grouped by operation type |

### Cloud costs & billing

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/admin/dashboard/cloud-costs/daily` | Admin | Combined AWS + GCP daily costs |
| GET | `/api/v2/admin/dashboard/cloud-costs/monthly` | Admin | Combined AWS + GCP monthly costs |
| GET | `/api/v2/admin/dashboard/billing/aws/daily` | Admin | AWS daily billing |
| GET | `/api/v2/admin/dashboard/billing/aws/monthly` | Admin | AWS monthly billing |
| GET | `/api/v2/admin/dashboard/billing/gcp/monthly` | Admin | GCP monthly billing |
| GET | `/api/v2/admin/dashboard/billing/gcp/monthly/detailed` | Admin | GCP monthly billing by SKU |

### Credit override

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/admin/credits/set` | Admin (staging) | Force a user's credit balance to a specific value — available on staging only, used for QA scenarios |

---

## 28. Help Menu

Prefix: `/api/v2/help`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/help` | Yes | Submit help / feedback request (multipart/form-data) |
| GET | `/api/v2/help` | Admin | Retrieve paginated help requests |

---

## 29. Authentication & API Keys

Auth endpoints back the web dashboard's sign-up / sign-in flow. They accept a Firebase-style bearer token from the configured identity provider (Firebase or Keycloak); they do **not** accept API keys. API-key management lives here too, and is what the dashboard uses to mint and rotate keys for API callers.

Prefix: `/api/v2/auth` and `/api/v2/api-keys`

### Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/auth/signup` | No | Register a new user via the identity provider |
| POST | `/api/v2/auth/login` | No | Exchange email + password for provider tokens |
| POST | `/api/v2/auth/google` | No | Complete a Google-OAuth login handoff |

### API Keys (dashboard, Firebase-bearer)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/api-keys` | Bearer (Firebase) | Return the caller's current API key (or `null`); never creates |
| POST | `/api/v2/api-keys` | Bearer (Firebase) | Return an existing key or provision one on first call |
| POST | `/api/v2/api-keys/regenerate` | Bearer (Firebase) | Rotate the caller's API key \u2014 the old key stops working immediately |

> **API-key lifecycle checks** live on `/api/v2/users` \u2014 `GET /users/api-key-check` and `GET /users/api-key-check/{user_id_param}`.

---

## 30. License

Deployment-level entitlements. Non-raising: an expired or invalid license reports features as `false` rather than returning a `500`, so admin UI can degrade gracefully.

Prefix: `/api/v2/license`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/license/features` | No | `{category: bool}` map for every gateable API category |
| GET | `/api/v2/license/status` | No | Deployment license status \u2014 `valid`, `expires_at`, tier, remaining seats |

---

## 31. Files

Prefix: `/api/v2/files`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/files/presigned-get` | Yes | 302-redirect to a presigned GET URL for a stored chat-image media handle (`med_...`). Refuses any key that is not under the caller's own `chat_images/` prefix. |

---

## 32. Upload Integrations

Third-party media transfers. Each `transfer` returns `202` with a job that resolves once the backend has pulled the files into the target collection. See [guides/upload-integrations.md](../guides/upload-integrations.md) for OAuth setup per provider.

Prefix: `/api/v2/upload`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/upload/google-drive/files` | Yes | List Drive files the caller can transfer (uses Google OAuth access token) |
| POST | `/api/v2/upload/google-drive/transfer` | Yes | Transfer selected Drive files into a collection (async, 202) |
| GET | `/api/v2/upload/dropbox/files` | Yes | List Dropbox files the caller can transfer |
| POST | `/api/v2/upload/dropbox/transfer` | Yes | Transfer selected Dropbox files into a collection (async, 202) |
| POST | `/api/v2/upload/huggingface/transfer` | Yes | Transfer a Hugging Face dataset\u00a0/\u00a0repo into a collection (async, 202) |

---

## 33. Miscellaneous

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/speed-comparison-reports/index` | No | List speed comparison report JSON files |
