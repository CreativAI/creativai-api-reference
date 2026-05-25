# CreativAI API — Complete Endpoint Registry

> Last updated: 2026-05-26  
> This document is published as integration reference and intentionally excludes backend implementation details.  
> **Version policy:** When an endpoint exists in both v2 and v3, only the **latest version (v3)** is shown. Use the version listed here for all new integrations.  
> **Base URL:** `https://creativai-apis.com`  
> **Auth:** `X-API-Key: <KEY>` or `Authorization: Bearer <KEY>`  
> **Response envelope:** `{"success": bool, "data": <payload>, "error": {"code": "...", "message": "...", "details": {}, "timestamp": "..."}}`

---

## Summary

| Module | # Endpoints | Notes |
|--------|-------------|-------|
| Health | 3 | No auth |
| Organizations | 4 | |
| Projects | 4 | |
| Collections | 8 | |
| Media / Videos | 4 | |
| Multipart Uploads | 4 | |
| S3 Transfers | 3 | |
| Indexing | 6 | Async (202) |
| Search | 1 | |
| Data Plates | 16 | v2 routes |
| Sub-Plates | 9 | **v3** (latest) |
| Knowledge Extraction | 8 | **v3** (latest) |
| Chat (Plate Sessions) | 5 | |
| Agentic Chat | 12 | SSE streaming |
| Collection Sharing & RBAC | 25 | |
| Collection Tasks | 12 | |
| Live Stream — Sessions | 10 | |
| Live Stream — Protocol Streams | 7 | |
| Live Stream — MediaMTX | 6 | |
| Live Stream — Internal Webhooks | 4 | Internal only |
| Live Stream — WebRTC Proxy | 4 | `?token=` auth |
| Online Search | 6 | Async |
| YouTube Search | 9 | **v2** (latest) |
| Transactions | 9 | |
| Users | 11 | |
| Payments | 3 | |
| Subscriptions | 14 | |
| Invoices | 3 | |
| Admin Dashboard | 12 | Admin only |
| **Total** | **~235** | |

---

## 1. Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | API root / version info |
| GET | `/health` | No | Health check for load balancers |
| GET | `/health/simple` | No | Minimal ALB liveness probe |

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
| POST | `/api/v2/collections` | Yes | Create collection (`model`: `"default"` or `"qwen"`) |
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
| GET | `/api/v2/collections/{collection_id}/media` | Yes | List all media with preprocessing status |
| DELETE | `/api/v2/collections/{collection_id}/media` | Yes | Remove specific media files |
| POST | `/api/v2/collections/{collection_id}/upload-url` | Yes | Get presigned S3 URL (single file) |
| POST | `/api/v2/collections/{collection_id}/upload-urls` | Yes | Get presigned URLs (batch) |

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

**Key indexing body params:** `collection_id` (required), `media_s3_uris` (optional list), `tags` (optional map of S3 URI → string list, `"*"` for all)

---

## 9. Search

Prefix: `/api/v2/search`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/search` | Yes | Semantic search (hybrid / vision / audio) |

**Request body params:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `collection_id` | string | Yes | |
| `text_query` | string | Yes | Natural language search query |
| `search_type` | string | No | `"hybrid"` (default), `"vision"`, `"audio"` |
| `page_number` | int | No | 1-indexed (default: 1) |
| `page_size` | int | No | Results per page (default: 100, max ~500) |
| `search_id` | string | No | Reuse previous search for pagination |
| `video_urls` | list[string] | No | Restrict to specific S3 URIs |
| `refine_query` | bool | No | LLM rewrites query for better recall |
| `image_base64` | string | No | Base64 image for visual query (Qwen only) |
| `image_key` | string | No | S3 key of uploaded image (Qwen only, preferred) |

---

## 10. Data Plates

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

## 11. Sub-Plates

> **Use `/api/v3/data-plates/sub-plates/...`** — v3 is the current and recommended version.

Prefix: `/api/v3/data-plates/sub-plates`

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

## 12. Knowledge Extraction

> **Use `/api/v3/knowledge-extraction/...`** — v3 is the current and recommended version.

Prefix: `/api/v3/knowledge-extraction`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v3/knowledge-extraction/columns/add` | Yes | Add extraction columns (questions) to plate (202) |
| POST | `/api/v3/knowledge-extraction/columns/list` | Yes | List extracted columns in plate |
| POST | `/api/v3/knowledge-extraction/columns/remove` | Yes | Remove extraction column from all segments |
| GET | `/api/v3/knowledge-extraction/jobs/{job_id}` | Yes | Poll extraction job status |
| POST | `/api/v3/knowledge-extraction/chat/upload-images` | Yes | Get presigned URLs for chat image attachments |
| POST | `/api/v3/knowledge-extraction/chat/query` | Yes | Query plate data with AI synthesis |
| POST | `/api/v3/knowledge-extraction/charts/plate` | Yes | Get auto-generated charts for a plate |
| POST | `/api/v3/knowledge-extraction/charts/collection` | Yes | Get charts across all plates in collection |

---

## 13. Chat (Data Plate Sessions)

Prefix: `/api/v2/chat`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/chat/sessions/get` | Yes | Get session with full message history |
| POST | `/api/v2/chat/sessions/list` | Yes | List sessions for a plate |
| DELETE | `/api/v2/chat/sessions/{session_id}` | Yes | Delete session |
| POST | `/api/v2/chat/sessions/update-title` | Yes | Update session title |
| POST | `/api/v2/chat/history` | Yes | Get paginated message history |

---

## 14. Agentic Chat

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
| GET | `/api/v2/agentic-chat/sessions/{session_id}/events` | Yes | Poll new agent events since last call |
| GET | `/api/v2/agentic-chat/sessions/{session_id}/stream` | Yes | Subscribe to running agent SSE stream (GET) |
| GET | `/api/v2/agentic-chat/sessions/{session_id}/status` | Yes | Check current agent status |

**SSE chat headers required:** `Accept: text/event-stream`, `Content-Type: application/json`

---

## 15. Collection Sharing & RBAC

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

### Device Tokens (FCM Push Notifications)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/sharing/device-token` | Yes | Register FCM device token |
| DELETE | `/api/v2/sharing/device-token` | Yes | Unregister FCM device token |

---

## 16. Collection Tasks

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

## 17. Live Stream

Prefix: `/api/v2/live-stream`

### Sessions

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/live-stream/sessions` | Yes | Create session (starts in `WAITING` state) |
| GET | `/api/v2/live-stream/sessions` | Yes | List sessions |
| GET | `/api/v2/live-stream/sessions/{session_id}` | Yes | Get session details + WHIP/WHEP URLs |
| POST | `/api/v2/live-stream/sessions/{session_id}/stop` | Yes | Stop active session |
| POST | `/api/v2/live-stream/sessions/{session_id}/resume` | Yes | Resume paused/stopped session |
| DELETE | `/api/v2/live-stream/sessions/{session_id}` | Yes | Delete session permanently |
| POST | `/api/v2/live-stream/sessions/{session_id}/add-questions` | Yes | Add/update live analysis questions |
| GET | `/api/v2/live-stream/sessions/{session_id}/indexing-jobs` | Yes | Get current indexing status |
| GET | `/api/v2/live-stream/sessions/{session_id}/worker-status` | Yes | Poll Qwen worker readiness |
| GET | `/api/v2/live-stream/sessions/{session_id}/mediamtx-status` | Yes | Poll MediaMTX readiness |

### Protocol-Specific Streams

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/live-stream/stream` | Yes | Auto-detect protocol and start stream |
| POST | `/api/v2/live-stream/stream/rtmp` | Yes | RTMP (OBS, encoders) — returns `rtmp_url` for push |
| POST | `/api/v2/live-stream/stream/rtsp` | Yes | RTSP (IP cameras, NVRs) |
| POST | `/api/v2/live-stream/stream/srt` | Yes | SRT (low latency, satellite links) |
| POST | `/api/v2/live-stream/stream/hls` | Yes | HLS / HTTP sources (phones, DroidCam, MJPEG) |
| POST | `/api/v2/live-stream/stream/webrtc` | Yes | WebRTC (WHIP) via browser |
| POST | `/api/v2/live-stream/stream/youtube` | Yes | YouTube Live URL |

### MediaMTX Management

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/live-stream/mediamtx/health` | No | Check MediaMTX sidecar reachability |
| GET | `/api/v2/live-stream/mediamtx/config` | Yes | Get MediaMTX endpoint configuration |
| GET | `/api/v2/live-stream/mediamtx/streams` | Yes | List active streams with session mappings |
| GET | `/api/v2/live-stream/mediamtx/streams/{path}` | Yes | Get status of a specific stream path |
| GET | `/api/v2/live-stream/mediamtx/connections/{protocol}` | Yes | List active connections for a protocol |
| GET | `/api/v2/live-stream/mediamtx/connections/summary` | Yes | Aggregated connection counts |

### WebRTC Signaling Proxy

> Auth via `?token=YOUR_API_KEY` query parameter (browser limitation).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST, OPTIONS | `/api/v2/live-stream/sessions/{session_id}/whip` | Token | WHIP publish SDP offer/answer |
| PATCH, DELETE, OPTIONS | `/api/v2/live-stream/sessions/{session_id}/whip/{resource_id}` | Token | WHIP ICE trickle / teardown |
| POST, OPTIONS | `/api/v2/live-stream/sessions/{session_id}/whep` | Token | WHEP playback SDP offer/answer |
| PATCH, DELETE, OPTIONS | `/api/v2/live-stream/sessions/{session_id}/whep/{resource_id}` | Token | WHEP ICE trickle / teardown |

### Internal Webhooks

> These are called by internal infrastructure, not external clients.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/live-stream/internal/live-plate-updated` | Internal | Live Qwen worker notifies new extracted_info |
| POST | `/api/v2/live-stream/internal/segment-recorded` | Internal | Segment uploaded to S3 by MediaMTX |
| POST | `/api/v2/live-stream/internal/stream-ready` | Internal | Publisher connected |
| POST | `/api/v2/live-stream/internal/stream-not-ready` | Internal | Publisher disconnected |

---

## 18. Online Search

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

## 19. YouTube Search

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

## 20. Transactions

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

## 21. Users

Prefix: `/api/v2/users`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/users/me` | Yes | Get current user ID |
| GET | `/api/v2/users/me/uploaded-hours` | Yes | Total uploaded hours + storage |
| GET | `/api/v2/users/me/info` | Yes | Credits, hours, search requests |
| GET | `/api/v2/users/api-key-check` | No | Validate API key (no auth required) |
| POST | `/api/v2/users/credits/claim-welcome` | Yes | Claim one-time welcome credits |
| POST | `/api/v2/users/credits/validate-indexing` | Yes | Check credit sufficiency for indexing |

### API Keys

Prefix: `/api/v2/api-keys`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/api-keys` | Yes | List API keys (metadata only; secret never returned) |
| POST | `/api/v2/api-keys` | Yes | Create a new API key |
| DELETE | `/api/v2/api-keys/{key_id}` | Yes | Revoke an API key |

---

## 22. Payments

Prefix: `/api/v2/payments`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/payments/stripe-webhook` | No (Stripe sig) | Stripe event webhook (called by Stripe, not clients) |
| GET | `/api/v2/payments/status/{payment_id}` | No | Get payment status |
| GET | `/api/v2/payments/verify/{payment_id}` | Yes | Verify payment + confirm credits added |

---

## 23. Subscriptions

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

---

## 24. Invoices

Prefix: `/api/v2/invoices`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/invoices` | Yes | List invoices |
| GET | `/api/v2/invoices/{invoice_id}` | Yes | Get invoice details |
| GET | `/api/v2/invoices/{invoice_id}/download` | Yes | Download invoice PDF |

---

## 25. Admin Dashboard

> These endpoints require admin-level access and are not available to regular API keys.

Prefix: `/api/v2/admin/dashboard`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v2/admin/dashboard/users/count` | Admin | Total user count |
| GET | `/api/v2/admin/dashboard/users/new` | Admin | New users within date range |
| GET | `/api/v2/admin/dashboard/users/analytics` | Admin | Paginated user analytics |
| GET | `/api/v2/admin/dashboard/stats/plates` | Admin | Data plate count |
| GET | `/api/v2/admin/dashboard/stats/collections` | Admin | Collection count |
| GET | `/api/v2/admin/dashboard/stats/credits-used` | Admin | Total credits used |
| GET | `/api/v2/admin/dashboard/stats/recent-plates` | Admin | Recently created plates |
| GET | `/api/v2/admin/dashboard/stats/recent-collections` | Admin | Recently created collections |
| GET | `/api/v2/admin/dashboard/billing/aws/daily` | Admin | AWS daily billing |
| GET | `/api/v2/admin/dashboard/billing/aws/monthly` | Admin | AWS monthly billing |
| GET | `/api/v2/admin/dashboard/billing/gcp/monthly` | Admin | GCP monthly billing |
| GET | `/api/v2/admin/dashboard/billing/gcp/monthly/detailed` | Admin | GCP monthly billing by SKU |

---

## 26. Help Menu

Prefix: `/api/v2/help`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v2/help` | Yes | Submit help / feedback request (multipart/form-data) |
| GET | `/api/v2/help` | Admin | Retrieve paginated help requests |

---

## 27. Miscellaneous

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/speed-comparison-reports/index` | No | List speed comparison report JSON files |
