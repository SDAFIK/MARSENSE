"""One-time, explicitly authorized initialization; never replaces existing records."""

import json

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from backend.auth import User, password_hash
from backend.config import Settings
from backend.domain import Mission
from backend.seed import seed
from backend.store import EntityRow, all_of


def initialize_fresh_cloud(
    session: Session, settings: Settings, slope_grid: np.ndarray | None,
) -> None:
    users = session.scalar(text("SELECT count(*) FROM marsense.bootstrap_users"))
    missions = all_of(session, Mission)
    if missions and users:
        # An initialized deployment is immutable to this bootstrap operation.
        return
    if session.scalar(select(EntityRow.id).limit(1)) is not None or users:
        raise ValueError("Fresh bootstrap refuses partially populated mission or identity data")
    if session.scalar(text("SELECT count(*) FROM marsense.asset_blobs")):
        raise ValueError("Fresh bootstrap refuses existing evidence assets")
    if session.scalar(text("SELECT count(*) FROM marsense_accounts.entities")):
        raise ValueError("Fresh bootstrap refuses existing account records")
    password = settings.cloud_admin_password.get_secret_value()
    if not 15 <= len(password) <= 256:
        raise ValueError("Set a private cloud administrator password of 15–256 characters")
    operator = User(
        id="cloud-operator", username="marsense-admin", name="MARSENSE Administrator",
        role="ADMIN", password_hash=password_hash(password),
    )
    seed(session, slope_grid)
    session.execute(text(
        "INSERT INTO marsense.bootstrap_users(id,payload) VALUES (:id,CAST(:payload AS json))"
    ), {"id": operator.id, "payload": json.dumps(operator.model_dump(mode="json"))})
