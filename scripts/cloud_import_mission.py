"""Explicit SQLite -> isolated PostgreSQL mission transfer; no source writes."""
import argparse
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from sqlalchemy import select

from backend.cloud_store import CloudStore
from backend.store import EntityRow, SCHEMA_VERSION

# Active login sessions and account secrets are not migrated into mission data.
_EXCLUDED = {"AuthSession", "RegisteredAccount", "RegistrationInvite", "AuthAudit"}


def read_mission_rows(path: Path) -> dict[str, tuple[str, dict[str, Any]]]:
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as source:
        if source.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Source SQLite integrity check failed")
        if source.execute("SELECT version FROM schema_version WHERE id=1").fetchone() != (SCHEMA_VERSION,):
            raise ValueError("Unsupported source schema; migrate a disposable copy first")
        rows = {
            ident: (kind, json.loads(payload))
            for ident, kind, payload in source.execute("SELECT id, kind, payload FROM entities")
            if kind not in _EXCLUDED
        }
    if not rows:
        raise ValueError("No mission records to import")
    return rows


def import_mission(store: CloudStore, rows: dict[str, tuple[str, dict[str, Any]]]) -> None:
    with store.session(write=True) as session:
        if session.scalar(select(EntityRow.id).limit(1)) is not None:
            raise ValueError("Target namespace is not empty; refusing overwrite")
        for ident, (kind, payload) in rows.items():
            session.add(EntityRow(id=ident, kind=kind, payload=payload))
        session.flush()
        written = {
            row.id: (row.kind, row.payload) for row in session.scalars(select(EntityRow))
        }
        if written != rows:
            raise ValueError("Record comparison failed; target transaction rolled back")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--apply", action="store_true", help="Write to empty cloud namespace")
    args = parser.parse_args()
    rows = read_mission_rows(args.source)
    print("Source integrity verified; mission records:", len(rows))
    if not args.apply:
        print("DRY RUN: no cloud writes performed")
        return
    url = os.environ["MARSENSE_CLOUD_DATABASE_URL"]
    store = CloudStore(url, args.schema)
    try:
        import_mission(store, rows)
        print("MISSION RECORD IMPORT AND COMPARISON PASSED", len(rows))
    finally:
        store.close()


if __name__ == "__main__":
    main()
