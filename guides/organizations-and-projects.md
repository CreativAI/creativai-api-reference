# Organizations & Projects

Organize collections using a two-level hierarchy: **Organizations** → **Projects** → **Collections**.

---

## Endpoints

### Organizations

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v2/organizations` | Create an organization |
| GET | `/api/v2/organizations` | List your organizations |
| GET | `/api/v2/organizations/{org_id}` | Get organization details |
| DELETE | `/api/v2/organizations/{org_id}` | Delete org and all its contents |

### Projects

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v2/organizations/{org_id}/projects` | Create a project in an org |
| GET | `/api/v2/organizations/{org_id}/projects` | List projects in an org |
| GET | `/api/v2/organizations/{org_id}/projects/{project_name}` | Get project + its collections |
| DELETE | `/api/v2/organizations/{org_id}/projects/{project_name}` | Delete project + all collections |

---

## cURL Examples

### Create an organization

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/organizations" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp"}'
```

### List organizations

```bash
curl -X GET "$CREATIVAI_BASE_URL/api/v2/organizations" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### Create a project

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/organizations/$ORG_ID/projects" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_name": "Q1 Campaign"}'
```

### Get a project and its collections

```bash
curl -X GET "$CREATIVAI_BASE_URL/api/v2/organizations/$ORG_ID/projects/Q1%20Campaign" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

### List collections by project

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/collections/by-project" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"org_id": "'"$ORG_ID"'", "project_name": "Q1 Campaign"}'
```

---

## Python Example

```python
import os, requests

BASE    = os.environ["CREATIVAI_BASE_URL"]
KEY     = os.environ["CREATIVAI_API_KEY"]
headers = {"X-API-Key": KEY}

# Create org
org = requests.post(f"{BASE}/api/v2/organizations",
    headers=headers, json={"name": "My Team"}).json()
org_id = org["data"]["org_id"]

# Create project
requests.post(f"{BASE}/api/v2/organizations/{org_id}/projects",
    headers=headers, json={"project_name": "Launch 2026"}).raise_for_status()

# Create collection inside project
requests.post(f"{BASE}/api/v2/collections", headers=headers, json={
    "collection_name": "Launch Videos",
    "model": "default",
    "organization_id": org_id,
    "project_name": "Launch 2026",
}).raise_for_status()

# List all collections in project
cols = requests.post(f"{BASE}/api/v2/collections/by-project",
    headers=headers,
    json={"org_id": org_id, "project_name": "Launch 2026"}).json()
print(cols["data"])
```
