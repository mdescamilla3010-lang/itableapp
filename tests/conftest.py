import os
import uuid

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/itable_test",
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.database import SessionLocal
from app.db.models import Tenant
from app.main import app


@pytest.fixture(autouse=True)
def _clean_database():
    """Ensures every test starts from an empty database.

    Deleting Tenant rows cascades to every other table (Branch, Staff,
    Order, OrderItem, CashShift, AuditEvent), so this is enough to reset
    state between tests without dropping the schema created by Alembic.
    """
    yield
    session = SessionLocal()
    try:
        session.execute(text("DELETE FROM tenants"))
        session.commit()
    finally:
        session.close()


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def tenant(db_session):
    t = Tenant(name="Restaurante de Prueba", slug=f"test-{uuid.uuid4().hex[:8]}")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t
