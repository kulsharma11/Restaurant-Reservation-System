# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

from sqlalchemy.pool import StaticPool

# In-memory SQLite — faster than file-based, and disappears after tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    """
    Creates all tables before each test, drops them after.
    autouse=True means this runs automatically for every test.
    This guarantees each test starts with a completely empty database.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(setup_database):
    """Provides a database session for tests that need direct DB access."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    """
    Provides a TestClient that uses the test database instead of the real one.
    Overrides the get_db dependency so no real DB is used during tests.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ── Helper Functions ──────────────────────────────────────────────────────────

def create_test_table(client, table_number=1, capacity=4, location="indoor"):
    """Helper to create a table in tests without repeating the POST call."""
    response = client.post("/tables/", json={
        "table_number": table_number,
        "capacity": capacity,
        "location": location
    })
    assert response.status_code == 201
    return response.json()


def create_test_reservation(client, table_id=None, guest_count=2,
                             date="2099-12-31", time_slot="18:00"):
    """Helper to create a reservation. Uses far-future date so it's always valid."""
    payload = {
        "date": date,
        "time_slot": time_slot,
        "guest_count": guest_count,
        "customer": {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "1234567890"
        }
    }
    if table_id is not None:  # use `is not None` instead of truthiness check
        payload["table_id"] = table_id

    response = client.post("/reservations/", json=payload)
    return response
