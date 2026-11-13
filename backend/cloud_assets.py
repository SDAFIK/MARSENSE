"""Server-only Supabase private asset access, scoped by verified workspace identity."""
import logging
import re
from typing import Any

import httpx
from fastapi import HTTPException

from backend.config import Settings

logger = logging.getLogger(__name__)
_NAMESPACE = re.compile(r"(?:operator|user-[a-f0-9]{32})")
_ASSET = re.compile(r"upload-[a-f0-9]{32}\.(?:jpg|bin)")


class CloudAssets:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        key = settings.cloud_storage_key.get_secret_value()
        headers = {"apikey": key}
        if not key.startswith("sb_secret_"):
            headers["Authorization"] = f"Bearer {key}"
        self.client = httpx.Client(
            base_url=settings.cloud_supabase_url.rstrip("/") + "/storage/v1/",
            headers=headers, timeout=30, follow_redirects=False, transport=transport,
        )
        self.bucket = settings.cloud_storage_bucket

    def close(self) -> None:
        self.client.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            return self.client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise HTTPException(503, "Private image storage is unavailable") from exc

    def verify_private_bucket(self) -> None:
        response = self._request("GET", f"bucket/{self.bucket}")
        if not response.is_success or response.json().get("public") is not False:
            raise RuntimeError("Dedicated private MARSENSE storage bucket is required")

    @staticmethod
    def _path(namespace: str, kind: str, name: str) -> str:
        if (not _NAMESPACE.fullmatch(namespace) or kind not in {"uploads", "originals"}
                or not _ASSET.fullmatch(name)
                or not name.endswith(".jpg" if kind == "uploads" else ".bin")):
            raise HTTPException(404, "Private image not found")
        return f"{namespace}/{kind}/{name}"

    def read(self, namespace: str, kind: str, name: str) -> bytes:
        path = self._path(namespace, kind, name)
        response = self._request("GET", f"object/authenticated/{self.bucket}/{path}")
        if response.status_code in (400, 404):
            raise HTTPException(404, "Saved image unavailable; evidence retained")
        if not response.is_success:
            raise HTTPException(503, "Private image storage is unavailable")
        return response.content

    def _put(self, path: str, content: bytes, mime: str) -> None:
        response = self._request("POST", f"object/{self.bucket}/{path}",
                                 content=content, headers={"Content-Type": mime, "x-upsert": "false"})
        if not response.is_success:
            raise HTTPException(503, "Image could not be stored; no evidence was recorded")

    def _remove(self, paths: list[str]) -> None:
        try:
            response = self._request("DELETE", f"object/{self.bucket}", json={"prefixes": paths})
            if not response.is_success:
                logger.warning("cloud_asset_cleanup_failed")
        except HTTPException:
            logger.warning("cloud_asset_cleanup_unavailable")

    def write_pair(self, namespace: str, name: str, original: bytes, derivative: bytes) -> None:
        a = self._path(namespace, "originals", name.replace(".jpg", ".bin"))
        b = self._path(namespace, "uploads", name)
        self._put(a, original, "application/octet-stream")
        try:
            self._put(b, derivative, "image/jpeg")
        except Exception:
            self._remove([a])
            raise

    def remove_pair(self, namespace: str, name: str) -> None:
        self._remove([self._path(namespace, "originals", name.replace(".jpg", ".bin")),
                      self._path(namespace, "uploads", name)])

    def ensure_quota(self, namespace: str, incoming: int) -> None:
        if not _NAMESPACE.fullmatch(namespace):
            raise HTTPException(404, "Workspace not found")
        size = 0
        count = 0
        for kind in ("originals", "uploads"):
            response = self._request("POST", f"object/list/{self.bucket}",
                                     json={"prefix": f"{namespace}/{kind}", "limit": 100, "offset": 0})
            if not response.is_success:
                raise HTTPException(503, "Storage quota could not be checked")
            items = response.json()
            if not isinstance(items, list) or len(items) >= 100:
                raise HTTPException(413, "Private storage quota reached")
            for item in items:
                metadata = item.get("metadata") or {}
                length = metadata.get("size")
                if not isinstance(length, int) or length < 0:
                    raise HTTPException(503, "Storage quota could not be checked")
                size += length
            if kind == "originals":
                count = len(items)
        if count >= 16 or size + incoming > 64 * 1024 * 1024:
            raise HTTPException(413, "Private workspace storage limit reached (16 images / 64 MB)")
