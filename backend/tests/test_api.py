import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSourcesEndpoints:
    def test_create_source(self, client):
        source_data = {
            "platform": "github",
            "name": "Test Source",
            "url_pattern": "https://github.com/test",
            "is_active": True,
            "config": {}
        }
        response = client.post("/api/sources/", json=source_data)
        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "github"
        assert data["name"] == "Test Source"
        assert "id" in data

    def test_list_sources(self, client):
        # Create a source first
        source_data = {
            "platform": "github",
            "name": "Test Source",
            "url_pattern": "https://github.com/test",
            "is_active": True,
            "config": {}
        }
        client.post("/api/sources/", json=source_data)

        response = client.get("/api/sources/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["platform"] == "github"

    def test_get_source(self, client):
        source_data = {
            "platform": "github",
            "name": "Test Source",
            "url_pattern": "https://github.com/test",
            "is_active": True,
            "config": {}
        }
        create_response = client.post("/api/sources/", json=source_data)
        source_id = create_response.json()["id"]

        response = client.get(f"/api/sources/{source_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == source_id
        assert data["name"] == "Test Source"

    def test_get_source_not_found(self, client):
        response = client.get("/api/sources/999")
        assert response.status_code == 404

    def test_update_source(self, client):
        source_data = {
            "platform": "github",
            "name": "Test Source",
            "url_pattern": "https://github.com/test",
            "is_active": True,
            "config": {}
        }
        create_response = client.post("/api/sources/", json=source_data)
        source_id = create_response.json()["id"]

        update_data = {"name": "Updated Source"}
        response = client.put(f"/api/sources/{source_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Source"

    def test_delete_source(self, client):
        source_data = {
            "platform": "github",
            "name": "Test Source",
            "url_pattern": "https://github.com/test",
            "is_active": True,
            "config": {}
        }
        create_response = client.post("/api/sources/", json=source_data)
        source_id = create_response.json()["id"]

        response = client.delete(f"/api/sources/{source_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Verify it's deleted
        get_response = client.get(f"/api/sources/{source_id}")
        assert get_response.status_code == 404

    def test_toggle_source_active(self, client):
        source_data = {
            "platform": "github",
            "name": "Test Source",
            "url_pattern": "https://github.com/test",
            "is_active": True,
            "config": {}
        }
        create_response = client.post("/api/sources/", json=source_data)
        source_id = create_response.json()["id"]

        response = client.post(f"/api/sources/{source_id}/toggle")
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False


class TestSummariesEndpoints:
    def test_list_summaries_empty(self, client):
        response = client.get("/api/summaries/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_get_summary_not_found(self, client):
        response = client.get("/api/summaries/999")
        assert response.status_code == 404

    def test_mark_as_read_not_found(self, client):
        response = client.post("/api/summaries/999/read")
        assert response.status_code == 404

    def test_toggle_favorite_not_found(self, client):
        response = client.post("/api/summaries/999/favorite")
        assert response.status_code == 404


class TestStatsEndpoints:
    def test_get_stats(self, client):
        response = client.get("/api/stats/")
        assert response.status_code == 200
        data = response.json()
        assert "total_summaries" in data
        assert "total_sources" in data
        assert "active_sources" in data
        assert "total_raw_contents" in data
        assert "read_count" in data
        assert "favorite_count" in data
        assert "platforms" in data
