# CreativAI API — Complete Endpoint Registry

> Auto-catalogued from source code. Last updated: 2026-05-25.
> This document is published as integration reference and intentionally excludes backend implementation details.
> Base: All V2 paths are prefixed with `/api/v2/`.
> Auth: Authenticated endpoints require `X-API-Key: <KEY>` or `Authorization: Bearer <KEY>` header.
> Response envelope: `{"success": bool, "data": <payload>, "error": {"code": "...", "message": "...", "details": {}, "timestamp": "..."}}`

---

## Summary

| Module | # Endpoints |
|---|---|
| Health | 3 |
| Organizations | 4 |
| Projects | 4 |
| Collections | 8 |
| Media / Videos | 4 |
| Multipart Uploads | 4 |
| S3 Transfers | 3 |
| Indexing | 6 |
| Search | 1 |
| Data Plates (V2) | 16 |
| Data Plates — Sub-Plates (V2 + V3) | 9 |
| Knowledge Extraction | 9 |
| Chat (Plate Sessions) | 5 |
| Agentic Chat | 12 |
| Collection Sharing & RBAC | 25 |
| Collection Tasks | 12 |
| Live Stream — Sessions | 10 |
| Live Stream — Protocol Streams | 7 |
| Live Stream — MediaMTX | 6 |
| Live Stream — Internal Webhooks | 4 |
| Live Stream — WebRTC Proxy | 4 |
| Online Search | 6 |
| YouTube Search V1 | 10 |
| YouTube Search V2 | 9 |
| Transactions | 9 |
| Users | 11 |
| Payments | 3 |
| Subscriptions | 14 |
| Invoices | 3 |
| Admin Dashboard | 12 |
| Help Menu | 2 |
| Misc (app-level) | 1 |
| **Total** | **~235** |

---

## 1. Health

Defined in `app.py` (top-level) and `api/routes/v2/health.py`.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/` | No | API root / version info |
| GET | `/health` | No | Health check for load balancers (timestamp) |
| GET | `/health/simple` | No | Minimal ALB liveness probe |

---

## 2. Organizations

Prefix: `/api/v2/organizations` — Source: `api/routes/v2/organizations.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/organizations` | Yes | Create organization |
| GET | `/api/v2/organizations` | Yes | List user's organizations |
| GET | `/api/v2/organizations/{org_id}` | Yes | Get organization details |
| DELETE | `/api/v2/organizations/{org_id}` | Yes | Delete organization + all contents |

---

## 3. Projects

Prefix: `/api/v2/organizations/{org_id}/projects` — Source: `api/routes/v2/projects.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/organizations/{org_id}/projects` | Yes | Create project in org |
| GET | `/api/v2/organizations/{org_id}/projects` | Yes | List projects in org |
| GET | `/api/v2/organizations/{org_id}/projects/{project_name}` | Yes | Get project + its collections |
| DELETE | `/api/v2/organizations/{org_id}/projects/{project_name}` | Yes | Delete project + all collections |

---

## 4. Collections

Prefix: `/api/v2/collections` — Source: `api/routes/v2/collections.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/collections` | Yes | Create collection (tier limit enforced, supports `model` selection) |
| GET | `/api/v2/collections` | Yes | List user's collections (pre-computed stats, fast) |
| POST | `/api/v2/collections/by-organization` | Yes | List collections by org |
| POST | `/api/v2/collections/by-project` | Yes | List collections by project |
| GET | `/api/v2/collections/{collection_id}` | Yes | Get collection details including all media files |
| PATCH | `/api/v2/collections/{collection_id}` | Yes | Update collection name / description (admin) |
| DELETE | `/api/v2/collections/{collection_id}` | Yes | Delete collection (admin) |
| POST | `/api/v2/collections/{collection_id}/restore` | Yes | Restore a soft-deleted (suspended) collection |

---

## 5. Media / Videos

Prefix: `/api/v2/collections/{collection_id}` — Source: `api/routes/v2/videos.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v2/collections/{collection_id}/media` | Yes | List all media in collection |
| DELETE | `/api/v2/collections/{collection_id}/media` | Yes | Remove specific media files |
| POST | `/api/v2/collections/{collection_id}/upload-url` | Yes | Get presigned S3 URL (single file) |
| POST | `/api/v2/collections/{collection_id}/upload-urls` | Yes | Get presigned URLs (batch) |

---

## 6. Multipart Uploads

Prefix: `/api/v2/collections/uploads` — Source: `api/routes/v2/videos.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/collections/uploads/initiate` | Yes | Initiate multipart upload |
| POST | `/api/v2/collections/uploads/{upload_id}/complete` | Yes | Complete multipart upload |
| DELETE | `/api/v2/collections/uploads/{upload_id}` | Yes | Abort multipart upload |
| POST | `/api/v2/collections/uploads/{upload_id}/regenerate-urls` | Yes | Regenerate expired part URLs |

---

## 7. S3 Transfers

Prefix: `/api/v2/transfers` — Source: `api/routes/v2/videos.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/transfers` | Yes | Start async transfer from external S3/URLs (202) |
| GET | `/api/v2/transfers/{job_id}` | Yes | Poll transfer job status |
| POST | `/api/v2/transfers/validate` | Yes | Validate source URL accessibility |

---

## 8. Indexing

Prefix: `/api/v2/indexing` — Source: `api/routes/v2/indexing.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/indexing/chunk-based` | Yes | Start chunk-based indexing job (202) |
| GET | `/api/v2/indexing/chunk-based/{indexing_id}/status` | Yes | Poll indexing job status |
| POST | `/api/v2/indexing/chunk-based/estimate-cost` | Yes | Estimate credit cost before indexing |
| GET | `/api/v2/indexing/preprocessing-status/{collection_id}` | Yes | Get preprocessing status for all media |
| GET | `/api/v2/indexing/preprocessed-videos/{collection_id}` | Yes | List media ready for indexing |
| GET | `/api/v2/indexing/video-status` | Yes | Get preprocessing status of a specific video or all videos in a collection |

---

## 9. Search

Prefix: `/api/v2/search` — Source: `api/routes/v2/search.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/search` | Yes | Semantic video/image search (hybrid, vision, audio) |

**Key params**: `collection_id`, `text_query`, `search_type` (hybrid/vision/audio), `page_size`, `search_id` (for pagination), `image_base64` / `image_key` (Qwen collections only), `video_urls` (restrict to specific videos)

---

## 10. Data Plates

### V2 Routes

Prefix: `/api/v2/data-plates` — Source: `api/routes/v2/data_plates.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/data-plates/list` | Yes | List plates in collection |
| POST | `/api/v2/data-plates/get` | Yes | Get plate with paginated segments |
| POST | `/api/v2/data-plates/create` | Yes | Create plate from search job (async, 202) |
| POST | `/api/v2/data-plates/create-from-collection` | Yes | Create plate from all indexed segments (async) |
| GET | `/api/v2/data-plates/jobs/{job_id}` | Yes | Poll plate creation job |
| POST | `/api/v2/data-plates/update` | Yes | Update plate metadata |
| POST | `/api/v2/data-plates/delete` | Yes | Delete plate + all data |
| POST | `/api/v2/data-plates/segments/add` | Yes | Add segments to plate |
| POST | `/api/v2/data-plates/segments/remove` | Yes | Remove segments from plate |
| POST | `/api/v2/data-plates/segments/update-extracted-info` | Yes | Update single extracted info field |
| POST | `/api/v2/data-plates/segments/update-extracted-info-multiple` | Yes | Update multiple fields at once |
| POST | `/api/v2/data-plates/segments/locate` | Yes | Return which page a segment is on within a plate |
| POST | `/api/v2/data-plates/columns/list` | Yes | List extracted columns |
| POST | `/api/v2/data-plates/columns/remove` | Yes | Remove a column from all segments |
| POST | `/api/v2/data-plates/generate-csv` | Yes | Generate + upload CSV to S3 |
| GET | `/api/v2/data-plates/export-csv/{collection_id}/{plate_id}` | Yes | Stream-download CSV |

### Sub-Plates Routes (V2 + V3)

Both `/api/v2/data-plates/sub-plates/...` and `/api/v3/data-plates/sub-plates/...` are mounted (same router).

| Method | Path (suffix) | Auth | Description |
|---|---|---|---|
| POST | `.../sub-plates/create` | Yes | Create sub plate (with optional filter) |
| POST | `.../sub-plates/list` | Yes | List direct child sub plates of a parent |
| POST | `.../sub-plates/hierarchy` | Yes | Get full hierarchy tree |
| POST | `.../sub-plates/delete` | Yes | Delete sub plate (cascades to children) |
| POST | `.../sub-plates/update` | Yes | Add/remove segments or columns from a verification sub-plate |
| POST | `.../sub-plates/verify` | Yes | Mark a segment as verified or flagged |
| POST | `.../sub-plates/verification-progress` | Yes | Get verification progress summary |
| POST | `.../sub-plates/destructive-warning` | Yes | Check if sub-plate has verified segments before destructive action |
| POST | `.../sub-plates/create-auto` | Yes | Atomically create parent verification task, sub-plates, and child tasks |

---

## 11. Knowledge Extraction

Prefix: `/api/v2/knowledge-extraction` (also mounted under `/api/v3/`) — Source: `api/routes/v2/knowledge_extraction.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/knowledge-extraction/columns/add` | Yes | Add extraction columns (questions) to plate (202) |
| POST | `/api/v2/knowledge-extraction/columns/list` | Yes | List extracted columns in plate |
| POST | `/api/v2/knowledge-extraction/columns/remove` | Yes | Remove extraction column |
| GET | `/api/v2/knowledge-extraction/jobs/{job_id}` | Yes | Poll extraction job status |
| POST | `/api/v2/knowledge-extraction/chat/upload-images` | Yes | Get presigned URLs for chat image attachments |
| POST | `/api/v2/knowledge-extraction/chat/query` | Yes | Query plate data with AI synthesis |
| POST | `/api/v2/knowledge-extraction/charts/plate` | Yes | Get auto-generated charts for a plate |
| POST | `/api/v2/knowledge-extraction/charts/collection` | Yes | Get charts across all plates in collection |
| POST | `/api/v2/knowledge-extraction/internal/jobs/{job_id}/trigger-synthesis` | Internal | Trigger synthesis after worker completes |

---

## 12. Chat (Data Plate Sessions)

Prefix: `/api/v2/chat` — Source: `api/routes/v2/chat.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/chat/sessions/get` | Yes | Get session with full message history |
| POST | `/api/v2/chat/sessions/list` | Yes | List sessions for a plate |
| DELETE | `/api/v2/chat/sessions/{session_id}` | Yes | Delete session |
| POST | `/api/v2/chat/sessions/update-title` | Yes | Update session title |
| POST | `/api/v2/chat/history` | Yes | Get paginated message history |

---

## 13. Agentic Chat

Prefix: `/api/v2/agentic-chat` — Source: `api/routes/v2/agentic_chat.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/agentic-chat/sessions` | Yes | Create agentic session (201) |
| GET | `/api/v2/agentic-chat/sessions` | Yes | List sessions |
| GET | `/api/v2/agentic-chat/sessions/{session_id}` | Yes | Get session |
| DELETE | `/api/v2/agentic-chat/sessions/{session_id}` | Yes | Delete session |
| GET | `/api/v2/agentic-chat/sessions/{session_id}/messages` | Yes | Get messages |
| POST | `/api/v2/agentic-chat/sessions/{session_id}/chat` | Yes | SSE streaming chat |
| POST | `/api/v2/agentic-chat/sessions/{session_id}/search-feedback` | Yes | Submit search feedback |
| POST | `/api/v2/agentic-chat/sessions/{session_id}/stop` | Yes | Stop agent at current step |
| POST | `/api/v2/agentic-chat/sessions/{session_id}/resume` | Yes | Resume agent after interrupt |
| GET | `/api/v2/agentic-chat/sessions/{session_id}/events` | Yes | Poll for new agent events since last call |
| GET | `/api/v2/agentic-chat/sessions/{session_id}/stream` | Yes | Subscribe to running agent task's SSE stream (GET) |
| GET | `/api/v2/agentic-chat/sessions/{session_id}/status` | Yes | Check current agent status for a session |

---

## 14. Collection Sharing & RBAC

Prefix: `/api/v2/sharing` — Source: `api/routes/v2/sharing.py`

### Invitations

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/sharing/invite` | Yes (admin) | Invite member by email |
| POST | `/api/v2/sharing/invitations/accept` | Yes | Accept invitation |
| POST | `/api/v2/sharing/invitations/decline` | Yes | Decline invitation |
| POST | `/api/v2/sharing/invitations/cancel` | Yes (admin) | Cancel/rescind invitation |
| GET | `/api/v2/sharing/invitations` | Yes | List received invitations |
| GET | `/api/v2/sharing/invitations/sent` | Yes | List sent invitations |

### Members

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/sharing/members` | Yes | List accepted members |
| POST | `/api/v2/sharing/members/history` | Yes (admin) | Invitation audit trail |
| POST | `/api/v2/sharing/members/user-history` | Yes (admin) | Status changes for a user |
| POST | `/api/v2/sharing/members/update` | Yes (admin) | Update role / plate access |
| POST | `/api/v2/sharing/members/remove` | Yes (admin) | Remove member |
| POST | `/api/v2/sharing/transfer-ownership` | Yes (admin) | Transfer ownership |
| POST | `/api/v2/sharing/leave` | Yes (non-admin) | Leave shared collection |

### Device Tokens (FCM Push)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/sharing/device-token` | Yes | Register FCM token |
| DELETE | `/api/v2/sharing/device-token` | Yes | Unregister FCM token |

### Groups

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/sharing/groups/create` | Yes (admin) | Create group label |
| POST | `/api/v2/sharing/groups/list` | Yes | List group labels |
| POST | `/api/v2/sharing/groups/delete` | Yes (admin) | Delete group label |
| POST | `/api/v2/sharing/groups/rename` | Yes (admin) | Rename group label |
| POST | `/api/v2/sharing/members/assign-groups` | Yes | Assign groups to member |
| POST | `/api/v2/sharing/members/bulk-assign-group` | Yes (admin) | Bulk-assign group to members |
| POST | `/api/v2/sharing/members/remove-groups` | Yes | Remove groups from member |
| POST | `/api/v2/sharing/members/by-group` | Yes | List members by group |
| POST | `/api/v2/sharing/groups/members` | Yes | List members by group (alias) |

---

## 15. Collection Tasks

Prefix: `/api/v2/tasks` — Source: `api/routes/v2/tasks.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/tasks/create` | Yes (admin) | Create task (assigned users must be collection members) |
| POST | `/api/v2/tasks/update` | Yes (admin) | Update task metadata |
| POST | `/api/v2/tasks/cancel` | Yes (admin) | Cancel / soft-delete task |
| POST | `/api/v2/tasks/delete` | Yes (admin) | Permanently delete task (irreversible) |
| POST | `/api/v2/tasks/update-status` | Yes | Update task status (allowed transitions) |
| POST | `/api/v2/tasks/update-progress` | Yes | Update progress 0–100 |
| POST | `/api/v2/tasks/add-comment` | Yes | Add comment (any assigned member) |
| POST | `/api/v2/tasks/list` | Yes | List tasks (admin sees all; member sees assigned) |
| POST | `/api/v2/tasks/get` | Yes | Get task + recent activity |
| POST | `/api/v2/tasks/activity` | Yes | Activity/comment log |
| POST | `/api/v2/tasks/my-tasks` | Yes | Tasks assigned to current user |
| POST | `/api/v2/tasks/auto-distribute` | Yes (admin) | Auto-distribute verification task by splitting plate & creating child tasks |

---

## 16. Live Stream

Prefix: `/api/v2/live-stream` — Source: `api/routes/v2/live_stream.py`

### Sessions

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/live-stream/sessions` | Yes | Create session (WAITING state) |
| GET | `/api/v2/live-stream/sessions` | Yes | List sessions |
| GET | `/api/v2/live-stream/sessions/{session_id}` | Yes | Get session details + WHIP/WHEP URLs |
| POST | `/api/v2/live-stream/sessions/{session_id}/stop` | Yes | Stop active session |
| POST | `/api/v2/live-stream/sessions/{session_id}/resume` | Yes | Resume paused/stopped session |
| DELETE | `/api/v2/live-stream/sessions/{session_id}` | Yes | Delete session permanently |
| POST | `/api/v2/live-stream/sessions/{session_id}/add-questions` | Yes | Add analysis questions |
| GET | `/api/v2/live-stream/sessions/{session_id}/indexing-jobs` | Yes | Get indexing status |
| GET | `/api/v2/live-stream/sessions/{session_id}/worker-status` | Yes | Poll Qwen worker readiness |
| GET | `/api/v2/live-stream/sessions/{session_id}/mediamtx-status` | Yes | Poll MediaMTX readiness |

### Protocol-Specific Streams

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/live-stream/stream` | Yes | Start live stream with auto-detected protocol |
| POST | `/api/v2/live-stream/stream/rtmp` | Yes | Start live stream via RTMP |
| POST | `/api/v2/live-stream/stream/rtsp` | Yes | Start live stream via RTSP |
| POST | `/api/v2/live-stream/stream/srt` | Yes | Start live stream via SRT |
| POST | `/api/v2/live-stream/stream/hls` | Yes | Start live stream via HLS |
| POST | `/api/v2/live-stream/stream/webrtc` | Yes | Start live stream via WebRTC (WHIP) |
| POST | `/api/v2/live-stream/stream/youtube` | Yes | Start live stream from YouTube URL |

### MediaMTX Management

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v2/live-stream/mediamtx/health` | No | Check MediaMTX sidecar reachability |
| GET | `/api/v2/live-stream/mediamtx/config` | Yes | Get MediaMTX endpoint configuration |
| GET | `/api/v2/live-stream/mediamtx/streams` | Yes | List all active streams with session mappings |
| GET | `/api/v2/live-stream/mediamtx/streams/{path}` | Yes | Get status of a specific stream path |
| GET | `/api/v2/live-stream/mediamtx/connections/{protocol}` | Yes | List active connections for a protocol |
| GET | `/api/v2/live-stream/mediamtx/connections/summary` | Yes | Aggregated connection counts across all protocols |

### Internal Webhooks

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/live-stream/internal/live-plate-updated` | Internal | Live Qwen worker notifies new extracted_info |
| POST | `/api/v2/live-stream/internal/segment-recorded` | Internal | Segment uploaded to S3 by MediaMTX |
| POST | `/api/v2/live-stream/internal/stream-ready` | Internal | Publisher connected and path ready |
| POST | `/api/v2/live-stream/internal/stream-not-ready` | Internal | Publisher disconnected and path not ready |

### WebRTC Signaling Proxy

| Method | Path | Auth | Description |
|---|---|---|---|
| POST, OPTIONS | `/api/v2/live-stream/sessions/{session_id}/whip` | Token | WHIP signaling proxy (publish SDP offer/answer) |
| PATCH, DELETE, OPTIONS | `/api/v2/live-stream/sessions/{session_id}/whip/{resource_id}` | Token | WHIP ICE trickle / teardown |
| POST, OPTIONS | `/api/v2/live-stream/sessions/{session_id}/whep` | Token | WHEP signaling proxy (playback SDP offer/answer) |
| PATCH, DELETE, OPTIONS | `/api/v2/live-stream/sessions/{session_id}/whep/{resource_id}` | Token | WHEP ICE trickle / teardown |

---

## 17. Online Search

Prefix: `/api/v2/online-search` — Source: `api/routes/v2/online_search.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/online-search/search` | Yes | Start an online video search job |
| GET | `/api/v2/online-search/{job_id}/status` | Yes | Get search job status |
| GET | `/api/v2/online-search/{job_id}/candidates` | Yes | List candidate videos found |
| DELETE | `/api/v2/online-search/{job_id}/candidates/{video_id}` | Yes | Remove a candidate video |
| POST | `/api/v2/online-search/{job_id}/search-more` | Yes | Run additional queries for same job |
| POST | `/api/v2/online-search/{job_id}/confirm` | Yes | Confirm candidates and start indexing |

---

## 18. YouTube Search V1

Prefix: `/api/v2/yt-search` — Source: `api/routes/v2/yt_search.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/yt-search/search` | Yes | Start a YouTube search job |
| POST | `/api/v2/yt-search/refine-query` | Yes | Refine user query into optimized YouTube search queries |
| POST | `/api/v2/yt-search/{job_id}/submit-results` | Yes | Submit YouTube search results from browser extension |
| GET | `/api/v2/yt-search/{job_id}/status` | Yes | Get job status and progress |
| GET | `/api/v2/yt-search/{job_id}/candidates` | Yes | List candidate YouTube videos |
| DELETE | `/api/v2/yt-search/{job_id}/candidates/{video_id}` | Yes | Remove a candidate video |
| POST | `/api/v2/yt-search/{job_id}/candidates/trim` | Yes | Keep only specified candidate IDs; remove rest |
| POST | `/api/v2/yt-search/{job_id}/trim` | Yes | Alias for /candidates/trim |
| POST | `/api/v2/yt-search/{job_id}/search-more` | Yes | Run additional query refinement for same job |
| POST | `/api/v2/yt-search/{job_id}/confirm` | Yes | Confirm candidates and start indexing |

---

## 19. YouTube Search V2

Prefix: `/api/v2/yt-search-v2` — Source: `api/routes/v2/yt_search_v2.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/yt-search-v2/refine-query` | Yes | Step 1: Refine user query into optimized YouTube search queries |
| POST | `/api/v2/yt-search-v2/{job_id}/submit-results` | Yes | Step 2: Submit YouTube search results from browser extension |
| GET | `/api/v2/yt-search-v2/{job_id}/status` | Yes | Get job status |
| GET | `/api/v2/yt-search-v2/{job_id}/candidates` | Yes | List candidate YouTube videos |
| DELETE | `/api/v2/yt-search-v2/{job_id}/candidates/{video_id}` | Yes | Remove a single candidate |
| POST | `/api/v2/yt-search-v2/{job_id}/trim` | Yes | Keep only specified candidates, remove others |
| POST | `/api/v2/yt-search-v2/{job_id}/search-more` | Yes | Run additional query refinement for same job |
| POST | `/api/v2/yt-search-v2/{job_id}/confirm` | Yes | Confirm candidates and trigger indexing |
| POST | `/api/v2/yt-search-v2/{job_id}/confirm-selected` | Yes | Index only selected video URLs from candidate list |

---

## 20. Transactions

Prefix: `/api/v2/transactions` — Source: `api/routes/v2/transactions.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v2/transactions` | Yes | Get paginated transaction history with optional filters |
| GET | `/api/v2/transactions/summary` | Yes | Credit usage summary: balance, totals, storage |
| GET | `/api/v2/transactions/breakdown` | Yes | Credit usage breakdown by feature category |
| GET | `/api/v2/transactions/breakdown/collections` | Yes | Credit usage breakdown by collection |
| GET | `/api/v2/transactions/breakdown/plates` | Yes | Credit usage breakdown by data plate |
| GET | `/api/v2/transactions/breakdown/sessions` | Yes | Credit usage breakdown by agentic chat session |
| GET | `/api/v2/transactions/categories` | Yes | List valid transaction filter categories |
| GET | `/api/v2/transactions/timeline` | Yes | Credit usage timeline for charts (credits used/added over time) |
| GET | `/api/v2/transactions/export` | Yes | Export transaction history as CSV download |

---

## 21. Users

Prefix: `/api/v2/users` — Source: `api/routes/v2/users.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v2/users/me` | Yes | Get current user ID |
| GET | `/api/v2/users/me/uploaded-hours` | Yes | Total uploaded hours + storage |
| GET | `/api/v2/users/me/info` | Yes | Comprehensive info: credits, hours, searches |
| GET | `/api/v2/users/get_users_info` | Yes | Legacy alias for /me/info |
| GET | `/api/v2/users/api-key-check` | No | Check if API key is valid |
| GET | `/api/v2/users/api-key-check/{user_id}` | No | Check API key by user_id (path param) |
| POST | `/api/v2/users/credits/claim-welcome` | Yes | Claim one-time welcome credits |
| POST | `/api/v2/users/credits/validate-indexing` | Yes | Validate credits for indexing |
| POST | `/api/v2/users/credits/validate-video-qa` | Yes | Validate credits for video QA |
| POST | `/api/v2/users/credits/consume-video-qa` | Yes | Consume credits for video QA |
| POST | `/api/v2/users/credits/consume-indexing` | Yes | Consume credits for indexing |

---

## 22. Payments

Prefix: `/api/v2/payments` — Source: `api/routes/v2/payments.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/payments/stripe-webhook` | No (Stripe sig) | Stripe event webhook |
| GET | `/api/v2/payments/status/{payment_id}` | No | Get payment status |
| GET | `/api/v2/payments/verify/{payment_id}` | Yes | Verify payment + credits added |

---

## 23. Subscriptions

Prefix: `/api/v2/subscriptions` — Source: `api/routes/v2/subscriptions.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v2/subscriptions/plans` | No | List all subscription plans |
| GET | `/api/v2/subscriptions/pricing` | No | Full pricing info (KE token rates + estimates) |
| GET | `/api/v2/subscriptions/me` | Yes | Current subscription details |
| GET | `/api/v2/subscriptions/features` | Yes | Feature flags/limits for user's tier |
| GET | `/api/v2/subscriptions/features/all` | No | Feature matrix for all tiers |
| GET | `/api/v2/subscriptions/storage-usage` | Yes | Storage usage + projected cost |
| POST | `/api/v2/subscriptions/checkout` | Yes | Create Stripe checkout session for subscription |
| POST | `/api/v2/subscriptions/portal` | Yes | Create Stripe customer portal session |
| POST | `/api/v2/subscriptions/cancel` | Yes | Cancel current subscription at end of billing period |
| GET | `/api/v2/subscriptions/billing/overdue-status` | Yes | Get current storage overdue status |
| POST | `/api/v2/subscriptions/admin/reset-free-tier` | Admin | Trigger free-tier credit reset |
| POST | `/api/v2/subscriptions/admin/enterprise` | Admin | Create enterprise subscription |
| POST | `/api/v2/subscriptions/admin/bill-storage` | Admin | Trigger storage billing for a user |
| POST | `/api/v2/subscriptions/admin/process-storage-overdue` | Admin | Process storage overdue enforcement |

---

## 24. Invoices

Prefix: `/api/v2/invoices` — Source: `api/routes/v2/invoices.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v2/invoices` | Yes | List invoices for user |
| GET | `/api/v2/invoices/{invoice_id}` | Yes | Get invoice details |
| GET | `/api/v2/invoices/{invoice_id}/download` | Yes | Download invoice PDF |

---

## 25. Admin Dashboard

Prefix: `/api/v2/admin/dashboard` — Source: `api/routes/v2/admin_dashboard.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v2/admin/dashboard/users/count` | Admin | Total user count |
| GET | `/api/v2/admin/dashboard/users/new` | Admin | New users within date range |
| GET | `/api/v2/admin/dashboard/users/analytics` | Admin | Paginated user analytics with details |
| GET | `/api/v2/admin/dashboard/stats/plates` | Admin | Data plate count |
| GET | `/api/v2/admin/dashboard/stats/collections` | Admin | Collection count |
| GET | `/api/v2/admin/dashboard/stats/credits-used` | Admin | Total credits used |
| GET | `/api/v2/admin/dashboard/stats/recent-plates` | Admin | Recently created plates (paginated) |
| GET | `/api/v2/admin/dashboard/stats/recent-collections` | Admin | Recently created collections (paginated) |
| GET | `/api/v2/admin/dashboard/billing/aws/daily` | Admin | AWS daily billing and usage |
| GET | `/api/v2/admin/dashboard/billing/aws/monthly` | Admin | AWS monthly billing and usage |
| GET | `/api/v2/admin/dashboard/billing/gcp/monthly` | Admin | GCP monthly billing |
| GET | `/api/v2/admin/dashboard/billing/gcp/monthly/detailed` | Admin | GCP monthly billing detailed by SKU |

---

## 26. Help Menu

Prefix: `/api/v2/help` — Source: `api/routes/v2/help_menu.py`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v2/help` | Yes | Submit help / feedback request (multipart/form-data) |
| GET | `/api/v2/help` | Admin | Admin-only: retrieve paginated help requests |

---

## 27. Miscellaneous (App-Level)

Defined directly in `app.py`.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/speed-comparison-reports/index` | No | List speed comparison report JSON files (hidden from OpenAPI) |
