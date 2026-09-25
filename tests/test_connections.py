import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

from app.models.user import User
from app.models.customer import Customer
from app.models.connection import Connection
from app.models.meter_reading import MeterReading
from app.models.bill import Bill
from app.models.payment import Payment
from app.models.service_request import ServiceRequest
from app.models.notification import Notification
from app.models.tariff import Tariff
from app.models.complaint import Complaint
from app.models.technician import Technician

from app.utils.security import hash_password


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


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():

    # IMPORTANT:
    # Re-apply this test file's database override before every test.
    app.dependency_overrides[get_db] = override_get_db

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    # Clean tables in dependency order.
    for model in [
        MeterReading,
        Payment,
        Bill,
        ServiceRequest,
        Notification,
        Complaint,
        Connection,
        Technician,
        Tariff,
        Customer,
        User,
    ]:
        db.query(model).delete()

    db.commit()

    # Create test user first because Customer.user_id is NOT NULL.
    user = User(
        full_name="Test Customer",
        email="customer@example.com",
        phone="9876543210",
        password_hash=hash_password("Test@12345"),
        role="Customer",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create customer linked to the user.
    customer = Customer(
        user_id=user.id,
        customer_number="CUS000001",
        full_name="Test Customer",
        email="customer@example.com",
        phone="9876543210",
        address="Chennai",
        connection_type="Domestic",
        connection_number="CUS-CONN-001",
        status="Active",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    yield customer

    db.close()

    Base.metadata.drop_all(bind=engine)


def connection_payload(customer_id):
    return {
        "customer_id": customer_id,
        "connection_type": "Domestic",
        "tariff_type": "Residential",
        "meter_number": "MTR000001",
        "meter_type": "Digital",
        "sanctioned_load": 5.0,
    }


def test_create_connection(setup_database):
    customer = setup_database

    response = client.post(
        "/connections",
        json=connection_payload(customer.id),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer.id
    assert data["connection_type"] == "Domestic"
    assert data["tariff_type"] == "Residential"
    assert data["meter_number"] == "MTR000001"
    assert data["meter_type"] == "Digital"
    assert data["sanctioned_load"] == 5.0
    assert data["status"] == "Active"


def test_get_connection(setup_database):
    customer = setup_database

    create_response = client.post(
        "/connections",
        json=connection_payload(customer.id),
    )

    assert create_response.status_code == 201

    connection_id = create_response.json()["id"]

    response = client.get(
        f"/connections/{connection_id}",
    )

    assert response.status_code == 200
    assert response.json()["id"] == connection_id


def test_get_connection_not_found(setup_database):
    response = client.get(
        "/connections/99999",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Connection not found"


def test_list_connections(setup_database):
    customer = setup_database

    response = client.post(
        "/connections",
        json=connection_payload(customer.id),
    )

    assert response.status_code == 201

    response = client.get("/connections")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_list_connections_by_customer(setup_database):
    customer = setup_database

    response = client.post(
        "/connections",
        json=connection_payload(customer.id),
    )

    assert response.status_code == 201

    response = client.get(
        "/connections",
        params={
            "customer_id": customer.id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["customer_id"] == customer.id


def test_list_connections_by_status(setup_database):
    customer = setup_database

    response = client.post(
        "/connections",
        json=connection_payload(customer.id),
    )

    assert response.status_code == 201

    response = client.get(
        "/connections",
        params={
            "status": "Active",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "Active"


def test_update_connection(setup_database):
    customer = setup_database

    response = client.post(
        "/connections",
        json=connection_payload(customer.id),
    )

    assert response.status_code == 201

    connection_id = response.json()["id"]

    response = client.put(
        f"/connections/{connection_id}",
        json={
            "connection_type": "Commercial",
            "tariff_type": "Commercial",
            "meter_number": "MTR000002",
            "meter_type": "Smart",
            "sanctioned_load": 10.0,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["connection_type"] == "Commercial"
    assert data["tariff_type"] == "Commercial"
    assert data["meter_number"] == "MTR000002"
    assert data["meter_type"] == "Smart"
    assert data["sanctioned_load"] == 10.0


def test_update_connection_not_found(setup_database):
    response = client.put(
        "/connections/99999",
        json={
            "connection_type": "Commercial",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Connection not found"


def test_update_connection_status(setup_database):
    customer = setup_database

    response = client.post(
        "/connections",
        json=connection_payload(customer.id),
    )

    assert response.status_code == 201

    connection_id = response.json()["id"]

    response = client.patch(
        f"/connections/{connection_id}/status",
        json={
            "status": "Suspended",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Suspended"


def test_update_connection_status_not_found(setup_database):
    response = client.patch(
        "/connections/99999/status",
        json={
            "status": "Suspended",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Connection not found"


def test_delete_connection(setup_database):
    customer = setup_database

    response = client.post(
        "/connections",
        json=connection_payload(customer.id),
    )

    assert response.status_code == 201

    connection_id = response.json()["id"]

    response = client.delete(
        f"/connections/{connection_id}",
    )

    assert response.status_code == 204

    response = client.get(
        f"/connections/{connection_id}",
    )

    assert response.status_code == 404


def test_delete_connection_not_found(setup_database):
    response = client.delete(
        "/connections/99999",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Connection not found"