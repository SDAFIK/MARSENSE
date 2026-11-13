import re
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import JSON, Integer, String, create_engine, event, inspect, select, text
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.pool import NullPool

from backend.domain import (
    Entity,
    Evidence,
    HumanDecision,
    Interpretation,
    Observation,
    Verification,
)


class Base(DeclarativeBase):
    pass


class EntityRow(Base):
    __tablename__ = "entities"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    kind: Mapped[str] = mapped_column(String(50), index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class SchemaVersion(Base):
    __tablename__ = "schema_version"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[int] = mapped_column(Integer)


SCHEMA_VERSION = 2


class Store:
    def __init__(self, url: str, schema: str = "marsense"):
        parsed = make_url(url)
        self.postgres = parsed.get_backend_name() == "postgresql"
        self.schema = schema
        if self.postgres:
            if not re.fullmatch(r"marsense(?:_accounts|_ws_[a-f0-9]{32})?", schema):
                raise ValueError("Invalid private MARSENSE schema")
            if parsed.drivername == "postgresql":
                parsed = parsed.set(drivername="postgresql+psycopg")
            if parsed.drivername != "postgresql+psycopg":
                raise ValueError("Cloud database requires psycopg")
            if parsed.query.get("sslmode", "require") not in {"require", "verify-ca", "verify-full"}:
                if parsed.host not in {"localhost", "127.0.0.1"}:
                    raise ValueError("Cloud database requires TLS")
            if "sslmode" not in parsed.query:
                parsed = parsed.update_query_dict({"sslmode": "require"})
            self.engine = create_engine(
                parsed, poolclass=NullPool, hide_parameters=True, connect_args={
                    "connect_timeout": 10, "prepare_threshold": None,
                },
            )
        elif parsed.get_backend_name() == "sqlite":
            self.engine = create_engine(
                parsed, connect_args={"check_same_thread": False, "timeout": 30}
            )

            @event.listens_for(self.engine, "connect")
            def configure(connection: Any, _: Any) -> None:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("PRAGMA foreign_keys=ON")
        else:
            raise ValueError("Unsupported database backend")

        try:
            with self.engine.begin() as connection:
                if self.postgres:
                    self._lock(connection)
                    connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"'))
                    self._scope(connection)
                    connection.execute(text(
                        f'REVOKE ALL ON SCHEMA "{self.schema}" '
                        "FROM PUBLIC, anon, authenticated, service_role"
                    ))
                else:
                    connection.execute(text("BEGIN IMMEDIATE"))
                version = (
                    connection.scalar(text("SELECT version FROM schema_version WHERE id=1"))
                    if inspect(connection).has_table(
                        "schema_version", schema=self.schema if self.postgres else None
                    )
                    else 1
                )
                if version is None or version > SCHEMA_VERSION:
                    raise ValueError("Database schema is newer or invalid; refusing migration")
                Base.metadata.create_all(connection)
                if self.postgres:
                    for table in ("entities", "schema_version"):
                        connection.execute(text(
                            f'ALTER TABLE "{self.schema}"."{table}" ENABLE ROW LEVEL SECURITY'
                        ))
                        connection.execute(text(
                            f'REVOKE ALL ON "{self.schema}"."{table}" '
                            "FROM PUBLIC, anon, authenticated, service_role"
                        ))
                    if self.schema == "marsense":
                        connection.execute(text("""
                            CREATE TABLE IF NOT EXISTS marsense.asset_blobs (
                                namespace varchar(63) NOT NULL,
                                name varchar(128) NOT NULL,
                                content bytea NOT NULL,
                                sha256 varchar(64) NOT NULL,
                                byte_count integer NOT NULL,
                                PRIMARY KEY (namespace, name),
                                CHECK (byte_count = octet_length(content)),
                                CHECK (sha256 ~ '^[0-9a-f]{64}
                    if version < 2:
                        from backend.migrations import migrate_legacy_segments

                        migrate_legacy_segments(session)
                    row = session.get(SchemaVersion, 1)
                    if row is None:
                        session.add(SchemaVersion(id=1, version=SCHEMA_VERSION))
                    else:
                        row.version = SCHEMA_VERSION
                    session.flush()
        except Exception:
            self.engine.dispose()
            raise

    def _scope(self, connection: Connection | Session) -> None:
        connection.execute(text(f'SET LOCAL search_path TO "{self.schema}", pg_catalog'))

    def _lock(self, connection: Connection | Session, write: bool = True) -> None:
        function = "pg_advisory_xact_lock" if write else "pg_advisory_xact_lock_shared"
        connection.execute(
            text(f"SELECT pg_catalog.{function}(pg_catalog.hashtextextended(:scope, 0))"),
            {"scope": self.schema},
        )

    @contextmanager
    def session(self, write: bool = False) -> Iterator[Session]:
        with Session(self.engine) as session:
            if self.postgres:
                self._scope(session)
                self._lock(session, write)
            elif write:
                session.execute(text("BEGIN IMMEDIATE"))
            try:
                yield session
                if write:
                    session.commit()
            except Exception:
                session.rollback()
                raise


def put(session: Session, entity: Entity) -> None:
    row = session.get(EntityRow, entity.id)
    if row is None:
        session.add(
            EntityRow(
                id=entity.id, kind=type(entity).__name__, payload=entity.model_dump(mode="json")
            )
        )
    else:
        if row.kind != type(entity).__name__:
            raise ValueError("Entity identity collision")
        if (
            isinstance(entity, (Observation, HumanDecision, Interpretation))
            or type(entity).__name__ in {
                "SourceDeclaration", "Supersession", "AuthAudit", "InferenceAttempt"
            }
        ) and (row.payload != entity.model_dump(mode="json")):
            raise ValueError("Original observation, interpretation and decision are immutable")
        if (
            isinstance(entity, Evidence)
            and (
                row.payload.get("source_type") == "orbital"
                or row.payload.get("verification_state")
                in {Verification.CONFIRMED.value, Verification.REJECTED.value}
            )
            and row.payload != entity.model_dump(mode="json")
        ):
            raise ValueError("NASA priors and final evidence decisions are immutable")
        row.payload = entity.model_dump(mode="json")
    session.flush()


def get[T: Entity](session: Session, cls: type[T], entity_id: str) -> T:
    row = session.get(EntityRow, entity_id)
    if row is None or row.kind != cls.__name__:
        raise KeyError(entity_id)
    return cls.model_validate(row.payload)


def all_of[T: Entity](session: Session, cls: type[T]) -> list[T]:
    rows = session.scalars(
        select(EntityRow).where(EntityRow.kind == cls.__name__).order_by(EntityRow.id)
    )
    return [cls.model_validate(row.payload) for row in rows]
)
                            )
                        """))
                        connection.execute(text(
                            "ALTER TABLE marsense.asset_blobs ENABLE ROW LEVEL SECURITY"
                        ))
                        connection.execute(text(
                            "REVOKE ALL ON marsense.asset_blobs "
                            "FROM PUBLIC, anon, authenticated, service_role"
                        ))
                        connection.execute(text("""
                            CREATE TABLE IF NOT EXISTS marsense.bootstrap_users (
                                id varchar(100) PRIMARY KEY,
                                payload json NOT NULL
                            )
                        """))
                        connection.execute(text(
                            "ALTER TABLE marsense.bootstrap_users ENABLE ROW LEVEL SECURITY"
                        ))
                        connection.execute(text(
                            "REVOKE ALL ON marsense.bootstrap_users "
                            "FROM PUBLIC, anon, authenticated, service_role"
                        ))
                with Session(bind=connection) as session:
                    if version < 2:
                        from backend.migrations import migrate_legacy_segments

                        migrate_legacy_segments(session)
                    row = session.get(SchemaVersion, 1)
                    if row is None:
                        session.add(SchemaVersion(id=1, version=SCHEMA_VERSION))
                    else:
                        row.version = SCHEMA_VERSION
                    session.flush()
        except Exception:
            self.engine.dispose()
            raise

    def _scope(self, connection: Connection | Session) -> None:
        connection.execute(text(f'SET LOCAL search_path TO "{self.schema}", pg_catalog'))

    def _lock(self, connection: Connection | Session, write: bool = True) -> None:
        function = "pg_advisory_xact_lock" if write else "pg_advisory_xact_lock_shared"
        connection.execute(
            text(f"SELECT pg_catalog.{function}(pg_catalog.hashtextextended(:scope, 0))"),
            {"scope": self.schema},
        )

    @contextmanager
    def session(self, write: bool = False) -> Iterator[Session]:
        with Session(self.engine) as session:
            if self.postgres:
                self._scope(session)
                self._lock(session, write)
            elif write:
                session.execute(text("BEGIN IMMEDIATE"))
            try:
                yield session
                if write:
                    session.commit()
            except Exception:
                session.rollback()
                raise


def put(session: Session, entity: Entity) -> None:
    row = session.get(EntityRow, entity.id)
    if row is None:
        session.add(
            EntityRow(
                id=entity.id, kind=type(entity).__name__, payload=entity.model_dump(mode="json")
            )
        )
    else:
        if row.kind != type(entity).__name__:
            raise ValueError("Entity identity collision")
        if (
            isinstance(entity, (Observation, HumanDecision, Interpretation))
            or type(entity).__name__ in {
                "SourceDeclaration", "Supersession", "AuthAudit", "InferenceAttempt"
            }
        ) and (row.payload != entity.model_dump(mode="json")):
            raise ValueError("Original observation, interpretation and decision are immutable")
        if (
            isinstance(entity, Evidence)
            and (
                row.payload.get("source_type") == "orbital"
                or row.payload.get("verification_state")
                in {Verification.CONFIRMED.value, Verification.REJECTED.value}
            )
            and row.payload != entity.model_dump(mode="json")
        ):
            raise ValueError("NASA priors and final evidence decisions are immutable")
        row.payload = entity.model_dump(mode="json")
    session.flush()


def get[T: Entity](session: Session, cls: type[T], entity_id: str) -> T:
    row = session.get(EntityRow, entity_id)
    if row is None or row.kind != cls.__name__:
        raise KeyError(entity_id)
    return cls.model_validate(row.payload)


def all_of[T: Entity](session: Session, cls: type[T]) -> list[T]:
    rows = session.scalars(
        select(EntityRow).where(EntityRow.kind == cls.__name__).order_by(EntityRow.id)
    )
    return [cls.model_validate(row.payload) for row in rows]
