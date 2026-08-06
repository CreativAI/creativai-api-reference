# Structured Output API — Developer Guide

Most AI systems can't effectively analyze long videos — let alone a whole library of them. Ours can.

Upload your videos into a collection. Then turn a natural-language question into a **typed JSON answer** with the **Structured Output API**.

You send a query and a JSON Schema. The agent runs the full pipeline and returns JSON that matches your schema — not prose.

`POST /api/v2/agentic-chat/structured-query`

---


## API 1 — Submit a query

`POST /api/v2/agentic-chat/structured-query`

Returns `202` with a `job_id`.

### Request options

| Field | Type | Required | Default | Description |
|---|---|:---:|---|---|
| `collection_id` | string | Yes | — | Collection to analyze. |
| `query` | string | Yes | — | Natural-language instruction (e.g. "count backhands and forehands"). |
| `output_schema` | object | Yes | — | A **JSON Schema** describing the result shape. Top-level type must be `object`. |
| `relevance_levels` | array of string | No | `["high","medium"]` | Which search buckets feed the data-plate. Subset of `high` / `medium` / `low`. |
| `top_k` | integer | No | `null` | Cap on segments kept per search. |
| `model_version` | string | No | `"pro"` | Extraction model: `base` or `pro`. |
| `plate_id` | string | No | `null` | Existing data-plate to scope/seed the analysis. |

### Response

```json
{ "success": true, "data": { "job_id": "sq_8903c014716d4721", "status": "processing" } }
```

---

## API 2 — Poll for the result

`GET /api/v2/agentic-chat/structured-query/{job_id}`

Poll this until `status` is `completed` or `failed`.

The response gives you three things: the **plan**, the **step progress**, and the **final answer**.

### Top-level fields

| Field | Type | Description |
|---|---|---|
| `status` | string | `processing` · `completed` · `failed`. |
| `result` | object | The JSON answer (populated when `completed`). |
| `error` | string | Failure reason (when `failed`). |
| `current_phase` | string | The phase running right now. |
| `current_step` | integer | Index of the active step. |
| `steps_total` | integer | Total steps in the plan. |
| `plan` | array | The ordered pipeline steps (see below). |
| `active_ke_jobs` | array | Knowledge-extraction jobs in flight. |

### The plan

The agent builds an ordered plan. Each entry maps a pipeline node to a friendly **phase**.

| Phase | What it does |
|---|---|
| `search` | Finds matching segments in the collection. |
| `create_data_plate` | Builds a table from the search results. |
| `knowledge_extraction` | Answers your question for each segment. |
| `data_retrieval` | Reads the extracted rows back. |
| `synthesis` | Aggregates the rows into the final JSON. |
| `visualization` | Optional chart generation. |
| `youtube_search` / `youtube_indexing` | Finds and indexes YouTube videos. |
| `web_search` | Fetches fresh external context. |

### The steps

Every step reports its progress and a few diagnostic details.

```json
"plan": [
  {
    "index": 0,
    "phase": "search",
    "status": "completed",
    "details": { "total_segments": 14, "level_counts": { "high": 2, "medium": 5, "low": 7 } }
  },
  {
    "index": 1,
    "phase": "create_data_plate",
    "status": "completed",
    "details": { "plate_id": "plate_9f3c", "segment_count": 7 }
  },
  {
    "index": 2,
    "phase": "knowledge_extraction",
    "status": "in_progress",
    "details": {}
  }
]
```

Step `status` is one of: `completed` · `in_progress` · `pending`.

Useful `details` keys: `total_segments`, `level_counts`, `plate_id`, `segment_count`, `row_count`, `empty`, `columns`.

### The final answer

When `status` is `completed`, `result` holds your JSON.

```json
{
  "success": true,
  "data": {
    "status": "completed",
    "result": { "backhands": 5, "forehands": 1 }
  }
}
```

The shape always matches your `output_schema`.

String fields come back as **Markdown bullet points**. Numbers stay numbers.

---

## Example

Ask one question, get typed stats back.

**Request**

```json
{
  "collection_id": "tennibot_f8f1247b",
  "query": "For each player, count backhands and forehands",
  "output_schema": {
    "type": "object",
    "properties": {
      "backhands": { "type": "integer" },
      "forehands": { "type": "integer" }
    },
    "required": ["backhands", "forehands"]
  },
  "relevance_levels": ["high", "medium", "low"]
}
```

**Result**

```json
{ "backhands": 5, "forehands": 1 }
```

---

## Billing

Same cost as the interactive chat.

- Knowledge-extraction and agentic LLM tokens are billed during the run.
- Indexing is billed only if the query triggers a YouTube-indexing step.

---

## Try it

Submit a query:

```bash
curl -sS -X POST "$HOST/api/v2/agentic-chat/structured-query" \
  -H "x-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "tennibot_f8f1247b",
    "query": "For each player, count backhands and forehands",
    "output_schema": {
      "type": "object",
      "properties": {
        "backhands": { "type": "integer" },
        "forehands": { "type": "integer" }
      },
      "required": ["backhands", "forehands"]
    },
    "relevance_levels": ["high", "medium", "low"]
  }'
```

Poll for the result (repeat until `status` is `completed`):

```bash
curl -sS "$HOST/api/v2/agentic-chat/structured-query/$JOB_ID" \
  -H "x-api-key: $API_KEY"
```

