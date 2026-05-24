"""
CreativAI Python Client
=======================
A lightweight, zero-dependency (stdlib + requests) client for the CreativAI API v2.

Usage:
    from client import CreativAIClient

    client = CreativAIClient(
        base_url="https://api.creativai.io",
        api_key="your-api-key"
    )
    col = client.create_collection("My Collection", model="qwen")
    print(col)
"""

from __future__ import annotations

import os
import time
import json
import base64
from pathlib import Path
from typing import Any, Iterator
import requests


class CreativAIClient:
    """Thin HTTP client for the CreativAI API v2."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 60,
    ):
        self.base_url = (base_url or os.environ["CREATIVAI_BASE_URL"]).rstrip("/")
        self.api_key = api_key or os.environ["CREATIVAI_API_KEY"]
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": self.api_key})

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/v2/{path.lstrip('/')}"

    def _get(self, path: str, **kwargs) -> dict:
        r = self.session.get(self._url(path), timeout=self.timeout, **kwargs)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, json_body: dict | None = None, **kwargs) -> dict:
        r = self.session.post(self._url(path), json=json_body, timeout=self.timeout, **kwargs)
        r.raise_for_status()
        return r.json()

    def _patch(self, path: str, json_body: dict) -> dict:
        r = self.session.patch(self._url(path), json=json_body, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _delete(self, path: str, **kwargs) -> dict:
        r = self.session.delete(self._url(path), timeout=self.timeout, **kwargs)
        r.raise_for_status()
        return r.json()

    def _data(self, resp: dict) -> Any:
        """Unwrap the standard {'success': bool, 'data': ...} envelope."""
        return resp.get("data", resp)

    # ─── Authentication ───────────────────────────────────────────────────────

    def check_api_key(self) -> dict:
        return self._data(self._get("users/api-key-check"))

    def get_me(self) -> dict:
        return self._data(self._get("users/me/info"))

    # ─── Collections ─────────────────────────────────────────────────────────

    def create_collection(
        self,
        name: str,
        description: str = "",
        model: str = "default",
    ) -> dict:
        """
        model: "default" (InternVideo2) | "qwen" (Qwen3-VL, multimodal)
        """
        return self._data(self._post("collections", {
            "collection_name": name,
            "description": description,
            "model": model,
        }))

    def list_collections(self) -> list[dict]:
        resp = self._get("collections")
        return self._data(resp)

    def get_collection(self, collection_id: str) -> dict:
        return self._data(self._get(f"collections/{collection_id}"))

    def update_collection(self, collection_id: str, **kwargs) -> dict:
        return self._data(self._patch(f"collections/{collection_id}", kwargs))

    def delete_collection(self, collection_id: str) -> dict:
        return self._data(self._delete(f"collections/{collection_id}"))

    # ─── Media Upload ─────────────────────────────────────────────────────────

    def get_upload_url(self, collection_id: str, filename: str, content_type: str = "video/mp4") -> dict:
        return self._data(self._post(f"collections/{collection_id}/upload-url", {
            "filename": filename,
            "content_type": content_type,
        }))

    def get_upload_urls(self, collection_id: str, files: list[dict]) -> list[dict]:
        """files: [{"filename": "...", "content_type": "..."}]"""
        return self._data(self._post(f"collections/{collection_id}/upload-urls", {"files": files}))

    def upload_file(self, collection_id: str, file_path: str | Path) -> str:
        """Upload a local file using a presigned URL. Returns the S3 URI."""
        file_path = Path(file_path)
        content_type = "video/mp4" if file_path.suffix in (".mp4", ".mov", ".avi") else "image/jpeg"
        resp = self.get_upload_url(collection_id, file_path.name, content_type)
        upload_url = resp["upload_url"]
        with open(file_path, "rb") as f:
            put_resp = requests.put(upload_url, data=f, headers={"Content-Type": content_type})
            put_resp.raise_for_status()
        return resp.get("s3_uri", resp.get("media_uri", ""))

    def list_media(self, collection_id: str) -> list[dict]:
        return self._data(self._get(f"collections/{collection_id}/media"))

    # ─── Indexing ─────────────────────────────────────────────────────────────

    def get_preprocessing_status(self, collection_id: str) -> dict:
        return self._data(self._get(f"indexing/preprocessing-status/{collection_id}"))

    def wait_for_preprocessing(self, collection_id: str, interval: int = 30, max_wait: int = 1800) -> dict:
        """Block until preprocessing is complete (can_start_indexing=True)."""
        start = time.time()
        while True:
            status = self.get_preprocessing_status(collection_id)
            print(f"Preprocessing: {status.get('status')} | can_start_indexing={status.get('can_start_indexing')}")
            if status.get("can_start_indexing"):
                return status
            if time.time() - start > max_wait:
                raise TimeoutError("Preprocessing timed out")
            time.sleep(interval)

    def start_indexing(
        self,
        collection_id: str,
        uris: list[str] | None = None,
        tags: dict | None = None,
    ) -> dict:
        """
        uris: optional list of specific S3 URIs to index (None = index all preprocessed media)
        tags: {"uri": ["tag1", "tag2"]} or {"*": ["global-tag"]}
        """
        body: dict = {"collection_id": collection_id}
        if uris:
            body["uris"] = uris
        if tags:
            body["tags"] = tags
        return self._data(self._post("indexing/chunk-based", body))

    def get_indexing_status(self, indexing_id: str) -> dict:
        return self._data(self._get(f"indexing/chunk-based/{indexing_id}/status"))

    def wait_for_indexing(self, indexing_id: str, interval: int = 15, max_wait: int = 3600) -> dict:
        """Block until indexing reaches a terminal state."""
        terminal = {"completed", "partial", "failed"}
        start = time.time()
        while True:
            status = self.get_indexing_status(indexing_id)
            st = status.get("status", "unknown")
            print(f"Indexing: {st}")
            if st in terminal:
                return status
            if time.time() - start > max_wait:
                raise TimeoutError("Indexing timed out")
            time.sleep(interval)

    def estimate_indexing_cost(self, collection_id: str) -> dict:
        return self._data(self._post("indexing/chunk-based/estimate-cost", {"collection_id": collection_id}))

    # ─── Search ───────────────────────────────────────────────────────────────

    def search(
        self,
        collection_id: str,
        query: str | None = None,
        image_base64: str | None = None,
        image_key: str | None = None,
        top_k: int = 10,
        search_type: str = "hybrid",
        filters: dict | None = None,
        search_id: str | None = None,
        page_number: int | None = None,
    ) -> dict:
        """
        search_type: "hybrid" | "vision" | "audio"
        For image-based search (Qwen only): provide image_base64 or image_key instead of query.
        """
        body: dict = {
            "collection_id": collection_id,
            "top_k": top_k,
            "search_type": search_type,
        }
        if query:
            body["query"] = query
        if image_base64:
            body["image_base64"] = image_base64
        if image_key:
            body["image_key"] = image_key
        if filters:
            body["filters"] = filters
        if search_id:
            body["search_id"] = search_id
        if page_number:
            body["page_number"] = page_number
        return self._data(self._post("search", body))

    def search_with_image_file(self, collection_id: str, image_path: str | Path, **kwargs) -> dict:
        """Search using a local image file as the query (Qwen collections only)."""
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        return self.search(collection_id, image_base64=img_b64, **kwargs)

    # ─── Data Plates ─────────────────────────────────────────────────────────

    def create_plate(self, collection_id: str, name: str, search_query: str, top_k: int = 50) -> dict:
        return self._data(self._post("data-plates/create", {
            "collection_id": collection_id,
            "plate_name": name,
            "search_query": search_query,
            "top_k": top_k,
        }))

    def create_plate_from_collection(self, collection_id: str, name: str) -> dict:
        return self._data(self._post("data-plates/create-from-collection", {
            "collection_id": collection_id,
            "plate_name": name,
        }))

    def list_plates(self, collection_id: str) -> list[dict]:
        return self._data(self._post("data-plates/list", {"collection_id": collection_id}))

    def get_plate(self, collection_id: str, plate_id: str) -> dict:
        return self._data(self._post("data-plates/get", {
            "collection_id": collection_id,
            "plate_id": plate_id,
        }))

    def export_plate_csv(self, collection_id: str, plate_id: str, output_path: str | Path) -> Path:
        """Generate and download a plate as CSV."""
        gen = self._data(self._post("data-plates/generate-csv", {
            "collection_id": collection_id,
            "plate_id": plate_id,
        }))
        csv_id = gen.get("csv_id") or gen.get("export_id")
        r = self.session.get(self._url(f"data-plates/export-csv/{collection_id}/{csv_id}"), stream=True)
        r.raise_for_status()
        output_path = Path(output_path)
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return output_path

    # ─── Knowledge Extraction ────────────────────────────────────────────────

    def add_ke_column(
        self,
        collection_id: str,
        plate_id: str,
        column_name: str,
        question: str | list[str],
        model_version: str = "base",
        image_keys: list[str] | None = None,
    ) -> dict:
        """
        model_version: "base" | "pro"
        question: single string or list of strings (multi-question column)
        image_keys: up to 10 S3 keys from /knowledge-extraction/chat/upload-images
        """
        body: dict = {
            "collection_id": collection_id,
            "plate_id": plate_id,
            "column_name": column_name,
            "question": question,
            "model_version": model_version,
        }
        if image_keys:
            body["image_keys"] = image_keys
        return self._data(self._post("knowledge-extraction/columns/add", body))

    def get_ke_job(self, job_id: str) -> dict:
        return self._data(self._get(f"knowledge-extraction/jobs/{job_id}"))

    def wait_for_ke_job(self, job_id: str, interval: int = 10, max_wait: int = 1800) -> dict:
        terminal = {"completed", "failed"}
        start = time.time()
        while True:
            status = self.get_ke_job(job_id)
            st = status.get("status", "unknown")
            print(f"KE job: {st}")
            if st in terminal:
                return status
            if time.time() - start > max_wait:
                raise TimeoutError("KE job timed out")
            time.sleep(interval)

    def ke_chat_query(
        self,
        collection_id: str,
        plate_id: str,
        message: str,
        session_id: str | None = None,
        aggregate_segments: bool = False,
    ) -> dict:
        body: dict = {
            "collection_id": collection_id,
            "plate_id": plate_id,
            "message": message,
            "aggregate_segments": aggregate_segments,
        }
        if session_id:
            body["session_id"] = session_id
        return self._data(self._post("knowledge-extraction/chat/query", body))

    # ─── Agentic Chat ─────────────────────────────────────────────────────────

    def create_chat_session(self, collection_id: str, name: str = "") -> dict:
        return self._data(self._post("agentic-chat/sessions", {
            "collection_id": collection_id,
            "session_name": name,
        }))

    def list_chat_sessions(self) -> list[dict]:
        return self._data(self._get("agentic-chat/sessions"))

    def get_chat_session(self, session_id: str) -> dict:
        return self._data(self._get(f"agentic-chat/sessions/{session_id}"))

    def get_session_status(self, session_id: str) -> dict:
        return self._data(self._get(f"agentic-chat/sessions/{session_id}/status"))

    def get_messages(self, session_id: str) -> list[dict]:
        return self._data(self._get(f"agentic-chat/sessions/{session_id}/messages"))

    def stop_session(self, session_id: str) -> dict:
        return self._data(self._post(f"agentic-chat/sessions/{session_id}/stop"))

    def send_search_feedback(self, session_id: str, feedback: str) -> dict:
        return self._data(self._post(f"agentic-chat/sessions/{session_id}/search-feedback", {"feedback": feedback}))

    def delete_chat_session(self, session_id: str) -> dict:
        return self._data(self._delete(f"agentic-chat/sessions/{session_id}"))

    def chat_stream(
        self,
        session_id: str,
        collection_id: str,
        message: str = "",
    ) -> Iterator[dict]:
        """
        Send a message and yield parsed SSE events.
        Pass message="" to reconnect to an already-running task.
        """
        url = self._url(f"agentic-chat/sessions/{session_id}/chat")
        resp = self.session.post(
            url,
            json={"message": message, "collection_id": collection_id},
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=None,
        )
        resp.raise_for_status()
        event_type = None
        for line in resp.iter_lines():
            if isinstance(line, bytes):
                line = line.decode()
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                raw = line[5:].strip()
                if raw == "[DONE]":
                    break
                try:
                    yield {"event": event_type, "data": json.loads(raw)}
                except json.JSONDecodeError:
                    yield {"event": event_type, "data": raw}

    # ─── Live Streaming ───────────────────────────────────────────────────────

    def start_live_stream(
        self,
        collection_id: str,
        source_url: str,
        name: str = "",
        protocol: str | None = None,
        periodic_indexing: int | None = None,
    ) -> dict:
        """
        protocol: None (auto-detect) | "rtsp" | "rtmp" | "srt" | "hls" | "webrtc" | "youtube"
        periodic_indexing: auto-index every N minutes (None to disable)
        """
        endpoint = f"live-stream/stream/{protocol}" if protocol else "live-stream/stream"
        body: dict = {"collection_id": collection_id, "source_url": source_url, "name": name}
        if periodic_indexing is not None:
            body["periodic_indexing"] = periodic_indexing
        return self._data(self._post(endpoint, body))

    def stop_live_stream(self, session_id: str) -> dict:
        return self._data(self._post(f"live-stream/sessions/{session_id}/stop"))

    def get_mediamtx_health(self) -> dict:
        return self._data(self._get("live-stream/mediamtx/health"))

    # ─── Online Search ────────────────────────────────────────────────────────

    def online_search(self, collection_id: str, query: str) -> dict:
        """Start a YouTube discovery job (server-side). Returns job_id."""
        return self._data(self._post("online-search/search", {
            "collection_id": collection_id,
            "query": query,
        }))

    def get_online_search_status(self, job_id: str) -> dict:
        return self._data(self._get(f"online-search/{job_id}/status"))

    def get_online_search_candidates(self, job_id: str) -> list[dict]:
        return self._data(self._get(f"online-search/{job_id}/candidates"))

    def confirm_online_search(self, job_id: str, collection_id: str) -> dict:
        return self._data(self._post(f"online-search/{job_id}/confirm", {"collection_id": collection_id}))

    def wait_for_online_search(self, job_id: str, interval: int = 10, max_wait: int = 600) -> dict:
        terminal = {"completed", "failed", "indexing_completed", "indexing_failed"}
        start = time.time()
        while True:
            status = self.get_online_search_status(job_id)
            st = status.get("status", "unknown")
            print(f"Online search: {st}")
            if st in terminal:
                return status
            if time.time() - start > max_wait:
                raise TimeoutError("Online search timed out")
            time.sleep(interval)

    # ─── Sharing ─────────────────────────────────────────────────────────────

    def invite_member(
        self,
        collection_id: str,
        email: str,
        role: str,
        plate_access: str = "all",
        plate_permissions: dict | None = None,
        groups: list[str] | None = None,
    ) -> dict:
        body: dict = {
            "collection_id": collection_id,
            "target_email": email,
            "role": role,
            "plate_access": plate_access,
        }
        if plate_permissions:
            body["plate_permissions"] = plate_permissions
        if groups:
            body["groups"] = groups
        return self._data(self._post("sharing/invite", body))

    def list_members(self, collection_id: str) -> list[dict]:
        return self._data(self._post("sharing/members", {"collection_id": collection_id}))

    def remove_member(self, collection_id: str, email: str) -> dict:
        return self._data(self._post("sharing/members/remove", {
            "collection_id": collection_id,
            "target_email": email,
        }))
