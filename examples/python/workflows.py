"""
CreativAI End-to-End Workflows
===============================
Complete workflow demonstrations using the CreativAI Python client.

Each workflow function is self-contained and shows a real integration pattern.

Prerequisites:
    pip install requests
    export CREATIVAI_BASE_URL=https://api.creativai.io
    export CREATIVAI_API_KEY=your-api-key
"""

from __future__ import annotations

import os
import json
import time
from pathlib import Path

from client import CreativAIClient


client = CreativAIClient()


# ─── Workflow 1: Basic Video Indexing and Search ──────────────────────────────

def workflow_index_and_search(video_files: list[Path], query: str):
    """
    Full pipeline: create collection → upload videos → wait for preprocessing
    → index → search → print results.
    """
    print("=== Workflow 1: Index & Search ===\n")

    # 1. Create collection
    col = client.create_collection(
        name="Demo Collection",
        description="Uploaded via Python workflow",
        model="default",  # InternVideo2 (video only)
    )
    collection_id = col["collection_id"]
    print(f"Created collection: {collection_id}")

    # 2. Upload videos
    for video in video_files:
        uri = client.upload_file(collection_id, video)
        print(f"  Uploaded: {video.name} → {uri}")

    # 3. Wait for Lambda preprocessing (splits into 16s chunks)
    print("\nWaiting for preprocessing...")
    client.wait_for_preprocessing(collection_id, interval=30)

    # 4. Start indexing
    indexing = client.start_indexing(collection_id)
    indexing_id = indexing["indexing_id"]
    print(f"\nIndexing started: {indexing_id}")
    client.wait_for_indexing(indexing_id, interval=15)

    # 5. Search
    print(f"\nSearching: '{query}'")
    results = client.search(collection_id, query=query, top_k=10, search_type="hybrid")
    segments = results.get("segments", [])
    print(f"Found {len(segments)} segments")
    for seg in segments[:3]:
        print(f"  [{seg.get('relevance_bucket', 'N/A')}] {seg.get('uri', '')} "
              f"@ {seg.get('start_time', 0):.1f}s – {seg.get('end_time', 0):.1f}s")
    return results


# ─── Workflow 2: Multimodal Collection with Qwen3-VL ─────────────────────────

def workflow_qwen_multimodal(video_files: list[Path], image_files: list[Path]):
    """
    Qwen3-VL pipeline supporting videos, images, and PDFs in a single collection.
    """
    print("=== Workflow 2: Qwen Multimodal ===\n")

    col = client.create_collection(
        name="Qwen Multimodal Collection",
        model="qwen",
    )
    cid = col["collection_id"]
    print(f"Collection (Qwen3-VL): {cid}")

    # Upload mixed media
    all_files = list(video_files) + list(image_files)
    for f in all_files:
        client.upload_file(cid, f)
        print(f"  Uploaded: {f.name}")

    # Wait and index
    client.wait_for_preprocessing(cid)
    idx = client.start_indexing(cid)
    client.wait_for_indexing(idx["indexing_id"])

    # Image-based search (Qwen only)
    if image_files:
        print("\nRunning image-based search using first image as query...")
        results = client.search_with_image_file(cid, image_files[0], top_k=5)
        print(f"Image search found {len(results.get('segments', []))} matches")

    return cid


# ─── Workflow 3: Data Plates and Knowledge Extraction ────────────────────────

def workflow_data_plates_ke(collection_id: str):
    """
    Create a data plate from a search, run knowledge extraction columns,
    and download the results as CSV.
    """
    print("=== Workflow 3: Data Plates & KE ===\n")

    # 1. Create plate
    plate_resp = client.create_plate(
        collection_id=collection_id,
        name="Safety Incidents Q1",
        search_query="person not wearing hard hat on construction site",
        top_k=50,
    )
    plate_id = plate_resp.get("plate_id") or plate_resp.get("data", {}).get("plate_id")
    print(f"Plate created: {plate_id}")

    if not plate_id:
        # Job-based creation
        job_id = plate_resp.get("job_id")
        if job_id:
            print("  Waiting for plate job...")
            while True:
                status = client._data(client._get(f"data-plates/jobs/{job_id}"))
                print(f"  Job status: {status.get('status')}")
                if status.get("status") in ("completed", "failed"):
                    plate_id = status.get("plate_id")
                    break
                time.sleep(5)

    # 2. Add KE column — single question
    ke = client.add_ke_column(
        collection_id=collection_id,
        plate_id=plate_id,
        column_name="PPE Violations",
        question="What PPE violations are visible? List missing equipment.",
        model_version="base",
    )
    job_id = ke.get("job_id")
    print(f"\nKE job started: {job_id}")
    client.wait_for_ke_job(job_id)

    # 3. Add KE column — multiple questions at once
    ke2 = client.add_ke_column(
        collection_id=collection_id,
        plate_id=plate_id,
        column_name="Site Audit",
        question=[
            "How many workers are visible?",
            "Is heavy machinery operating?",
            "What is the risk level (low/medium/high)?",
        ],
        model_version="pro",
    )
    client.wait_for_ke_job(ke2["job_id"])
    print("KE columns complete")

    # 4. Export to CSV
    out = Path("/tmp/safety_incidents_q1.csv")
    client.export_plate_csv(collection_id, plate_id, out)
    print(f"\nCSV exported to: {out}")

    # 5. Conversational Q&A
    print("\nKE Chat query:")
    chat = client.ke_chat_query(
        collection_id=collection_id,
        plate_id=plate_id,
        message="Which camera location has the most PPE violations?",
        aggregate_segments=True,
    )
    print(f"  Answer: {chat.get('message', chat)[:300]}")

    return plate_id


# ─── Workflow 4: Agentic Chat with SSE ───────────────────────────────────────

def workflow_agentic_chat(collection_id: str, questions: list[str]):
    """
    Create an agentic chat session and stream responses with interrupt handling.
    """
    print("=== Workflow 4: Agentic Chat ===\n")

    # Create session
    session = client.create_chat_session(collection_id, name="Automated Analysis")
    session_id = session["session_id"]
    print(f"Session: {session_id}\n")

    for question in questions:
        print(f"Q: {question}")
        print("A: ", end="", flush=True)

        full_response = ""
        interrupt_type = None

        for event in client.chat_stream(session_id, collection_id, message=question):
            et = event.get("event")
            data = event.get("data", {})

            if et == "message_delta":
                delta = data.get("delta", "")
                print(delta, end="", flush=True)
                full_response += delta

            elif et == "message_complete":
                print()  # newline after full message

            elif et == "search_results":
                segments = data.get("results", [])
                print(f"\n  [Searched: {len(segments)} segments found]")

            elif et == "execution_plan":
                steps = data.get("steps", [])
                print(f"\n  [Plan: {len(steps)} steps]")

            elif et == "interrupt":
                interrupt_type = data.get("interrupt_type")
                print(f"\n  [Interrupt: {interrupt_type}]")
                break

            elif et == "done":
                break

        # Handle interrupts
        if interrupt_type == "search_feedback":
            print("  Providing search feedback...")
            client.send_search_feedback(session_id, "Focus on the most critical incidents only")
            # Continue streaming
            for event in client.chat_stream(session_id, collection_id, message=""):
                et = event.get("event")
                if et == "message_delta":
                    print(event["data"].get("delta", ""), end="", flush=True)
                elif et in ("message_complete", "done"):
                    print()
                    break

        elif interrupt_type == "youtube_search_candidates_ready":
            print("  YouTube candidates ready — confirming all...")
            # In production, review candidates first
            # client.confirm_online_search(job_id, collection_id)
            pass

        print()

    client.delete_chat_session(session_id)
    print("Session closed")


# ─── Workflow 5: Live Stream Ingestion ───────────────────────────────────────

def workflow_live_stream(collection_id: str, camera_urls: list[dict]):
    """
    Start live stream sessions for multiple cameras, monitor, then stop.

    camera_urls: [{"url": "rtsp://...", "name": "Camera 1"}, ...]
    """
    print("=== Workflow 5: Live Stream ===\n")

    sessions = []
    for camera in camera_urls:
        session = client.start_live_stream(
            collection_id=collection_id,
            source_url=camera["url"],
            name=camera["name"],
            periodic_indexing=5,  # auto-index every 5 minutes
        )
        session_id = session["session_id"]
        sessions.append(session_id)
        print(f"  Started: {camera['name']} → session {session_id}")

    # Check MediaMTX health
    health = client.get_mediamtx_health()
    print(f"\nMediaMTX health: {health.get('status')}")

    # Monitor for 30 seconds
    print("Monitoring for 30s...")
    time.sleep(30)

    # Stop all sessions
    for session_id in sessions:
        client.stop_live_stream(session_id)
        print(f"  Stopped: {session_id}")

    return sessions


# ─── Workflow 6: YouTube Discovery and Indexing ───────────────────────────────

def workflow_youtube_discovery(collection_id: str, search_query: str):
    """
    Use Online Search to find YouTube videos and index them into a Qwen collection.
    """
    print("=== Workflow 6: YouTube Discovery ===\n")

    # Start search
    job = client.online_search(collection_id, search_query)
    job_id = job["job_id"]
    print(f"Search job: {job_id}")

    # Wait until candidates are ready
    client.wait_for_online_search(job_id, interval=10)

    # Review candidates
    candidates = client.get_online_search_candidates(job_id)
    print(f"\nFound {len(candidates)} candidates:")
    for c in candidates:
        print(f"  [{c.get('duration_seconds', 0)//60}m] {c.get('title', 'N/A')}")
        print(f"    {c.get('url')}")

    # Confirm all candidates for indexing
    confirm = client.confirm_online_search(job_id, collection_id)
    print(f"\nIndexing started: {confirm}")

    # Wait for indexing to complete
    client.wait_for_online_search(job_id, interval=15, max_wait=1800)
    print("YouTube videos indexed")
    return job_id


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("CreativAI Workflows Demo")
    print("========================\n")

    # Verify connection
    me = client.get_me()
    print(f"Connected as: {me.get('email', me.get('user_id', 'unknown'))}\n")

    # Run Workflow 1 with local files
    sample_videos = list(Path(".").glob("*.mp4"))
    if sample_videos:
        workflow_index_and_search(
            video_files=sample_videos[:2],
            query="person entering restricted area",
        )
    else:
        print("No .mp4 files found in current directory. Skipping Workflow 1.")
        print("Set a COL_ID env var to run other workflows:")
        col_id = os.environ.get("COL_ID")
        if col_id:
            print(f"\nRunning Workflows 3, 4 with COL_ID={col_id}")
            plate_id = workflow_data_plates_ke(col_id)
            workflow_agentic_chat(col_id, [
                "What are the top 3 most concerning incidents in this footage?",
                "Are there any patterns in the timing of incidents?",
            ])
