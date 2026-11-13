"""Import a consistent, private runtime backup into the dedicated MARSENSE PostgreSQL DB."""

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.engine import make_url

from backend.auth import User
from backend.cloud_assets import CLOUD_LIMIT, put_asset, read_asset, validate_name
from backend.store import SCHEMA_VERSION, EntityRow, Store

PROJECT_REF = "knfvcyujieelulhswkxg"
WORKSPACE = re.compile(r"account-([a-f0-9]{32})")


@dataclass
class Snapshot:
    schema: str
    rows: dict[str, tuple[str, dict[str, Any]]]
    assets: dict[str, bytes]


def read_snapshot(path: Path, schema: str) -> Snapshot:
    if not path.is_file():
        raise ValueError("Required backup database is missing")
    # SQLite WAL recovery can require writable sidecars, even for a read-only query.
    # Copy the quiesced backup and WAL to private temporary storage; never modify source.
    with tempfile.TemporaryDirectory(prefix="marsense-migration-") as directory:
        local = Path(directory) / path.name
        shutil.copyfile(path, local)
        wal = path.with_name(path.name + "-wal")
        if wal.is_file():
            shutil.copyfile(wal, local.with_name(local.name + "-wal"))
        with sqlite3.connect(local) as db:
            if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("SQLite backup integrity check failed")
            if db.execute("SELECT version FROM schema_version WHERE id=1").fetchone() != (
                SCHEMA_VERSION,
            ):
                raise ValueError("Only a verified version-2 source backup can be imported")
            rows = {}
            for ident, kind, raw in db.execute("SELECT id,kind,payload FROM entities"):
                payload = json.loads(raw)
                if not isinstance(payload, dict) or payload.get("id") != ident:
                    raise ValueError("Invalid source entity identity")
                rows[ident] = (kind, payload)
    assets = {}
    if schema != "marsense_accounts":
        for folder, suffix in (("uploads", ".jpg"), ("originals", ".bin")):
            for asset in (path.parent / folder).glob("*"):
                if not asset.is_file() or not asset.name.endswith(suffix):
                    raise ValueError("Unexpected file in source evidence directory")
                validate_name(asset.name)
                assets[asset.name] = asset.read_bytes()
        for kind, payload in rows.values():
            if kind != "Observation":
                continue
            name = str(payload.get("raw_asset_reference", "")).rsplit("/", 1)[-1]
            if not name.startswith("upload-"):
                continue
            validate_name(name)
            if name not in assets:
                raise ValueError("A source observation is missing its derivative image")
            expected = payload.get("model_input_sha256")
            if expected and hashlib.sha256(assets[name]).hexdigest() != expected:
                raise ValueError("Source derivative image hash mismatch")
            if payload.get("original_asset_reference"):
                original = assets.get(name.replace(".jpg", ".bin"))
                if original is None or hashlib.sha256(original).hexdigest() != payload.get(
                    "asset_sha256"
                ):
                    raise ValueError("Source original image hash mismatch")
    return Snapshot(schema, rows, assets)


def read_runtime(runtime: Path) -> list[Snapshot]:
    result = [read_snapshot(runtime / "marsense.db", "marsense")]
    if not any(kind == "Mission" for kind, _ in result[0].rows.values()):
        raise ValueError("Source production snapshot has no missions")
    root = runtime / "personal_workspaces"
    accounts = root / "accounts.db"
    if accounts.is_file():
        result.append(read_snapshot(accounts, "marsense_accounts"))
        account_ids = {
            ident for ident, (kind, _) in result[-1].rows.items()
            if kind == "RegisteredAccount"
        }
    else:
        account_ids = set()
    if root.is_dir():
        for directory in sorted(root.iterdir()):
            if not directory.is_dir():
                continue
            match = WORKSPACE.fullmatch(directory.name)
            if not match or directory.name not in account_ids:
                raise ValueError("Unrecognized or orphan personal workspace in backup")
            result.append(read_snapshot(directory / "mission.db", "marsense_ws_" + match[1]))
    if sum(len(data) for item in result for data in item.assets.values()) > CLOUD_LIMIT:
        raise ValueError("Backup exceeds the initial cloud evidence storage budget")
    return result


def read_users(path: Path) -> dict[str, dict[str, Any]]:
    users = [User.model_validate(item) for item in json.loads(path.read_text(encoding="utf-8"))]
    if not users or len({u.id for u in users}) != len(users) or len(
        {u.username.casefold() for u in users}
    ) != len(users):
        raise ValueError("Bootstrap identities are missing or duplicated")
    for user in users:
        if not re.fullmatch(r"scrypt\$131072\$8\$1\$[0-9a-f]{32}\$[0-9a-f]{128}",
                            user.password_hash):
            raise ValueError("Invalid bootstrap password hash")
    return {u.id: u.model_dump(mode="json") for u in users}


def sync_snapshot(
    url: str, item: Snapshot, users: dict[str, dict[str, Any]] | None = None,
    *, verify_only: bool = False,
) -> None:
    store = Store(url, item.schema)
    if not store.postgres:
        store.engine.dispose()
        raise ValueError("Migration destination must be PostgreSQL")
    try:
        with store.session(write=True) as session:
            existing = {
                row.id: (row.kind, row.payload) for row in session.scalars(select(EntityRow))
            }
            if any(ident not in item.rows or item.rows[ident] != row
                   for ident, row in existing.items()):
                raise ValueError(
                    "Destination contains different mission records; refusing overwrite"
                )
            names = set(session.scalars(text(
                "SELECT name FROM marsense.asset_blobs WHERE namespace=:namespace"
            ), {"namespace": item.schema}))
            if names - item.assets.keys():
                raise ValueError("Destination contains additional assets; refusing overwrite")
            for name in names:
                if read_asset(session, item.schema, name) != item.assets[name]:
                    raise ValueError("Destination asset differs from source")
            if users is not None:
                stored = dict(session.execute(text(
                    "SELECT id,payload FROM marsense.bootstrap_users"
                )).tuples().all())
                if any(ident not in users or users[ident] != payload
                       for ident, payload in stored.items()):
                    raise ValueError("Destination bootstrap identity differs; refusing overwrite")
            else:
                stored = {}
            if verify_only and (
                existing != item.rows or names != set(item.assets)
                or (users is not None and stored != users)
            ):
                raise ValueError("Destination is not an exact verified copy")
            if not verify_only:
                for ident, (kind, payload) in item.rows.items():
                    if ident not in existing:
                        session.add(EntityRow(id=ident, kind=kind, payload=payload))
                for name, data in item.assets.items():
                    if name not in names:
                        put_asset(session, item.schema, name, data)
                if users is not None:
                    for ident, payload in users.items():
                        if ident not in stored:
                            session.execute(text(
                                "INSERT INTO marsense.bootstrap_users(id,payload) "
                                "VALUES (:id,CAST(:payload AS json))"
                            ), {"id": ident, "payload": json.dumps(payload)})
                session.flush()
                current = {
                    row.id: (row.kind, row.payload) for row in session.scalars(select(EntityRow))
                }
                if current != item.rows:
                    raise ValueError("Record comparison failed; transaction rolled back")
                for name, content in item.assets.items():
                    if read_asset(session, item.schema, name) != content:
                        raise ValueError("Asset comparison failed; transaction rolled back")
                if users is not None and dict(session.execute(text(
                    "SELECT id,payload FROM marsense.bootstrap_users"
                )).tuples().all()) != users:
                    raise ValueError("Identity comparison failed; transaction rolled back")
    finally:
        store.engine.dispose()


def validate_destination(url: str) -> None:
    parsed = make_url(url)
    direct = parsed.host == f"db.{PROJECT_REF}.supabase.co" and parsed.username == "postgres"
    pooled = (
        bool(parsed.host and parsed.host.endswith(".pooler.supabase.com"))
        and bool(parsed.username and parsed.username.endswith("." + PROJECT_REF))
    )
    if not (direct or pooled) or parsed.database != "postgres" or parsed.port != 5432:
        raise ValueError("Use this MARSENSE project's direct or session-pooler connection")
    if parsed.get_backend_name() != "postgresql":
        raise ValueError("Migration destination must be PostgreSQL")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--users", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    snapshots = read_runtime(args.runtime)
    users = read_users(args.users)
    for item in snapshots:
        print(f"{item.schema}: {len(item.rows)} records, {len(item.assets)} assets")
    print(f"Private operator identities: {len(users)}")
    if not (args.apply or args.verify):
        print("SOURCE VERIFIED. Dry run only; destination untouched.")
        return
    url = os.environ.get("MARSENSE_DATABASE_URL", "")
    validate_destination(url)
    for item in snapshots:
        sync_snapshot(
            url, item, users if item.schema == "marsense" else None, verify_only=args.verify,
        )
    for item in snapshots:
        sync_snapshot(url, item, users if item.schema == "marsense" else None, verify_only=True)
    print("CLOUD RECORD, ASSET AND IDENTITY COMPARISON PASSED. No source data changed.")


if __name__ == "__main__":
    main()
