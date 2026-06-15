# Data Plates

Data plates are curated, named sets of video segments — the foundation for all AI analysis in CreativAI. Create a plate from search results, then use Knowledge Extraction and Agentic Chat to analyze it.

## Concept

```
Collection (indexed videos)
      │
      ├── Search  ──────────────────────────────────────────►  search_id
      │
      ├── Data Plate  ◄── search_id (or full collection)
      │       │
      │       ├── Segments  (rows: video clips with start/end timestamps)
      │       │
      │       ├── Columns  (AI-extracted answers per segment via Knowledge Extraction)
      │       │
      │       ├── Filters  (slice by any column value at read time)
      │       │
      │       └── Sub-Plates  (split work across annotators for verification)
      │
      └── Knowledge Extraction ──────────► AI answers → structured table → CSV export
```

A plate stores:
- A list of video **segments** (each with `start_time`, `end_time`, `video_url`)
- **Extracted info** — AI-generated answers per segment (columns via Knowledge Extraction)
- **Metadata** — name, creation context, original query

---

## Create a Plate from Search Results

After running a search, use the `search_id` to create a plate:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/create" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "search_id": "'$SEARCH_ID'",
    "top_k": 50,
    "levels": ["high", "medium"],
    "name": "Entrance Security Incidents",
    "user_query": "person carrying unidentified bag",
    "model_version": "base"
  }'
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `collection_id` | string | required | Collection containing the search |
| `search_id` | string | required | ID from a previous search response |
| `top_k` | int | `10` | Max segments to include |
| `levels` | list | `["high","medium","low"]` | Relevance tiers to include |
| `name` | string | auto | Plate display name |
| `model_version` | string | `"base"` | `"base"` or `"pro"` for AI quality |
| `early_stop` | bool | `false` | Stop adding segments when relevance drops |
| `image_query_key` | string | null | S3 key of image used in search query |

**Plate creation is async** — poll the returned `job_id`:

```bash
curl "$CREATIVAI_BASE_URL/api/v2/data-plates/jobs/$JOB_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Create a Plate from All Collection Segments

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/create-from-collection" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "name": "Full Collection Overview",
    "video_urls": [
      "s3://bucket/col_xxx/uploads/lobby.mp4"
    ]
  }'
```

Omit `video_urls` to include all indexed videos.

---

## List Plates

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/list" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'"}'
```

---

## Get a Plate (with Segments)

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/get" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "page": 1,
    "page_size": 50
  }'
```

Response includes `can_write` (based on caller role) and a paginated `segments` array.

---

## Filtering Segments by Extracted Column Values

After Knowledge Extraction has populated columns (e.g. "Is anyone wearing a safety vest?"), you can filter the plate at read time to only see segments matching specific answers. Filters are **case-insensitive substring matches** and can combine multiple columns.

```bash
# Show only segments where no safety vest is worn AND exactly 2 people are visible
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/get" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "page": 1,
    "page_size": 50,
    "filters": {
      "Is anyone wearing a safety vest?": "No",
      "How many people are visible?": "2"
    }
  }'
```

```bash
# Show only segments where environment is "outdoor"
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/get" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "page": 1,
    "page_size": 50,
    "filters": {
      "Describe the environment": "outdoor"
    }
  }'
```

**Key points about filters:**
- The filter key is the **exact question text** used when the column was created via Knowledge Extraction
- The filter value is matched as a **case-insensitive substring** (e.g. `"No"` matches `"No"`, `"no"`, `"None"`)
- Multiple filters are combined with **AND** logic
- Filters only apply to columns that have been extracted — unextracted columns are ignored
- Filtered results respect the same pagination (`page`, `page_size`) as unfiltered requests

---

## Update / Delete a Plate

```bash
# Update
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/update" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "name": "Updated Name"
  }'

# Delete (also removes all extracted data)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/delete" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'", "plate_id": "'$PLATE_ID'"}'
```

---

## Segment Management

### Add / Remove Segments

```bash
# Add
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/segments/add" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "segment_ids": ["seg_abc123", "seg_def456"]
  }'

# Remove
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/segments/remove" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "segment_ids": ["seg_abc123"]
  }'
```

### Update Extracted Info (Manual Override)

```bash
# Single field
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/segments/update-extracted-info" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "segment_id": "seg_abc123",
    "question": "How many people are visible?",
    "answer": "3"
  }'

# Multiple fields at once
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/segments/update-extracted-info-multiple" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "segment_id": "seg_abc123",
    "updates": {
      "How many people are visible?": "3",
      "Is the person wearing a uniform?": "No"
    }
  }'
```

### Locate a Segment (which page it's on)

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/segments/locate" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "segment_id": "seg_abc123",
    "page_size": 50
  }'
```

---

## Column Management

```bash
# List columns
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/columns/list" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'", "plate_id": "'$PLATE_ID'"}'

# Remove a column (deletes all extracted data for that column)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/columns/remove" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "column_name": "How many people are visible?"
  }'
```

---

## CSV Export

```bash
# Get presigned download URL (valid for expiration_days)
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/generate-csv" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "expiration_days": 7
  }'

# Direct streaming download
curl -O -J "$CREATIVAI_BASE_URL/api/v2/data-plates/export-csv/$COLLECTION_ID/$PLATE_ID" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

---

## Sub-Plates (Annotation & Verification)

> Use `/api/v2/data-plates/sub-plates/...` for all sub-plate operations.

Sub-plates are child plates created from a parent plate to split annotation or verification work across a team. Each sub-plate contains a subset of the parent's segments.

### Why Sub-Plates?

When a plate contains thousands of segments, a single annotator cannot review everything efficiently. Sub-plates allow you to:

- Split segments equally across multiple annotators
- Assign specific column questions to specific team members
- Filter by extracted values to route edge-cases to specialists
- Track individual verification progress per sub-plate

**Sub-plate modes:**

| Mode | Description | Use When |
|---|---|---|
| `"filter"` | Filtered subset of parent segments based on column values | Route anomalies to specialists |
| `"segment_wise"` | A contiguous slice of the parent's segment index range | Split evenly across annotators |
| `"column_wise"` | Specific columns assigned for annotation | Different experts handle different questions |

### Create a Sub-Plate Manually

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/sub-plates/create" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "parent_plate_id": "'$PLATE_ID'",
    "name": "Annotator Team 1 — Segments 1-100",
    "mode": "segment_wise",
    "slices": [{"start": 0, "end": 100}],
    "assigned_users": ["user_alice", "user_bob"]
  }'
```

### Auto-Distribute (Recommended for Team Workflows)

Creates a verification task, splits the parent plate, and assigns sub-plates to annotators — all in one atomic operation:

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/tasks/auto-distribute" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "plate_id": "'$PLATE_ID'",
    "task_title": "Verify Q1 Security Incidents",
    "mode": "segment_wise",
    "distribution": "equal",
    "assignees": ["user_alice", "user_bob", "user_charlie"]
  }'
```

This creates three sub-plates, each containing ~⅓ of the parent plate's segments, assigns them to the three users, creates a tracking task, and sends FCM push notifications to all assignees.

### Verify a Segment

Annotators mark segments as verified, flagged, or pending. This updates the sub-plate's verification progress.

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/sub-plates/verify" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "'$COLLECTION_ID'",
    "sub_plate_id": "'$SUB_PLATE_ID'",
    "segment_id": "seg_abc123",
    "status": "verified",
    "notes": "Confirmed 3 people, no PPE worn"
  }'
```

| `status` value | Meaning |
|---|---|
| `"verified"` | Segment reviewed and confirmed |
| `"flagged"` | Segment needs follow-up or escalation |
| `"pending"` | Not yet reviewed (default) |

### Check Verification Progress

```bash
curl -X POST "$CREATIVAI_BASE_URL/api/v2/data-plates/sub-plates/verification-progress" \
  -H "X-API-Key: $CREATIVAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"collection_id": "'$COLLECTION_ID'", "sub_plate_id": "'$SUB_PLATE_ID'"}'
```

Returns counts of `verified`, `flagged`, `pending` segments and an overall `progress` percentage.

---

## Next Steps

- Extract AI answers from segments → [knowledge-extraction.md](knowledge-extraction.md)
- Chat with your plate using AI → [knowledge-extraction.md](knowledge-extraction.md)
- Assign review tasks to team members → [sharing-and-rbac.md](sharing-and-rbac.md)
