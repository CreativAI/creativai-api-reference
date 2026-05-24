# Sharing & RBAC

Collections can be shared with team members using role-based access control (RBAC). Each member has a collection-level role and optionally per-plate access restrictions. Groups allow organizing members by function (e.g. annotators, verifiers).

---

## Roles

| Role | Constant | Capabilities |
|---|---|---|
| `admin` | `"admin"` | Full control: invite/remove members, change roles, delete collection, manage tasks |
| `read_write` | `"read_write"` | Upload media, run indexing, search, create/edit plates, run KE |
| `read_only` | `"read_only"` | Read and search only; no modifications |
| `viewer` | `"viewer"` | Legacy alias for `read_only` |

---

## Invitations

### Invite a Member

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/invite" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "target_email": "alice@example.com",
    "role": "read_write",
    "plate_access": "all"
  }'
```

### Invite with Restricted Plate Access

By default, members see all plates. To restrict a member to specific plates:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/invite" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "target_email": "bob@example.com",
    "role": "read_write",
    "plate_access": "restricted",
    "plate_permissions": {
      "plt_001": "read_write",
      "plt_002": "read_only"
    }
  }'
```

`plate_access`: `"all"` | `"restricted"`

### Invite with Groups

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/invite" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "target_email": "charlie@example.com",
    "role": "read_write",
    "plate_access": "all",
    "groups": ["annotator"]
  }'
```

Groups must already exist on the collection (see Groups section below).

### Accept / Decline Invitation

```bash
# Accept
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/invitations/accept" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'

# Decline
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/invitations/decline" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'
```

### Cancel a Sent Invitation

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/invitations/cancel" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "target_email": "alice@example.com"
  }'
```

### List Received / Sent Invitations

```bash
# Received (as invitee)
curl "$CREATIVAI_BASE_URL/api/v2/sharing/invitations" \
  -H "X-API-Key: $CREATIVAI_API_KEY"

# Sent (as admin)
curl "$CREATIVAI_BASE_URL/api/v2/sharing/invitations/sent" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Member Management

### List Members

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/members" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'
```

### Update Member Role / Permissions

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/members/update" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "target_email": "bob@example.com",
    "role": "admin",
    "plate_access": "restricted",
    "plate_permissions": {
      "plt_003": "read_write",
      "plt_001": null
    }
  }'
```

Setting a plate permission to `null` revokes access. New entries are merged with existing permissions.

### Remove a Member

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/members/remove" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "target_email": "bob@example.com"
  }'
```

### Leave a Collection

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/leave" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'
```

### Transfer Ownership

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/transfer-ownership" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "new_owner_email": "alice@example.com"
  }'
```

---

## Groups

Groups are labels used to organize members by function. Useful for task assignment (e.g. "annotator" group gets assigned sub-plates automatically).

### Create / List / Delete / Rename Groups

```bash
# Create
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/groups/create" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'", "group_name": "annotator"}'

# List
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/groups/list" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'

# Rename
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/groups/rename" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'", "old_name": "annotator", "new_name": "Annotators"}'

# Delete
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/groups/delete" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'", "group_name": "Annotators"}'
```

### Assign / Remove Groups from a Member

```bash
# Assign groups
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/members/assign-groups" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "target_email": "charlie@example.com",
    "groups": ["annotator", "verifier"]
  }'

# Remove groups
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/members/remove-groups" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "target_email": "charlie@example.com",
    "groups": ["verifier"]
  }'

# Bulk assign a group to multiple members
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/members/bulk-assign-group" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "group_name": "annotator",
    "emails": ["alice@example.com", "bob@example.com"]
  }'

# List members in a group
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/members/by-group" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'", "group_name": "annotator"}'
```

---

## FCM Push Notifications

Register device tokens to receive push notifications (task assignments, status changes):

```bash
# Register
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/device-token" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "fcm_token_here",
    "platform": "web"
  }'

# Unregister
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/sharing/device-token" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"device_token": "fcm_token_here"}'
```

`platform`: `"web"` | `"android"` | `"ios"`

---

## Audit Trail

```bash
# Full invitation history for a collection
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/members/history" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'

# Status changes for a specific user
curl -X POST "$CREATIVAI_BASE_URL/api/v2/sharing/members/user-history" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "user_email": "alice@example.com"
  }'
```

---

## Collection Tasks

Tasks let you assign work items (annotation, review, verification) to collection members.

### Create a Task

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/create" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "title": "Annotate PPE compliance",
    "description": "Mark all segments where PPE violations occur",
    "task_type": "annotation",
    "priority": "high",
    "assigned_users": ["user_alice", "user_bob"],
    "assigned_groups": ["annotator"],
    "plate_id": "'$PLATE_ID'",
    "due_date": "2026-06-01T00:00:00Z"
  }'
```

**Task Types**: `"annotation"` | `"review"` | `"verification"` | `"general"`
**Priority**: `"low"` | `"normal"` | `"high"` | `"urgent"`

### List Tasks

```bash
# Admin sees all tasks; members see only their assigned tasks
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/list" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'

# My tasks only
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/my-tasks" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'
```

### Update Task Status

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

**Status values**: `"pending"` → `"in_progress"` → `"completed"` / `"cancelled"`

### Add a Comment

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/add-comment" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "task_id": "'$TASK_ID'",
    "comment": "Completed segments 1-50. Found 3 PPE violations."
  }'
```

### Update Progress

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

### Auto-Distribute Verification

Split a plate into equal workloads and create sub-tasks for each annotator:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/auto-distribute" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "task_title": "Verify Q1 Incidents",
    "mode": "segment_wise",
    "distribution": "equal",
    "assignees": ["user_alice", "user_bob", "user_charlie"]
  }'
```
