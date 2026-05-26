# Collection Tasks

Tasks are work items assigned to collection members for annotation, review, or verification of video segments. They are the coordination layer between admins who define the work and team members who execute it.

> **Prefix:** `/api/v2/tasks`  
> **Auth:** All endpoints require `X-API-Key` or `Authorization: Bearer`.  
> **Access:** Admins can see and manage all tasks in a collection. Regular members can only see tasks assigned to them.

---

## How Tasks Fit Into the Workflow

```
Admin creates a Data Plate (search results or full collection)
        ↓
Admin creates a Task (or uses Auto-Distribute to split into sub-tasks)
        ↓
Annotators receive FCM push notification + can list via /tasks/my-tasks
        ↓
Annotators update status (pending → in_progress → completed)
        ↓
Annotators mark segments as verified in the Sub-Plate
        ↓
Admin monitors progress via /tasks/get and /tasks/activity
```

> **Real-world example:** A safety team receives 400 hours of warehouse CCTV. An admin creates a plate of 2,000 flagged segments, runs `auto-distribute` to split them equally across 4 annotators, and tracks daily progress until all segments are verified as PPE-compliant or escalated.

---

## Create a Task

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/create" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "title": "Annotate PPE compliance — Q1 footage",
    "description": "Review every segment and mark whether all workers are wearing hard hats and high-vis vests.",
    "task_type": "verification",
    "priority": "high",
    "assigned_users": ["user_alice", "user_bob"],
    "assigned_groups": ["annotator"],
    "due_date": "2026-06-15T00:00:00Z"
  }'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection_id` | string | Yes | Collection the task belongs to |
| `title` | string | Yes | Short human-readable task name |
| `description` | string | No | Detailed instructions for assignees |
| `task_type` | string | No | `"annotation"` \| `"review"` \| `"verification"` \| `"general"` |
| `priority` | string | No | `"low"` \| `"normal"` (default) \| `"high"` \| `"urgent"` |
| `plate_id` | string | No | Data plate the task applies to |
| `assigned_users` | list[string] | No | User IDs to assign (must be collection members) |
| `assigned_groups` | list[string] | No | Group labels to assign (members of those groups receive the task) |
| `due_date` | string (ISO-8601) | No | Deadline for the task |

**Response (`201 Created`):**
```json
{
  "success": true,
  "data": {
    "task_id": "task_abc123",
    "collection_id": "col_xxx",
    "plate_id": "plt_yyy",
    "title": "Annotate PPE compliance — Q1 footage",
    "task_type": "verification",
    "priority": "high",
    "status": "pending",
    "progress": 0,
    "assigned_users": ["user_alice", "user_bob"],
    "assigned_groups": ["annotator"],
    "due_date": "2026-06-15T00:00:00Z",
    "created_at": "2026-05-26T10:00:00Z",
    "created_by": "user_admin"
  },
  "error": null
}
```

---

## Get a Task

Retrieve full task details plus recent activity.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/get" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "task_id": "'$TASK_ID'"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": "task_abc123",
    "title": "Annotate PPE compliance — Q1 footage",
    "task_type": "verification",
    "priority": "high",
    "status": "in_progress",
    "progress": 45,
    "assigned_users": ["user_alice", "user_bob"],
    "due_date": "2026-06-15T00:00:00Z",
    "created_at": "2026-05-26T10:00:00Z",
    "recent_activity": [
      {
        "user_id": "user_alice",
        "action": "status_changed",
        "from": "pending",
        "to": "in_progress",
        "timestamp": "2026-05-26T11:00:00Z"
      }
    ]
  },
  "error": null
}
```

---

## List Tasks

```bash
# Admin: see all tasks in the collection
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/list" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'"
  }'

# Member: see only tasks assigned to the calling user
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/my-tasks" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "task_id": "task_abc123",
        "title": "Annotate PPE compliance — Q1 footage",
        "task_type": "verification",
        "priority": "high",
        "status": "in_progress",
        "progress": 45,
        "assigned_users": ["user_alice", "user_bob"],
        "due_date": "2026-06-15T00:00:00Z",
        "created_at": "2026-05-26T10:00:00Z"
      }
    ],
    "total": 1
  },
  "error": null
}
```

---

## Update a Task

Update the task title, description, priority, assignees, or due date (admin only).

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/update" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "task_id": "'$TASK_ID'",
    "priority": "urgent",
    "due_date": "2026-06-10T00:00:00Z",
    "assigned_users": ["user_alice", "user_bob", "user_charlie"]
  }'
```

Only fields provided are updated — omitted fields retain their current values.

---

## Update Task Status

Allowed transitions: `pending` → `in_progress` → `completed` or `cancelled`.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/update-status" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "task_id": "'$TASK_ID'",
    "status": "in_progress"
  }'
```

| Transition | Who can do it |
|------------|---------------|
| `pending` → `in_progress` | Any assigned member or admin |
| `in_progress` → `completed` | Any assigned member or admin |
| Any → `cancelled` | Admin only (use `/tasks/cancel`) |

---

## Update Progress

Report percentage completion (0–100). Useful for tracking multi-day annotation tasks.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/update-progress" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "task_id": "'$TASK_ID'",
    "progress": 75
  }'
```

> **Tip:** Call this at the end of each annotator session. Progress is visible to all task participants and in the admin dashboard.

---

## Add a Comment

Any assigned member or admin can add comments. Use this for status notes, blockers, or handoff messages.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/add-comment" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "task_id": "'$TASK_ID'",
    "comment": "Completed segments 1–500. Found 12 PPE violations — flagged in the sub-plate. Handing off to Bob for second review."
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "comment_id": "cmt_xyz",
    "task_id": "task_abc123",
    "user_id": "user_alice",
    "comment": "Completed segments 1–500...",
    "created_at": "2026-05-26T14:30:00Z"
  },
  "error": null
}
```

---

## Activity Log

Full audit trail of all status changes, progress updates, and comments on a task.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/activity" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "task_id": "'$TASK_ID'"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "activity": [
      {
        "activity_id": "act_001",
        "user_id": "user_admin",
        "action": "created",
        "details": { "title": "Annotate PPE compliance — Q1 footage" },
        "timestamp": "2026-05-26T10:00:00Z"
      },
      {
        "activity_id": "act_002",
        "user_id": "user_alice",
        "action": "status_changed",
        "details": { "from": "pending", "to": "in_progress" },
        "timestamp": "2026-05-26T11:00:00Z"
      },
      {
        "activity_id": "act_003",
        "user_id": "user_alice",
        "action": "progress_updated",
        "details": { "progress": 75 },
        "timestamp": "2026-05-26T14:00:00Z"
      },
      {
        "activity_id": "act_004",
        "user_id": "user_alice",
        "action": "comment_added",
        "details": { "comment": "Completed segments 1–500..." },
        "timestamp": "2026-05-26T14:30:00Z"
      }
    ]
  },
  "error": null
}
```

---

## Cancel a Task

Soft-deletes the task (marks as cancelled, preserves history). Admin only.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/cancel" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "task_id": "'$TASK_ID'"
  }'
```

---

## Delete a Task

Permanently removes the task and all its activity history. **Irreversible.** Admin only.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/delete" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "task_id": "'$TASK_ID'"
  }'
```

> **Prefer `cancel` over `delete`** unless you need to permanently remove the record. Cancelled tasks are still visible in audit logs; deleted tasks are not.

---

## Auto-Distribute Verification

Automatically splits a data plate into equal-sized sub-plates and creates one child task per assignee. This is the recommended way to distribute large verification workloads across a team.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/auto-distribute" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "task_title": "Verify Q1 Incidents",
    "task_type": "verification",
    "priority": "high",
    "mode": "segment_wise",
    "distribution": "equal",
    "assignees": ["user_alice", "user_bob", "user_charlie"],
    "due_date": "2026-06-15T00:00:00Z"
  }'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection_id` | string | Yes | Collection ID |
| `plate_id` | string | Yes | Parent plate to split |
| `task_title` | string | Yes | Title prefix; sub-tasks get a suffix like `— Alice (1–667)` |
| `task_type` | string | No | Task type applied to all sub-tasks |
| `priority` | string | No | Priority applied to all sub-tasks |
| `mode` | string | Yes | `"segment_wise"` — splits by segment count |
| `distribution` | string | Yes | `"equal"` — equal segments per assignee |
| `assignees` | list[string] | Yes | User IDs; one sub-task created per user |
| `due_date` | string (ISO-8601) | No | Deadline applied to all sub-tasks |

**Response:**
```json
{
  "success": true,
  "data": {
    "parent_task_id": "task_parent_001",
    "sub_tasks": [
      {
        "task_id": "task_sub_001",
        "assigned_user": "user_alice",
        "sub_plate_id": "plt_sub_001",
        "segment_range": { "start": 0, "end": 666 }
      },
      {
        "task_id": "task_sub_002",
        "assigned_user": "user_bob",
        "sub_plate_id": "plt_sub_002",
        "segment_range": { "start": 667, "end": 1333 }
      },
      {
        "task_id": "task_sub_003",
        "assigned_user": "user_charlie",
        "sub_plate_id": "plt_sub_003",
        "segment_range": { "start": 1334, "end": 1999 }
      }
    ],
    "total_segments": 2000,
    "segments_per_assignee": 667
  },
  "error": null
}
```

---

## Complete Annotation Workflow Example

```bash
# 1. Admin: create a plate from search results (near-miss incidents)
PLATE_ID=$(curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/create" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COLLECTION_ID\", \"search_id\": \"$SEARCH_ID\", \"name\": \"Near-Miss Q1\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['plate_id'])")

# 2. Admin: auto-distribute across 3 annotators
curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/auto-distribute" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"collection_id\": \"$COLLECTION_ID\",
    \"plate_id\": \"$PLATE_ID\",
    \"task_title\": \"Verify Near-Miss Q1\",
    \"task_type\": \"verification\",
    \"priority\": \"high\",
    \"mode\": \"segment_wise\",
    \"distribution\": \"equal\",
    \"assignees\": [\"user_alice\", \"user_bob\", \"user_charlie\"]
  }"

# 3. Annotator (user_alice): check my tasks
curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/my-tasks" \
  -H "X-API-Key: $ALICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COLLECTION_ID\"}"

# 4. Annotator: start work
curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/update-status" \
  -H "X-API-Key: $ALICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COLLECTION_ID\", \"task_id\": \"$TASK_ID\", \"status\": \"in_progress\"}"

# 5. Annotator: report progress mid-way
curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/update-progress" \
  -H "X-API-Key: $ALICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COLLECTION_ID\", \"task_id\": \"$TASK_ID\", \"progress\": 50}"

# 6. Annotator: add a handoff note
curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/add-comment" \
  -H "X-API-Key: $ALICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COLLECTION_ID\", \"task_id\": \"$TASK_ID\", \"comment\": \"Segments 1-333 done. 8 flagged incidents.\"}"

# 7. Admin: check activity log
curl -s -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/activity" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"collection_id\": \"$COLLECTION_ID\", \"task_id\": \"$TASK_ID\"}"
```
