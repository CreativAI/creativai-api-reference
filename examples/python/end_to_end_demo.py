"""
CreativAI — End-to-End Developer Demo
======================================
This script walks through the full CreativAI workflow from scratch:

  Step 1  →  Authenticate & verify credits
  Step 2  →  Create a collection
  Step 3  →  Upload local video (road_traffic_footage.mp4) to collection
  Step 4  →  Wait for preprocessing
  Step 5  →  Estimate indexing cost, then start indexing
  Step 6  →  Run semantic search (3 example queries)
  Step 7  →  Create a data plate from search results
  Step 8  →  Run knowledge extraction (3 questions)
  Step 9  →  Display extracted results per segment
  Step 10 →  Export results to CSV
  Step 11 →  Agentic chat — ask one natural-language question
  Step 12 →  (Optional) Clean up

Setup
-----
1.  pip install requests
2.  export CREATIVAI_API_KEY="sk_live_..."
3.  Ensure road_traffic_footage.mp4 is present in the repository root
4.  python end_to_end_demo.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# ── Import the thin client that lives next to this file ──────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from client import CreativAIClient

# ╔══════════════════════════════════════════════════════════════════╗
# ║                    CONFIGURATION                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

# Local video file — road_traffic_footage.mp4 lives next to this script.
# Path is resolved relative to this script so it works from any working directory.
LOCAL_VIDEO_PATH = Path(__file__).parent / "road_traffic_footage.mp4"
VIDEO_NAME       = LOCAL_VIDEO_PATH.name  # "road_traffic_footage.mp4"

# Collection settings
COLLECTION_NAME  = "CreativAI Demo — Road Traffic Footage"
COLLECTION_MODEL = "multimodal"  # "video_only" | "multimodal"

# Search queries run after indexing — tailored to road-traffic footage
SEARCH_QUERIES = [
    "vehicles and cars on road",
    "traffic congestion or heavy traffic",
    "pedestrians crossing the road or walking near traffic",
]

# Data plate: created from the first search above
PLATE_NAME  = "Demo Plate — Traffic Incidents"
PLATE_TOP_K = 20  # max segments to include in the plate

# Knowledge extraction questions — answered per video segment
KE_QUESTIONS = [
    {
        "column_name": "traffic_activity",
        "question": "Describe the traffic activity in this segment. How many vehicles are visible and what are they doing?",
    },
    {
        "column_name": "road_hazard",
        "question": "Is there any road hazard, traffic violation, or unusual incident visible? If yes, describe it briefly.",
    },
    {
        "column_name": "road_condition",
        "question": "What is the road and weather condition? (e.g. clear highway, wet road, intersection, night-time, congested, etc.)",
    },
]

# Where to save the exported CSV
OUTPUT_CSV = Path("demo_extraction_results.csv")

# ╔══════════════════════════════════════════════════════════════════╗
# ║                    HELPERS                                        ║
# ╚══════════════════════════════════════════════════════════════════╝

# ANSI colours — fall back gracefully on non-TTY terminals
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_GREEN  = "\033[32m"
_CYAN   = "\033[36m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_DIM    = "\033[2m"

def _c(text: str, colour: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"{colour}{text}{_RESET}"

def banner(step: int, title: str) -> None:
    line = "─" * 60
    print(f"\n{_c(line, _CYAN)}")
    print(_c(f"  Step {step}  │  {title}", _BOLD))
    print(_c(line, _CYAN))

def ok(msg: str)   -> None: print(_c(f"  ✓ {msg}", _GREEN))
def info(msg: str) -> None: print(_c(f"  ·  {msg}", _DIM))
def warn(msg: str) -> None: print(_c(f"  ⚠  {msg}", _YELLOW))
def fail(msg: str) -> None: print(_c(f"  ✗  {msg}", _RED)); sys.exit(1)

def poll(label: str, fn, terminal: set[str], interval: int = 10, max_wait: int = 1800, progress_fn=None) -> dict:
    """Generic poll loop. ``fn`` must return a dict with a ``"status"`` key.
    Optional ``progress_fn(result) -> str`` is called to append extra info (e.g. percentage).
    """
    start = time.time()
    dots = 0
    while True:
        result = fn()
        st = result.get("status", "unknown")
        elapsed = int(time.time() - start)
        extra = f"  {progress_fn(result)}" if progress_fn else ""
        print(f"\r  {label}: {_c(st, _YELLOW)}{extra}  [{elapsed}s]" + "." * (dots % 4) + "   ", end="", flush=True)
        dots += 1
        if st in terminal:
            print()  # newline after the \r loop
            return result
        if time.time() - start > max_wait:
            print()
            fail(f"{label} timed out after {max_wait}s")
        time.sleep(interval)


# ╔══════════════════════════════════════════════════════════════════╗
# ║                    MAIN DEMO                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

BASE_URL = "https://creativai-apis.com"


def main() -> None:
    client = CreativAIClient(base_url=BASE_URL)

    collection_id: str = ""
    plate_id: str      = ""

    # ──────────────────────────────────────────────────────────────
    # Step 1 — Authenticate & verify credits
    # ──────────────────────────────────────────────────────────────
    banner(1, "Authenticate & verify credits")
    try:
        me = client.get_me()
    except Exception as exc:
        fail(f"Authentication failed — {exc}\n"
             "  Make sure CREATIVAI_API_KEY is set: export CREATIVAI_API_KEY=sk_live_...")

    user_id = me.get("user_id", "unknown")
    credits = me.get("credits", me.get("credits_remaining", "?"))
    uploaded_hours = me.get("total_indexed_hours", me.get("uploaded_hours", "?"))
    ok(f"Authenticated as {_c(user_id, _BOLD)}")
    ok(f"Credits available  : {_c(str(credits), _BOLD)}")
    ok(f"Total indexed hours: {uploaded_hours}")

    if isinstance(credits, (int, float)) and credits < 10:
        warn("Low credits. Some steps (indexing, KE) consume credits.")

    # ──────────────────────────────────────────────────────────────
    # Step 2 — Create a collection
    # ──────────────────────────────────────────────────────────────
    banner(2, "Create collection")
    col = client.create_collection(
        name=COLLECTION_NAME,
        description="Automatically created by end_to_end_demo.py",
        model=COLLECTION_MODEL,
    )
    collection_id = col["collection_id"]
    ok(f"Collection created  : {_c(collection_id, _BOLD)}")
    ok(f"Model               : {COLLECTION_MODEL}")

    # ──────────────────────────────────────────────────────────────
    # Step 3 — Upload local video to collection
    # ──────────────────────────────────────────────────────────────
    banner(3, "Upload local video to collection")
    info(f"Local file : {LOCAL_VIDEO_PATH}")

    if not LOCAL_VIDEO_PATH.exists():
        fail(
            f"Video file not found: {LOCAL_VIDEO_PATH}\n"
            "  Make sure road_traffic_footage.mp4 is in the repository root."
        )

    _mb = LOCAL_VIDEO_PATH.stat().st_size // 1_048_576
    info(f"File size  : {_mb} MB")

    info("Initiating multipart upload → uploading parts → completing…")
    s3_uri = client.upload_file(collection_id, LOCAL_VIDEO_PATH)
    ok(f"Uploaded   : {s3_uri or VIDEO_NAME}")

    # ──────────────────────────────────────────────────────────────
    # Step 4 — Wait for preprocessing
    # ──────────────────────────────────────────────────────────────
    banner(4, "Wait for preprocessing")
    info("CreativAI splits uploaded videos into 16-second chunks for indexing.")

    # Preprocessing response uses "preprocessing_status" key and "can_start_indexing" flag.
    # Poll until can_start_indexing is True (covers "completed" and "partial" states).
    _preproc_start = time.time()
    preproc = client.get_preprocessing_status(collection_id)
    while not preproc.get("can_start_indexing"):
        _pre_st = preproc.get("preprocessing_status", preproc.get("status", "unknown"))
        _elapsed = int(time.time() - _preproc_start)
        print(f"\r  Preprocessing: {_c(_pre_st, _YELLOW)}  [{_elapsed}s]   ", end="", flush=True)
        if _pre_st == "failed":
            print()
            fail(f"Preprocessing failed: {preproc}")
        if time.time() - _preproc_start > 1200:
            print()
            fail("Preprocessing timed out after 1200s")
        time.sleep(20)
        preproc = client.get_preprocessing_status(collection_id)
    print()  # newline after \r loop

    chunk_count = preproc.get("total_chunks", preproc.get("chunk_count", "?"))
    ok(f"Preprocessing done  : {chunk_count} chunk(s) ready")

    # ──────────────────────────────────────────────────────────────
    # Step 5 — Estimate cost, then index
    # ──────────────────────────────────────────────────────────────
    banner(5, "Estimate cost & start indexing")
    try:
        estimate = client.estimate_indexing_cost(collection_id)
        est_credits = estimate.get("estimated_credits", estimate.get("cost_estimate", "?"))
        info(f"Estimated indexing cost: {est_credits} credits")
    except Exception:
        info("Cost estimation not available — continuing.")

    indexing = client.start_indexing(collection_id)
    indexing_id = indexing.get("indexing_id") or indexing.get("job_id")
    ok(f"Indexing job started: {_c(indexing_id, _BOLD)}")

    result = poll(
        label="Indexing",
        fn=lambda: client.get_indexing_status(indexing_id),
        terminal={"completed", "partial", "failed"},
        interval=15,
        max_wait=3600,
        progress_fn=lambda r: f"{int(r.get('progress', 0) * 100)}%",
    )
    if result.get("status") == "failed":
        fail(f"Indexing failed: {result}")
    segments_indexed = result.get("indexed_chunks", result.get("total_chunks", "?"))
    ok(f"Indexing complete   : {segments_indexed} segment(s) indexed  (status={result['status']})")

    # ──────────────────────────────────────────────────────────────
    # Step 6 — Semantic search
    # ──────────────────────────────────────────────────────────────
    banner(6, "Semantic search")
    first_search_id: str | None = None

    for i, query in enumerate(SEARCH_QUERIES, 1):
        results = client.search(
            collection_id,
            query=query,
            top_k=50,
            search_type="hybrid",
        )
        # Search response uses relevance buckets: high / medium / low
        high_segs   = results.get("high", [])
        medium_segs = results.get("medium", [])
        low_segs    = results.get("low", [])
        segments    = high_segs + medium_segs + low_segs
        search_id   = results.get("search_id")
        print(f"\n  Query {i}: \"{_c(query, _BOLD)}\"")
        print(f"  Found {len(segments)} segment(s)  (high={len(high_segs)} med={len(medium_segs)} low={len(low_segs)})  │  search_id={search_id}")
        for seg in segments[:3]:
            score  = seg.get("score", "?")
            bucket = seg.get("relevance_bucket", "")
            uri    = seg.get("video_s3_uri", seg.get("uri", seg.get("video_url", "")))
            t0_s   = seg.get("start_time", 0)
            t1_s   = seg.get("end_time", 0)
            score_str = f"{score:.3f}" if isinstance(score, float) else str(score)
            print(f"    [{score_str}|{bucket}]  {uri}  @  {t0_s:.1f}s – {t1_s:.1f}s")
        if i == 1:
            first_search_id = search_id  # keep for plate creation

    # ──────────────────────────────────────────────────────────────
    # Step 7 — Create a data plate
    # ──────────────────────────────────────────────────────────────
    banner(7, "Create data plate")

    if first_search_id:
        info(f"Building plate from search_id={first_search_id} (query='{SEARCH_QUERIES[0]}')")
        plate_resp = client.create_plate(
            collection_id=collection_id,
            name=PLATE_NAME,
            search_id=first_search_id,
            top_k=PLATE_TOP_K,
        )
    else:
        info("No search_id available — building plate from full collection instead.")
        plate_resp = client.create_plate_from_collection(collection_id, PLATE_NAME)

    plate_job_id = plate_resp.get("job_id")
    plate_id     = plate_resp.get("plate_id")

    if plate_job_id and not plate_id:
        info(f"Plate creation job: {plate_job_id}  — polling...")
        job_result = poll(
            label="Plate creation",
            fn=lambda: client._data(client._get(f"data-plates/jobs/{plate_job_id}")),
            terminal={"completed", "failed"},
            interval=5,
            max_wait=300,
        )
        if job_result.get("status") == "failed":
            fail(f"Plate creation failed: {job_result}")
        plate_id = job_result.get("plate_id")

    if not plate_id:
        fail("Could not determine plate_id from creation response.")

    ok(f"Data plate created  : {_c(plate_id, _BOLD)}")
    ok(f"Plate name          : {PLATE_NAME}")

    plate_data   = client.get_plate(collection_id, plate_id)
    seg_count    = len(plate_data.get("segments", []))
    ok(f"Segments in plate   : {seg_count}")

    # ──────────────────────────────────────────────────────────────
    # Step 8 — Knowledge extraction (3 questions)
    # ──────────────────────────────────────────────────────────────
    banner(8, "Knowledge extraction")
    info(f"Running {len(KE_QUESTIONS)} extraction question(s) across {seg_count} segment(s)…")

    ke_job_ids: list[str] = []
    for q in KE_QUESTIONS:
        info(f"  Column '{q['column_name']}': {q['question'][:70]}…")
        ke_resp = client.add_ke_column(
            collection_id=collection_id,
            plate_id=plate_id,
            column_name=q["column_name"],
            question=q["question"],
            model_version="base",
        )
        job_id = ke_resp.get("job_id") or ke_resp.get("ke_job_id")
        if job_id:
            ke_job_ids.append(job_id)

    ok(f"Queued {len(ke_job_ids)} KE job(s)")

    for job_id in ke_job_ids:
        result = poll(
            label=f"KE job {job_id[:16]}",
            fn=lambda jid=job_id: client.get_ke_job(jid),
            terminal={"completed", "failed"},
            interval=10,
            max_wait=1800,
        )
        if result.get("status") == "failed":
            warn(f"KE job {job_id} failed — continuing with partial results.")
        else:
            ok(f"KE job {job_id[:16]} done")

    # ──────────────────────────────────────────────────────────────
    # Step 9 — Display extracted results
    # ──────────────────────────────────────────────────────────────
    banner(9, "Extracted results")

    refreshed = client.get_plate(collection_id, plate_id)
    segments  = refreshed.get("segments", [])

    if not segments:
        warn("No segments returned — the plate may still be processing.")
    else:
        print(f"\n  {'Segment':<20}  {'Time':>10}  {'traffic_activity':<46}  {'road_hazard':<22}  road_condition")
        print("  " + "─" * 130)
        for seg in segments[:10]:  # cap display at 10 rows
            info_map = seg.get("extracted_info", {})
            seg_id   = str(seg.get("segment_id", seg.get("id", "")))[:18]
            t0       = seg.get("start_time", seg.get("start", 0))
            t1       = seg.get("end_time",   seg.get("end",   0))
            activity = str(info_map.get("traffic_activity", "—"))[:44]
            hazard   = str(info_map.get("road_hazard",      "—"))[:20]
            cond     = str(info_map.get("road_condition",   "—"))[:24]
            print(f"  {seg_id:<20}  {t0:>5.1f}–{t1:<5.1f}  {activity:<46}  {hazard:<22}  {cond}")

        if len(segments) > 10:
            info(f"  … and {len(segments) - 10} more segments (see CSV export)")

    # ──────────────────────────────────────────────────────────────
    # Step 10 — Export to CSV
    # ──────────────────────────────────────────────────────────────
    banner(10, "Export results to CSV")
    try:
        client.export_plate_csv(collection_id, plate_id, OUTPUT_CSV)
        ok(f"CSV saved           : {OUTPUT_CSV.resolve()}")
    except Exception as exc:
        warn(f"CSV export failed (non-fatal): {exc}")

    # ──────────────────────────────────────────────────────────────
    # Step 11 — Agentic chat (single question, streaming)
    # ──────────────────────────────────────────────────────────────
    banner(11, "Agentic chat — natural language question")
    AGENT_QUESTION = "Analyse the road traffic footage. What are the most common traffic patterns, any notable incidents or hazards, and what is the overall road condition throughout the video?"
    info(f"Question: \"{AGENT_QUESTION}\"")

    try:
        session = client.create_chat_session(collection_id, name="Demo session")
        session_id = session.get("session_id")
        ok(f"Session created     : {session_id}")

        print()
        answer_text = ""
        for event in client.chat_stream(session_id, collection_id, AGENT_QUESTION):
            etype = event.get("event", "")
            data  = event.get("data", {})

            if etype == "thinking":
                text = data.get("text", data) if isinstance(data, dict) else str(data)
                print(_c(f"  [thinking] {str(text)[:100]}", _DIM))

            elif etype in ("answer", "message", "response"):
                text = data.get("text", data.get("content", data)) if isinstance(data, dict) else str(data)
                answer_text = str(text)
                print(f"\n  {_c('Answer:', _GREEN + _BOLD)}\n")
                # Word-wrap at ~80 chars
                words = answer_text.split()
                line = "  "
                for w in words:
                    if len(line) + len(w) > 82:
                        print(line)
                        line = "  " + w + " "
                    else:
                        line += w + " "
                if line.strip():
                    print(line)

            elif etype == "done":
                break

        client.delete_chat_session(session_id)
        ok("Agent session cleaned up")
    except Exception as exc:
        warn(f"Agentic chat skipped (non-fatal): {exc}")

    # ──────────────────────────────────────────────────────────────
    # Step 12 — Optional cleanup
    # ──────────────────────────────────────────────────────────────
    banner(12, "Cleanup (optional)")
    print()
    print(f"  Collection ID  : {_c(collection_id, _BOLD)}")
    print(f"  Plate ID       : {_c(plate_id, _BOLD)}")
    print(f"  CSV export     : {OUTPUT_CSV}")
    print()

    if sys.stdin.isatty():
        answer = input(_c("  Delete the demo collection and all its data? [y/N]: ", _YELLOW)).strip().lower()
    else:
        answer = "n"

    if answer == "y":
        client.delete_collection(collection_id)
        ok("Collection deleted")
    else:
        ok("Collection preserved — you can explore it in the CreativAI app.")
        info(f"https://creativ-ai.com/collections/{collection_id}")

    # ── Final summary ──────────────────────────────────────────────
    print(f"\n{_c('═' * 60, _GREEN)}")
    print(_c("  Demo completed successfully.", _GREEN + _BOLD))
    print(f"  Ran: authenticate → create collection → import URL → preprocess")
    print(f"       → index → search × {len(SEARCH_QUERIES)} → data plate → knowledge extraction × {len(KE_QUESTIONS)}")
    print(f"       → export CSV → agentic chat")
    print(_c("═" * 60, _GREEN))
    print()


# ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
