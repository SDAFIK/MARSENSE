import os
from uuid import uuid4

import pytest
from sqlalchemy import select

from backend.cloud_store import CloudStore
from backend.domain import Mission
from backend.seed import seed
from backend.store import EntityRow, all_of
from scripts.cloud_import_mission import import_mission


@pytest.mark.skipif(not os.getenv("MARSENSE_TEST_POSTGRES_URL"), reason="Dedicated Postgres required")
def test_cloud_namespace_isolation_persistence_and_no_overwrite():
    url = os.environ["MARSENSE_TEST_POSTGRES_URL"]
    first_schema = "marsense_test_" + uuid4().hex
    second_schema = "marsense_test_" + uuid4().hex
    first = CloudStore(url, first_schema)
    second = CloudStore(url, second_schema)
    try:
        with first.session(write=True) as session:
            seed(session)
            rows = {r.id: (r.kind, r.payload) for r in session.scalars(select(EntityRow))}
        with second.session() as session:
            assert all_of(session, Mission) == []
        import_mission(second, rows)
        with pytest.raises(ValueError, match="not empty"):
            import_mission(second, rows)
        first.close()
        reopened = CloudStore(url, first_schema)
        try:
            with reopened.session() as session:
                assert {r.id: (r.kind, r.payload) for r in session.scalars(select(EntityRow))} == rows
        finally:
            reopened.close()
    finally:
        first.close()
        second.close()


def test_cloud_store_rejects_unscoped_database():
    with pytest.raises(ValueError, match="dedicated"):
        CloudStore("postgresql://invalid", "public")
    with pytest.raises(ValueError, match="PostgreSQL"):
        CloudStore("sqlite:///:memory:", "marsense_test")
