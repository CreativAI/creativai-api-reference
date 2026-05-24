# Async Jobs

Many CreativAI operations are long-running and return immediately with a job ID. This guide covers the polling pattern and job lifecycle for all async operations.

---

## Async Operations Overview

| Operation | Start Endpoint | Status Endpoint | Typical Duration |
|---|---|---|---|
| S3 Transfer | `POST /transfers` | `GET /transfers/{job_id}` | 1–60 min |
| Indexing | `POST /indexing/chunk-based` | `GET /indexing/chunk-based/{id}/status` | 5–30 min |
| Plate Creation | `POST /data-plates/create` | `GET /data-plates/jobs/{job_id}` | 10–60 sec |
| Knowledge Extraction | `POST /knowledge-extraction/columns/add` | `GET /knowledge-extraction/jobs/{job_id}` | 1–20 min |
| Online Search | `POST /online-search/search` | `GET /online-search/{job_id}/status` | 30 sec–5 min |
| YouTube Search | `POST /yt-search/search` | `GET /yt-search/{job_id}/status` | 30 sec–5 min |

---

## Polling Pattern

All status endpoints return a consistent `status` field. Poll until you see a terminal state.

```bash
# Universal polling loop (bash)
poll_job() {
  local URL=$1
  local INTERVAL=${2:-10}
  
  while true; do
    RESPONSE=$(curl -s "$URL" -H "X-API-Key: $CREATIVAI_API_KEY")
    STATUS=$(echo $RESPONSE | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('status','unknown'))")
    echo "$(date +%H:%M:%S) Status: $STATUS"
    
    case $STATUS in
      completed|indexing_completed|done) echo "Done!"; break ;;
      failed|error) echo "FAILED"; echo $RESPONSE; break ;;
    esac
    
    sleep $INTERVAL
  done
}

# Usage
poll_job "$CREATIVAI_BASE_URL/api/v2/indexing/chunk-based/$INDEXING_ID/status" 15
```

---

## Status Values by Operation

### Indexing

| Status | Terminal | Description |
|---|---|---|
| `initiated` | No | Job created |
| `processing` | No | Embedding pipeline running |
| `completed` | ✅ | All chunks indexed |
| `partial` | ✅ | Some chunks indexed, some failed |
| `failed` | ✅ | All chunks failed |

### Preprocessing

| Status | `can_start_indexing` | Description |
|---|---|---|
| `processing` | false | Lambda still running |
| `completed` | true | All media preprocessed |
| `partial` | true | Some succeeded, some failed |
| `failed` | false | All failed |
| `no_media` | false | No uploads yet |

### Knowledge Extraction

| Status | Terminal | Description |
|---|---|---|
| `initiated` | No | Job queued |
| `processing` | No | LLM analyzing segments |
| `completed` | ✅ | All segments processed |
| `failed` | ✅ | Job failed |

### Online Search / YouTube Search

| Status | Terminal | Description |
|---|---|---|
| `initiated` | No | Job created |
| `refining_query` | No | LLM generating search queries |
| `searching_youtube` | No | Querying YouTube |
| `fetching_transcripts` | No | Downloading transcripts |
| `finalizing` | No | Saving results |
| `completed` | ✅ | Candidates ready for review |
| `failed` | ✅ | Error (see `error_message`) |
| `indexing_initiated` | No | Indexing started after confirmation |
| `indexing_online_videos` | No | Processing video content |
| `inserting_the_data` | No | Storing in vector DB |
| `indexing_completed` | ✅ | Fully indexed |
| `indexing_failed` | ✅ | Indexing step failed |

### Plate Creation

| Status | Terminal | Description |
|---|---|---|
| `initiated` | No | Job created |
| `processing` | No | Fetching and organizing segments |
| `completed` | ✅ | Plate ready |
| `failed` | ✅ | Plate creation failed |

---

## Recommended Poll Intervals

| Operation | First poll | Subsequent polls | Max wait |
|---|---|---|---|
| Preprocessing status | After upload + 30s | Every 30s | 30 min |
| Indexing status | 30s after start | Every 15s | 60 min |
| KE job | 10s after start | Every 10s | 30 min |
| Plate creation | 5s after start | Every 5s | 5 min |
| Online search | 10s after start | Every 10s | 10 min |

---

## Python Polling Helper

```python
import time
import requests

def poll_until_done(url, api_key, interval=10, max_wait=3600, terminal_states=None):
    """Poll a status endpoint until a terminal state is reached.
    
    Returns the final response data dict.
    Raises TimeoutError if max_wait is exceeded.
    Raises RuntimeError if a failure state is reached.
    """
    if terminal_states is None:
        terminal_states = {"completed", "failed", "partial", "indexing_completed", "indexing_failed"}
    
    failure_states = {"failed", "error", "indexing_failed"}
    headers = {"X-API-Key": api_key}
    start = time.time()
    
    while True:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        status = data.get("status", "unknown")
        
        print(f"Status: {status}")
        
        if status in failure_states:
            raise RuntimeError(f"Job failed: {data}")
        if status in terminal_states:
            return data
        
        elapsed = time.time() - start
        if elapsed > max_wait:
            raise TimeoutError(f"Job did not complete within {max_wait}s. Last status: {status}")
        
        time.sleep(interval)

# Example usage
import os

BASE_URL = os.environ["CREATIVAI_BASE_URL"]
API_KEY = os.environ["CREATIVAI_API_KEY"]

# Wait for indexing
result = poll_until_done(
    f"{BASE_URL}/api/v2/indexing/chunk-based/{indexing_id}/status",
    api_key=API_KEY,
    interval=15
)
print(f"Indexed {result['indexed_chunks']} chunks")
```

---

## Notes

- **Credits are deducted at job creation**, not at completion. A failed job may still consume credits for work already done.
- For **preprocessing status**, poll `GET /indexing/preprocessing-status/{collection_id}` rather than a job endpoint — there's no job ID for preprocessing.
- Agentic Chat uses **SSE streaming** rather than polling — see [agentic-chat.md](agentic-chat.md).
