import io
from pathlib import Path

import pytest

from scripts.range_archive import RangeArchive


def test_range_reader_refuses_whole_archive_fallback(tmp_path: Path, monkeypatch) -> None:
    class Response(io.BytesIO):
        status = 200
        headers: dict[str, str] = {}

    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: Response(b"unsafe"))
    reader = RangeArchive("https://example.test/archive", 100, tmp_path)
    with pytest.raises(ValueError, match="exact range"):
        reader.read(10)
    assert not list(tmp_path.iterdir())


def test_range_reader_checks_budget_and_cached_length(tmp_path: Path) -> None:
    reader = RangeArchive("https://example.test/archive", 100, tmp_path, budget=10)
    with pytest.raises(ValueError, match="budget"):
        reader.read(11)
    (tmp_path / "0-10.bin").write_bytes(b"short")
    with pytest.raises(ValueError, match="cached"):
        reader.read(10)


def test_range_reader_retries_truncation_but_only_caches_complete_bytes(tmp_path, monkeypatch):
    calls = []

    class Response(io.BytesIO):
        status = 206
        headers = {"Content-Range": "bytes 0-9/100"}

    def respond(*args, **kwargs):
        calls.append(1)
        return Response(b"short" if len(calls) < 3 else b"0123456789")

    monkeypatch.setattr("urllib.request.urlopen", respond)
    reader = RangeArchive("https://example.test/archive", 100, tmp_path)
    assert reader.read(10) == b"0123456789"
    assert len(calls) == 3
    assert (tmp_path / "0-10.bin").read_bytes() == b"0123456789"
