import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_list_customers():
    response = client.get("/customers")

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "pages" in data


def test_list_customers_with_pagination():
    response = client.get(
        "/customers",
        params={
            "page": 1,
            "page_size": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["page_size"] == 10


def test_list_customers_with_search():
    response = client.get(
        "/customers",
        params={
            "search": "Test",
        },
    )

    assert response.status_code == 200


def test_list_customers_with_status_filter():
    response = client.get(
        "/customers",
        params={
            "status": "Active",
        },
    )

    assert response.status_code == 200


def test_list_customers_with_city_filter():
    response = client.get(
        "/customers",
        params={
            "city": "Chennai",
        },
    )

    assert response.status_code == 200


def test_list_customers_with_connection_type_filter():
    response = client.get(
        "/customers",
        params={
            "connection_type": "Domestic",
        },
    )

    assert response.status_code == 200


def test_list_customers_invalid_page():
    response = client.get(
        "/customers",
        params={
            "page": 0,
        },
    )

    assert response.status_code == 422


