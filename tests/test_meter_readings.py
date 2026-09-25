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

    # Important: re-apply this test's database
    # before every test.
    app.dependency_overrides[get_db] = override_get_db

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    # Clean existing test data.
    for model in [
        MeterReading,
        Connection,
        Customer,
        User,
    ]:
        db.query(model).delete()

    db.commit()

    # Create user.
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

    # Create customer.
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

    # Create electricity connection.
    connection = Connection(
        customer_id=customer.id,
        connection_number="CONN000001",
        connection_type="Domestic",
        tariff_type="Residential",
        meter_number="MTR000001",
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


def reading_payload(connection_id, reading_value=100.0):
    return {
        "connection_id": connection_id,
        "reading_date": "2026-09-24",
        "reading_value": reading_value,
        "reading_type": "Actual",
        "remarks": "Test reading",
    }


def test_create_meter_reading(setup_database):
    connection = setup_database["connection"]

    response = client.post(
        "/meter-readings",
        json=reading_payload(connection.id),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["connection_id"] == connection.id
    assert data["reading_value"] == 100.0
    assert data["previous_reading"] == 0
    assert data["consumption_units"] == 100.0
    assert data["reading_type"] == "Actual"


def test_create_second_reading_calculates_consumption(
    setup_database,
):
    connection = setup_database["connection"]

    first_response = client.post(
        "/meter-readings",
        json=reading_payload(
            connection.id,
            100.0,
        ),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/meter-readings",
        json={
            "connection_id": connection.id,
            "reading_date": "2026-09-25",
            "reading_value": 150.0,
            "reading_type": "Actual",
            "remarks": "Second reading",
        },
    )

    assert second_response.status_code == 201

    data = second_response.json()

    assert data["previous_reading"] == 100.0
    assert data["consumption_units"] == 50.0


def test_create_meter_reading_with_zero_value(
    setup_database,
):
    connection = setup_database["connection"]

    response = client.post(
        "/meter-readings",
        json=reading_payload(
            connection.id,
            0.0,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["reading_value"] == 0.0
    assert data["consumption_units"] == 0.0


def test_create_meter_reading_negative_value_rejected(
    setup_database,
):
    connection = setup_database["connection"]

    response = client.post(
        "/meter-readings",
        json=reading_payload(
            connection.id,
            -10.0,
        ),
    )

    assert response.status_code == 422


def test_get_meter_reading(setup_database):
    connection = setup_database["connection"]

    create_response = client.post(
        "/meter-readings",
        json=reading_payload(connection.id),
    )

    assert create_response.status_code == 201

    reading_id = create_response.json()["id"]

    response = client.get(
        f"/meter-readings/{reading_id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == reading_id
    assert data["connection_id"] == connection.id


def test_list_meter_readings(setup_database):
    connection = setup_database["connection"]

    response = client.post(
        "/meter-readings",
        json=reading_payload(connection.id),
    )

    assert response.status_code == 201

    response = client.get(
        "/meter-readings",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_list_meter_readings_by_connection(
    setup_database,
):
    connection = setup_database["connection"]

    response = client.post(
        "/meter-readings",
        json=reading_payload(connection.id),
    )

    assert response.status_code == 201

    response = client.get(
        "/meter-readings",
        params={
            "connection_id": connection.id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["connection_id"] == connection.id


def test_list_meter_readings_pagination(
    setup_database,
):
    connection = setup_database["connection"]

    for index, value in enumerate(
        [100.0, 150.0, 200.0],
        start=1,
    ):
        response = client.post(
            "/meter-readings",
            json={
                "connection_id": connection.id,
                "reading_date": f"2026-09-{20 + index}",
                "reading_value": value,
                "reading_type": "Actual",
                "remarks": f"Reading {index}",
            },
        )

        assert response.status_code == 201

    response = client.get(
        "/meter-readings",
        params={
            "page": 1,
            "page_size": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["pages"] == 2
    assert len(data["items"]) == 2


def test_update_meter_reading(setup_database):
    connection = setup_database["connection"]

    create_response = client.post(
        "/meter-readings",
        json=reading_payload(
            connection.id,
            100.0,
        ),
    )

    assert create_response.status_code == 201

    reading_id = create_response.json()["id"]

    response = client.put(
        f"/meter-readings/{reading_id}",
        json={
            "reading_date": "2026-09-25",
            "reading_value": 125.0,
            "reading_type": "Actual",
            "remarks": "Updated reading",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["reading_value"] == 125.0
    assert data["reading_type"] == "Actual"
    assert data["remarks"] == "Updated reading"


def test_update_meter_reading_negative_value_rejected(
    setup_database,
):
    connection = setup_database["connection"]

    create_response = client.post(
        "/meter-readings",
        json=reading_payload(
            connection.id,
            100.0,
        ),
    )

    assert create_response.status_code == 201

    reading_id = create_response.json()["id"]

    response = client.put(
        f"/meter-readings/{reading_id}",
        json={
            "reading_value": -50.0,
        },
    )

    assert response.status_code == 422


def test_delete_meter_reading(setup_database):
    connection = setup_database["connection"]

    create_response = client.post(
        "/meter-readings",
        json=reading_payload(connection.id),
    )

    assert create_response.status_code == 201

    reading_id = create_response.json()["id"]

    response = client.delete(
        f"/meter-readings/{reading_id}",
    )

    assert response.status_code == 204

    response = client.get(
        f"/meter-readings/{reading_id}",
    )

    assert response.status_code == 404