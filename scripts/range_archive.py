"""Seekable, capped HTTP-range reader for bounded official scientific ZIP subsets."""

import hashlib
import io
import urllib.request
from pathlib import Path
from urllib.error import URLError


class RangeArchive(io.RawIOBase):
    def __init__(self, url: str, size: int, cache: Path, budget: int = 64 * 1024 * 1024):
        super().__init__()
        self.url, self.size, self.cache, self.budget = url, size, cache, budget
        self.position = 0
        self.requested_bytes = 0
        self.ranges: list[dict[str, object]] = []
        cache.mkdir(parents=True, exist_ok=True)

    def seekable(self) -> bool:
        return True

    def readable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = 0) -> int:
        position = (
            offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        )
        if whence not in (0, 1, 2) or not 0 <= position <= self.size:
            raise ValueError("Invalid archive seek")
        self.position = position
        return position

    def read(self, size: int = -1) -> bytes:
        remaining = self.size - self.position if size < 0 else min(size, self.size - self.position)
        if self.requested_bytes + remaining > self.budget:
            raise ValueError("Archive range budget exceeded; refusing whole archive")
        result = bytearray()
        while remaining:
            length = min(remaining, 1024 * 1024)
            start = self.position
            name = f"{start}-{length}.bin"
            path = self.cache / name
            if path.exists():
                content = path.read_bytes()
            else:
                request = urllib.request.Request(
                    self.url,
                    headers={
                        "Range": f"bytes={start}-{start + length - 1}",
                        "Cache-Control": "no-cache",
                    },
                )
                content = b""
                for attempt in range(3):
                    try:
                        with urllib.request.urlopen(request, timeout=30) as response:
                            expected = f"bytes {start}-{start + length - 1}/{self.size}"
                            if (
                                response.status != 206
                                or response.headers.get("Content-Range") != expected
                            ):
                                raise ValueError(
                                    "Server refused exact range; full download is prohibited"
                                )
                            content = response.read(length + 1)
                        if len(content) == length:
                            break
                    except (URLError, TimeoutError):
                        if attempt == 2:
                            raise
                if len(content) != length:
                    raise ValueError("Truncated archive range")
                temporary = path.with_suffix(".partial")
                temporary.write_bytes(content)
                temporary.replace(path)
            if len(content) != length:
                raise ValueError("Invalid cached archive range")
            self.ranges.append(
                {
                    "offset": start,
                    "length": length,
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            )
            self.requested_bytes += length
            self.position += length
            remaining -= length
            result.extend(content)
        return bytes(result)
