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
from app.models.complaint import Complaint
from app.models.technician import Technician
from app.models.tariff import Tariff

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

    app.dependency_overrides[get_db] = override_get_db

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    for model in [
        Payment,
        Bill,
        MeterReading,
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

    user = User(
        full_name="Analytics Customer",
        email="analytics@example.com",
        phone="9876543210",
        password_hash=hash_password("Test@12345"),
        role="Customer",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    customer = Customer(
        user_id=user.id,
        customer_number="CUS000001",
        full_name="Analytics Customer",
        email="analytics@example.com",
        phone="9876543210",
        address="Chennai",
        connection_type="Domestic",
        connection_number="CUS-CONN-001",
        status="Active",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    connection = Connection(
        customer_id=customer.id,
        connection_number="AN-CONN-001",
        connection_type="Domestic",
        tariff_type="Residential",
        meter_number="AN-MTR-001",
        meter_type="Digital",
        sanctioned_load=5.0,
        status="Active",
    )

    db.add(connection)
    db.commit()
    db.refresh(connection)

    yield {
        "customer": customer,
        "connection": connection,
    }

    db.close()

    Base.metadata.drop_all(bind=engine)


def create_meter_reading(
    connection_id,
    reading_date,
    reading_value,
):
    response = client.post(
        "/meter-readings",
        json={
            "connection_id": connection_id,
            "reading_date": reading_date,
            "reading_value": reading_value,
            "reading_type": "Actual",
            "remarks": "Analytics test",
        },
    )

    assert response.status_code == 201

    return response


def test_dashboard(setup_database):

    response = client.get(
        "/analytics/dashboard"
    )

    assert response.status_code == 200

    data = response.json()

    assert "total_customers" in data
    assert "active_connections" in data
    assert "total_units_consumed" in data
    assert "total_bills" in data
    assert "paid_bills" in data
    assert "unpaid_bills" in data
    assert "total_revenue" in data
    assert "open_service_requests" in data

    assert data["total_customers"] == 1
    assert data["active_connections"] == 1


def test_connection_monthly_consumption(
    setup_database,
):
    connection_id = setup_database["connection"].id

    create_meter_reading(
        connection_id,
        "2026-09-01",
        100.0,
    )

    create_meter_reading(
        connection_id,
        "2026-09-20",
        150.0,
    )

    response = client.get(
        f"/analytics/connections/{connection_id}/monthly"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert data[0]["month"] == "2026-09"
    assert data[0]["units_consumed"] == 150.0


def test_connection_monthly_consumption_connection_not_found(
    setup_database,
):
    response = client.get(
        "/analytics/connections/99999/monthly"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Connection not found"
    )


def test_yearly_consumption(
    setup_database,
):
    connection_id = setup_database["connection"].id

    create_meter_reading(
        connection_id,
        "2026-01-10",
        100.0,
    )

    create_meter_reading(
        connection_id,
        "2026-02-10",
        200.0,
    )

    response = client.get(
        "/analytics/yearly"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    year_data = next(
        item
        for item in data
        if item["year"] == 2026
    )

    assert year_data["units_consumed"] == 200.0


def test_connection_usage(
    setup_database,
):
    connection_id = setup_database["connection"].id

    create_meter_reading(
        connection_id,
        "2026-09-01",
        100.0,
    )

    response = client.get(
        "/analytics/connections"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    connection_data = next(
        item
        for item in data
        if item["connection_id"] == connection_id
    )

    assert connection_data["units_consumed"] == 100.0


def test_customer_usage(
    setup_database,
):
    connection_id = setup_database["connection"].id

    create_meter_reading(
        connection_id,
        "2026-09-01",
        100.0,
    )

    response = client.get(
        "/analytics/customers"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_highest_consuming_connections(
    setup_database,
):
    connection_id = setup_database["connection"].id

    create_meter_reading(
        connection_id,
        "2026-09-01",
        100.0,
    )

    response = client.get(
        "/analytics/connections/highest",
        params={"limit": 10},
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert data[0]["connection_id"] == connection_id
    assert data[0]["units_consumed"] == 100.0


def test_highest_consuming_connections_limit(
    setup_database,
):
    response = client.get(
        "/analytics/connections/highest",
        params={"limit": 5},
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_average_monthly_consumption(
    setup_database,
):
    connection_id = setup_database["connection"].id

    create_meter_reading(
        connection_id,
        "2026-09-01",
        100.0,
    )

    response = client.get(
        "/analytics/average-monthly"
    )

    assert response.status_code == 200

    data = response.json()

    assert "average_monthly_consumption" in data
    assert data["average_monthly_consumption"] == 100.0


def test_average_monthly_consumption_empty(
    setup_database,
):
    response = client.get(
        "/analytics/average-monthly"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["average_monthly_consumption"] == 0.0