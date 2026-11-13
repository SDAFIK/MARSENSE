"""Postgres persistence adapter for an isolated MARSENSE namespace.

Enabled only by explicit cloud configuration. Local SQLite remains supported.
"""
from collections.abc import Iterator
from contextlib import contextmanager
import re

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import Engine, URL, make_url
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema

from backend.store import Base, SCHEMA_VERSION, SchemaVersion

_SCHEMA = re.compile(r"marsense_[a-z0-9_]{1,48}")


def create_cloud_engine(url: str) -> Engine:
    parsed: URL = make_url(url)
    if parsed.get_backend_name() != "postgresql":
        raise ValueError("CloudStore requires PostgreSQL")
    return create_engine(
        parsed.set(drivername="postgresql+psycopg"),
        pool_size=2, max_overflow=2, pool_pre_ping=True,
        pool_recycle=300, hide_parameters=True,
    )


class CloudStore:
    """Same entity/session contract as Store, with namespaced tables and write locks."""

    def __init__(self, url: str, schema: str, shared_engine: Engine | None = None):
        if not _SCHEMA.fullmatch(schema):
            raise ValueError("Use a dedicated marsense_ schema")
        self.schema = schema
        self._owns_engine = shared_engine is None
        self.engine = (shared_engine or create_cloud_engine(url)).execution_options(
            schema_translate_map={None: schema}
        )
        try:
            with self.engine.begin() as connection:
                connection.execute(
                    text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
                    {"scope": schema},
                )
                connection.execute(CreateSchema(schema, if_not_exists=True))
                has_version = inspect(connection).has_table("schema_version", schema=schema)
                version = (
                    connection.scalar(select(SchemaVersion.version).where(SchemaVersion.id == 1))
                    if has_version else SCHEMA_VERSION
                )
                if version != SCHEMA_VERSION:
                    raise ValueError("Cloud schema version mismatch; explicit migration required")
                Base.metadata.create_all(connection)
                # Private namespaces must not be granted through the public Data API.
                connection.execute(text(f'REVOKE ALL ON SCHEMA "{schema}" FROM PUBLIC'))
                connection.execute(text(f'REVOKE ALL ON ALL TABLES IN SCHEMA "{schema}" FROM PUBLIC'))
                with Session(bind=connection) as session:
                    if session.get(SchemaVersion, 1) is None:
                        session.add(SchemaVersion(id=1, version=SCHEMA_VERSION))
                    session.flush()
        except Exception:
            self.close()
            raise

    @contextmanager
    def session(self, write: bool = False) -> Iterator[Session]:
        with Session(self.engine) as session:
            try:
                if write:
                    # Serialize writes within one mission namespace across worker processes.
                    session.execute(
                        text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
                        {"scope": self.schema},
                    )
                yield session
                if write:
                    session.commit()
            except Exception:
                session.rollback()
                raise

    def close(self) -> None:
        if self._owns_engine:
            self.engine.dispose()
