"""Private, transaction-bound cloud evidence bytes; never exposed through PostgREST."""

import hashlib
import re
from typing import cast

from sqlalchemy import text
from sqlalchemy.orm import Session

# Bounded prototype capacity: preserve room for JSON mission records and database overhead.
WORKSPACE_LIMIT = 64 * 1024 * 1024
CLOUD_LIMIT = 200 * 1024 * 1024
MAX_UPLOADS = 16
_NAME = re.compile(r"upload-[a-f0-9]{32}\.(?:jpg|bin)")


def validate_name(name: str) -> None:
    if not _NAME.fullmatch(name):
        raise ValueError("Invalid private evidence asset name")


def read_asset(session: Session, namespace: str, name: str) -> bytes | None:
    validate_name(name)
    row = session.execute(text("""
        SELECT content, sha256, byte_count
        FROM marsense.asset_blobs WHERE namespace=:namespace AND name=:name
    """), {"namespace": namespace, "name": name}).one_or_none()
    if row is None:
        return None
    content = bytes(row.content)
    if len(content) != row.byte_count or hashlib.sha256(content).hexdigest() != row.sha256:
        raise ValueError("Cloud evidence integrity check failed")
    return content


def enforce_cloud_quota(session: Session, namespace: str, incoming: int) -> None:
    # All namespaces serialize quota checks; evidence and assets commit together.
    session.execute(text("SELECT pg_advisory_xact_lock(788201426193)"))
    total = session.scalar(text("SELECT coalesce(sum(byte_count),0) FROM marsense.asset_blobs"))
    used, uploads = cast(tuple[int, int], session.execute(text("""
        SELECT coalesce(sum(byte_count),0), count(*) FILTER (WHERE name LIKE '%.bin')
        FROM marsense.asset_blobs WHERE namespace=:namespace
    """), {"namespace": namespace}).one())
    if (
        int(total or 0) + incoming > CLOUD_LIMIT
        or (namespace != "marsense" and (
            used + incoming > WORKSPACE_LIMIT or uploads >= MAX_UPLOADS
        ))
    ):
        raise ValueError("Cloud evidence storage quota reached")


def put_asset(session: Session, namespace: str, name: str, content: bytes) -> None:
    validate_name(name)
    digest = hashlib.sha256(content).hexdigest()
    existing = read_asset(session, namespace, name)
    if existing is not None:
        if existing != content:
            raise ValueError("Existing cloud evidence is immutable")
        return
    session.execute(text("""
        INSERT INTO marsense.asset_blobs(namespace,name,content,sha256,byte_count)
        VALUES (:namespace,:name,:content,:sha256,:byte_count)
    """), {
        "namespace": namespace, "name": name, "content": content,
        "sha256": digest, "byte_count": len(content),
    })
