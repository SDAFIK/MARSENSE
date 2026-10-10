from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import JSON, Integer, String, create_engine, event, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

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
    def __init__(self, url: str):
        self.engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30})

        @event.listens_for(self.engine, "connect")
        def configure(connection: Any, _: Any) -> None:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")

        try:
            with self.engine.begin() as connection:
                connection.execute(text("BEGIN IMMEDIATE"))
                version = (
                    connection.scalar(text("SELECT version FROM schema_version WHERE id=1"))
                    if inspect(connection).has_table("schema_version")
                    else 1
                )
                if version is None or version > SCHEMA_VERSION:
                    raise ValueError("Database schema is newer or invalid; refusing migration")
                Base.metadata.create_all(connection)
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

    @contextmanager
    def session(self, write: bool = False) -> Iterator[Session]:
        with Session(self.engine) as session:
            if write:
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
            or type(entity).__name__ in {"SourceDeclaration", "Supersession", "AuthAudit"}
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
