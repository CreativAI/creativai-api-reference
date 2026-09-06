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

    def get_me(self) -> dict:
        return self._data(self._get("users/get_users_info"))

    # ─── Collections ─────────────────────────────────────────────────────────

    def create_collection(
        self,
        name: str,
        description: str = "",
        model: str = "video_only",
    ) -> dict:
        """
        model: "video_only" (Video-Only) | "multimodal" (Multimodal, video + images)
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

    _PART_SIZE = 25 * 1024 * 1024  # 25 MB per multipart part

    def get_upload_url(self, collection_id: str, filename: str, content_type: str = "video/mp4") -> dict:
        return self._data(self._post(f"collections/{collection_id}/upload-url", {
            "filename": filename,
            "content_type": content_type,
        }))

    def get_upload_urls(self, collection_id: str, files: list[dict]) -> list[dict]:
        """files: [{"filename": "...", "content_type": "..."}]"""
        return self._data(self._post(f"collections/{collection_id}/upload-urls", {"files": files}))

    def initiate_multipart_upload(
        self,
        collection_id: str,
        filename: str,
        file_size: int,
        content_type: str = "video/mp4",
    ) -> dict:
        """
        Initiate a multipart upload.
        Returns the first item of uploads[] — contains upload_id, presigned_urls, part_size, s3_key.
        """
        resp = self._data(self._post("collections/uploads/initiate", {
            "collection_id": collection_id,
            "files": [{"filename": filename, "file_size": file_size, "content_type": content_type}],
        }))
        uploads = resp.get("uploads", [])
        return uploads[0] if uploads else resp

    def complete_multipart_upload(self, upload_id: str, parts: list[dict]) -> dict:
        """
        Complete a multipart upload after all parts have been PUT.
        parts: [{"part_number": int, "etag": str}]
        Triggers preprocessing automatically.
        """
        return self._data(self._post(f"collections/uploads/{upload_id}/complete", {
            "parts": parts,
        }))

    def upload_file(self, collection_id: str, file_path: str | Path) -> str:
        """
        Upload a local file via the multipart upload API.
        Flow: initiate → PUT each part → complete (triggers preprocessing).
        Returns the S3 URI of the uploaded file.
        """
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        content_type = "video/mp4" if ext in (".mp4", ".mov", ".avi", ".mkv", ".webm") else "image/jpeg"
        file_size = file_path.stat().st_size

        # Step 1 — Initiate: get upload_id + presigned part URLs
        upload_info = self.initiate_multipart_upload(
            collection_id, file_path.name, file_size, content_type
        )
        upload_id     = upload_info["upload_id"]
        presigned_urls = upload_info["presigned_urls"]
        part_size      = upload_info.get("part_size", self._PART_SIZE)
        s3_key         = upload_info.get("s3_key", "")

        # Step 2 — PUT each chunk to its presigned S3 URL
        parts: list[dict] = []
        with open(file_path, "rb") as f:
            for i, url_entry in enumerate(presigned_urls, 1):
                # presigned_urls may be plain strings or {"url": ..., "part_number": ...} dicts
                url = url_entry.get("url") if isinstance(url_entry, dict) else url_entry
                chunk = f.read(part_size)
                if not chunk:
                    break
                put_resp = requests.put(url, data=chunk)
                put_resp.raise_for_status()
                etag = put_resp.headers.get("ETag", "").strip('"')
                parts.append({"part_number": i, "etag": etag})

        # Step 3 — Complete: finalize on S3, triggers Lambda preprocessing
        self.complete_multipart_upload(upload_id, parts)

        # Derive the S3 URI from the upload info
        if s3_key:
            # Extract bucket from first presigned URL (https://<bucket>.s3.amazonaws.com/...)
            first_url = (
                presigned_urls[0].get("url")
                if isinstance(presigned_urls[0], dict)
                else presigned_urls[0]
            )
            bucket = first_url.split("/")[2].split(".s3.")[0]
            return f"s3://{bucket}/{s3_key}"
        return upload_info.get("s3_uri", file_path.name)

    def list_media(self, collection_id: str) -> list[dict]:
        return self._data(self._get(f"collections/{collection_id}/media"))

    # ─── Confirm upload (registers media, kicks off preprocessing) ───────────

    def confirm_upload(
        self,
        collection_id: str,
        media_ids: list[str],
        tags: dict[str, list[str]] | None = None,
        metadata: dict[str, dict[str, dict]] | None = None,
        metadata_schema: dict[str, dict] | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        """Async: returns {job_id, status, poll_url}.

        tags:            {"s3://.../file.mp4": ["tag1"], "*": ["global"]}
        metadata:        {"s3://.../file.mp4": {"duration": {"datatype": "number", "value": 24.5}}, ...}
        metadata_schema: {"region": {"type": "enum", "values": ["eu", "us"]}}
        """
        body: dict = {"media_ids": media_ids}
        if tags:
            body["tags"] = tags
        if metadata:
            body["metadata"] = metadata
        if metadata_schema:
            body["metadata_schema"] = metadata_schema
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else {}
        return self._data(self._post(
            f"collections/{collection_id}/confirm-upload", body, headers=headers,
        ))

    def get_confirm_upload_job(self, collection_id: str, job_id: str) -> dict:
        return self._data(self._get(f"collections/{collection_id}/confirm-upload/jobs/{job_id}"))

    # ─── Tags ────────────────────────────────────────────────────────────────

    def list_collection_tags(self, collection_id: str) -> dict:
        """Returns {tags: [...], tag_counts: {...}}."""
        return self._data(self._get(f"collections/{collection_id}/tags"))

    def update_collection_tags(
        self,
        collection_id: str,
        add: list[str] | None = None,
        remove: list[str] | None = None,
        media_ids: list[str] | None = None,
        all_media: bool = False,
    ) -> dict:
        """Async: rewrites every chunk row of the affected media. Returns {job_id, status, progress}."""
        body: dict = {}
        if add:       body["add"] = add
        if remove:    body["remove"] = remove
        if media_ids: body["media_ids"] = media_ids
        if all_media: body["all_media"] = True
        return self._data(self._post(f"collections/{collection_id}/tags", body))

    def get_tag_update_job(self, collection_id: str, job_id: str) -> dict:
        return self._data(self._get(f"collections/{collection_id}/tags/jobs/{job_id}"))

    # ─── Metadata schema + updates ───────────────────────────────────────────

    def get_metadata_schema(self, collection_id: str) -> dict:
        """The collection's learned metadata registry (types, known values, ranges, counts)."""
        return self._data(self._get(f"collections/{collection_id}/metadata-schema"))

    def declare_metadata_enums(
        self,
        collection_id: str,
        metadata_schema: dict[str, dict],
    ) -> dict:
        """Idempotent: only ever widens an enum's legal values."""
        return self._data(self._post(
            f"collections/{collection_id}/metadata-schema/enums",
            {"metadata_schema": metadata_schema},
        ))

    def update_collection_metadata(
        self,
        collection_id: str,
        set_values: dict[str, dict] | None = None,
        unset: list[str] | None = None,
        metadata_schema: dict[str, dict] | None = None,
        media_ids: list[str] | None = None,
        all_media: bool = False,
    ) -> dict:
        """Async: same {datatype, value} envelope as confirm_upload.

        set_values:      {"region": {"datatype": "enum", "value": "us"}, ...}
        metadata_schema: enum declarations applied before the delta
        """
        body: dict = {}
        if set_values:      body["set"] = set_values
        if unset:           body["unset"] = unset
        if metadata_schema: body["metadata_schema"] = metadata_schema
        if media_ids:       body["media_ids"] = media_ids
        if all_media:       body["all_media"] = True
        return self._data(self._post(f"collections/{collection_id}/metadata", body))

    def get_metadata_update_job(self, collection_id: str, job_id: str) -> dict:
        return self._data(self._get(f"collections/{collection_id}/metadata/jobs/{job_id}"))

    # ─── Indexing ─────────────────────────────────────────────────────────────

    def get_preprocessing_status(self, collection_id: str) -> dict:
        return self._data(self._get(f"indexing/preprocessing-status/{collection_id}"))

    def wait_for_preprocessing(self, collection_id: str, interval: int = 30, max_wait: int = 1800) -> dict:
        """Block until preprocessing is complete (can_start_indexing=True)."""
        start = time.time()
        while True:
            status = self.get_preprocessing_status(collection_id)
            pre_st = status.get('preprocessing_status', status.get('status', 'unknown'))
            print(f"Preprocessing: {pre_st} | can_start_indexing={status.get('can_start_indexing')}")
            if status.get("can_start_indexing"):
                return status
            if time.time() - start > max_wait:
                raise TimeoutError("Preprocessing timed out")
            time.sleep(interval)

    def start_indexing(
        self,
        collection_id: str,
        media_ids: list[str] | None = None,
    ) -> dict:
        """
        media_ids: optional list of specific media handles (S3 URIs) to index (None = index all preprocessed media)

        Tags are NOT accepted here. Declare them at upload time on
        POST /collections/{id}/confirm-upload, or change them on already-indexed
        media with the async job at POST /collections/{id}/tags.
        """
        body: dict = {"collection_id": collection_id}
        if media_ids:
            body["media_ids"] = media_ids
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
        video_key: str | None = None,
        tags: list[str] | None = None,
        meta_filter: dict | None = None,
        plan_metadata: bool = False,
        top_k: int = 50,
        search_type: str = "hybrid",
        search_id: str | None = None,
        page_number: int | None = None,
        page_size: int | None = None,
        min_score: float | None = None,
        include_scores: bool = False,
        score_bins: int | None = None,
    ) -> dict:
        """Submit a search.

        For a new search, this returns a **submitted** job envelope
        ``{search_job_id, poll_url, status: "submitted", ...}`` — call
        ``wait_for_search`` (or poll ``get_search_job``) for the first page.

        Paginating an existing ``search_id`` skips the async submit and returns
        the page directly (``status: "completed"``).

        tags:         restrict to media carrying at least one of these (OR semantics)
        meta_filter:  AST filter over typed metadata, e.g.
                        {"op": "and", "clauses": [{"key": "duration", "cmp": "<", "value": 30}]}
        plan_metadata: let an LLM split ``query`` into a visual half + metadata clauses
        """
        body: dict = {
            "collection_id": collection_id,
            "page_size": page_size if page_size is not None else top_k,
            "search_type": search_type,
            "page_number": page_number or 1,
        }
        if query:          body["text_query"] = query
        if image_base64:   body["image_base64"] = image_base64
        if image_key:      body["image_key"] = image_key
        if video_key:      body["video_key"] = video_key
        if tags:           body["tags"] = tags
        if meta_filter:    body["meta_filter"] = meta_filter
        if plan_metadata:  body["plan_metadata"] = True
        if search_id:      body["search_id"] = search_id
        if min_score is not None: body["min_score"] = min_score
        if include_scores: body["include_scores"] = True
        if score_bins:     body["score_bins"] = score_bins
        return self._data(self._post("search", body))

    def get_search_job(
        self,
        job_id: str,
        collection_id: str | None = None,
        page_number: int = 1,
        page_size: int = 100,
    ) -> dict:
        params = {"page_number": page_number, "page_size": page_size}
        if collection_id:
            params["collection_id"] = collection_id
        return self._data(self._get(f"search/jobs/{job_id}", params=params))

    def wait_for_search(
        self,
        job_id: str,
        collection_id: str | None = None,
        interval: float = 2.0,
        max_wait: int = 300,
    ) -> dict:
        """Poll a search job until completion. Returns the completed page."""
        terminal = {"completed", "failed"}
        start = time.time()
        while True:
            resp = self.get_search_job(job_id, collection_id=collection_id)
            st = resp.get("status", "unknown")
            if st in terminal:
                return resp
            if time.time() - start > max_wait:
                raise TimeoutError(f"Search job {job_id} timed out")
            time.sleep(interval)

    def search_and_wait(self, *args, **kwargs) -> dict:
        """Convenience: submit a search and block until the first page is ready."""
        submitted = self.search(*args, **kwargs)
        # A paginated request (search_id set) returns the page directly.
        if submitted.get("status") == "completed":
            return submitted
        job_id = submitted.get("search_job_id") or submitted.get("search_id")
        return self.wait_for_search(job_id, collection_id=kwargs.get("collection_id"))

    def search_with_image_file(self, collection_id: str, image_path: str | Path, **kwargs) -> dict:
        """Search using a local image file as the query (multimodal collections only)."""
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        return self.search(collection_id, image_base64=img_b64, **kwargs)

    # ─── Data Plates ─────────────────────────────────────────────────────────

    def create_plate(self, collection_id: str, name: str, search_id: str, top_k: int = 50) -> dict:
        return self._data(self._post("data-plates/create", {
            "collection_id": collection_id,
            "name": name,
            "search_id": search_id,
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
