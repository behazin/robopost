import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

from services.management_api import main
from services.management_api.database import Base, get_db
from services.management_api import models

# Disable database initialization during tests
main.init_db = lambda: None
app = main.app

# Set up in-memory SQLite database
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the in-memory session

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_create_and_delete_source(client):
    response = client.post("/sources/", json={"name": "source1"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "source1"
    source_id = data["id"]

    delete_response = client.delete(f"/sources/{source_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "deleted"}


def test_create_and_delete_destination(client):
    payload = {"name": "dest1", "credentials": {"token": "abc"}}
    response = client.post("/destinations/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "dest1"
    assert data["credentials"] == {"token": "abc"}
    dest_id = data["id"]

    delete_response = client.delete(f"/destinations/{dest_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "deleted"}


def test_source_model_defaults_and_constraints(db_session):
    src = models.Source(name="unique-source")
    db_session.add(src)
    db_session.commit()
    db_session.refresh(src)
    assert src.created_at is not None

    db_session.add(models.Source(name="unique-source"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    db_session.add(models.Source(name=None))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_destination_model_defaults_and_constraints(db_session):
    dest = models.Destination(name="unique-dest", credentials={"api_key": "123"})
    db_session.add(dest)
    db_session.commit()
    db_session.refresh(dest)
    assert dest.created_at is not None

    db_session.add(models.Destination(name="unique-dest", credentials={"api_key": "456"}))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    db_session.add(models.Destination(name="dest2", credentials=None))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()