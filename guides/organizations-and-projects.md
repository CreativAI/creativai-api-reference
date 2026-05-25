# Organizations & Projects

Organize collections using a two-level hierarchy: **Organizations** → **Projects** → **Collections**.

```
Organization (Acme Corp)
  └── Project (Q1 Campaign)
        └── Collection (TV Ads)
        └── Collection (Social Media)
  └── Project (Product Launch)
        └── Collection (Demo Videos)
```

---

## Organizations

### Create an Organization

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/organizations" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp"}'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Organization display name |

**Response:**
```json
{
  "success": true,
  "data": {
    "org_id": "org_abc123",
    "name": "Acme Corp",
    "owner_id": "usr_xyz789",
    "created_at": "2026-05-26T10:00:00Z"
  },
  "error": null
}
```

### List Organizations

```bash
curl "$CREATIVAI_BASE_URL/api/v2/organizations" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "organizations": [
      {
        "org_id": "org_abc123",
        "name": "Acme Corp",
        "created_at": "2026-05-26T10:00:00Z"
      }
    ]
  },
  "error": null
}
```

### Get Organization Details

```bash
curl "$CREATIVAI_BASE_URL/api/v2/organizations/$ORG_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "org_id": "org_abc123",
    "name": "Acme Corp",
    "owner_id": "usr_xyz789",
    "projects": ["Q1 Campaign", "Product Launch"],
    "created_at": "2026-05-26T10:00:00Z"
  },
  "error": null
}
```

### Delete an Organization

**Irreversible.** Deletes all projects and collections within.

```bash
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/organizations/$ORG_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": { "message": "Organization org_abc123 deleted" },
  "error": null
}
```

---

## Projects

### Create a Project

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/organizations/$ORG_ID/projects" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_name": "Q1 Campaign"}'
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_name` | string | Yes | Project name (unique within the org) |

**Response:**
```json
{
  "success": true,
  "data": {
    "org_id": "org_abc123",
    "project_name": "Q1 Campaign",
    "created_at": "2026-05-26T10:00:00Z"
  },
  "error": null
}
```

### List Projects

```bash
curl "$CREATIVAI_BASE_URL/api/v2/organizations/$ORG_ID/projects" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "project_name": "Q1 Campaign",
        "collection_count": 3,
        "created_at": "2026-05-10T09:00:00Z"
      }
    ]
  },
  "error": null
}
```

### Get Project (+ its Collections)

```bash
# URL-encode spaces: "Q1 Campaign" → "Q1%20Campaign"
curl "$CREATIVAI_BASE_URL/api/v2/organizations/$ORG_ID/projects/Q1%20Campaign" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "org_id": "org_abc123",
    "project_name": "Q1 Campaign",
    "collections": [
      {
        "collection_id": "tv-ads_a1b2c3d4",
        "collection_name": "TV Ads",
        "total_videos": 12,
        "indexed": true,
        "created_at": "2026-05-15T11:00:00Z"
      }
    ]
  },
  "error": null
}
```

### Delete a Project

**Irreversible.** Deletes all collections within.

```bash
curl -X DELETE "$CREATIVAI_BASE_URL/api/v2/organizations/$ORG_ID/projects/Q1%20Campaign" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## List Collections by Organization or Project

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
  -d '{"organization_id": "org_abc123", "project_name": "Q1 Campaign"}'
```

---

## Python Example

```python
import os, requests

BASE    = os.environ["CREATIVAI_BASE_URL"]
KEY     = os.environ["CREATIVAI_API_KEY"]
headers = {"X-API-Key": KEY, "Content-Type": "application/json"}

# Create org
org = requests.post(f"{BASE}/api/v2/organizations",
    headers=headers, json={"name": "My Team"}).json()
org_id = org["data"]["org_id"]

# Create project
requests.post(f"{BASE}/api/v2/organizations/{org_id}/projects",
    headers=headers, json={"project_name": "Launch 2026"}).raise_for_status()

# Create collection inside project
col = requests.post(f"{BASE}/api/v2/collections", headers=headers, json={
    "collection_name": "Launch Videos",
    "model": "default",
    "organization_id": org_id,
    "project_name": "Launch 2026",
}).json()
collection_id = col["data"]["collection_id"]
print(f"Collection: {collection_id}")

# List all collections in project
cols = requests.post(f"{BASE}/api/v2/collections/by-project",
    headers=headers,
    json={"organization_id": org_id, "project_name": "Launch 2026"}).json()
print(cols["data"])
```
