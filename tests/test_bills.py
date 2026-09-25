from datetime import date

from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.models.customer import Customer
from app.models.connection import Connection
from app.models.meter_reading import MeterReading

from tests.conftest import TestingSessionLocal


client = TestClient(app)


def create_test_data():
    db = TestingSessionLocal()

    user = User(
        full_name="Test Customer",
        email="customer@example.com",
        phone="9876543210",
        password_hash="test-password-hash",
        role="Customer",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

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

    connection = Connection(
        customer_id=customer.id,
        connection_number="CONN000001",
        connection_type="Domestic",
        tariff_type="Residential",
        meter_number="MTR000001",
        meter_type="Digital",
        sanctioned_load=5.0,
        status="Active",
        connection_date=date(2026, 1, 1),
    )

    db.add(connection)
    db.commit()
    db.refresh(connection)

    customer_id = customer.id
    connection_id = connection.id

    db.close()

    return customer_id, connection_id


def add_meter_readings(connection_id):
    db = TestingSessionLocal()

    first_reading = MeterReading(
        connection_id=connection_id,
        reading_date=date(2026, 1, 1),
        reading_value=100.0,
        previous_reading=0.0,
        consumption_units=100.0,
        reading_type="Actual",
        remarks=None,
    )

    second_reading = MeterReading(
        connection_id=connection_id,
        reading_date=date(2026, 1, 31),
        reading_value=150.0,
        previous_reading=100.0,
        consumption_units=50.0,
        reading_type="Actual",
        remarks=None,
    )

    db.add(first_reading)
    db.add(second_reading)

    db.commit()
    db.close()


def bill_payload(connection_id):
    return {
        "connection_id": connection_id,
        "billing_period_start": "2026-01-01",
        "billing_period_end": "2026-01-31",
        "due_date": "2026-02-15",
    }


def test_create_bill():
    customer_id, connection_id = create_test_data()

    add_meter_readings(connection_id)

    response = client.post(
        "/bills",
        json=bill_payload(connection_id),
    )

    print("STATUS:", response.status_code)
    print("BODY:", response.text)

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == customer_id
    assert data["connection_id"] == connection_id
    assert data["bill_number"].startswith("BILL")

    assert data["previous_reading"] == 100.0
    assert data["current_reading"] == 150.0
    assert data["units_consumed"] == 50.0

    assert data["energy_charge"] == 325.0
    assert data["fixed_charge"] == 100.0
    assert data["tax_amount"] == 21.25
    assert data["total_amount"] == 446.25

    assert data["status"] == "Unpaid"


def test_create_bill_without_meter_reading():
    customer_id, connection_id = create_test_data()

    response = client.post(
        "/bills",
        json=bill_payload(connection_id),
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "No meter reading found for this billing period"
    )


def test_create_bill_connection_not_found():
    create_test_data()

    response = client.post(
        "/bills",
        json=bill_payload(99999),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Connection not found"


def test_create_bill_invalid_billing_period():
    customer_id, connection_id = create_test_data()

    add_meter_readings(connection_id)

    response = client.post(
        "/bills",
        json={
            "connection_id": connection_id,
            "billing_period_start": "2026-02-01",
            "billing_period_end": "2026-01-31",
            "due_date": "2026-02-15",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Billing period end date cannot be before start date"
    )


def test_create_bill_invalid_due_date():
    customer_id, connection_id = create_test_data()

    add_meter_readings(connection_id)

    response = client.post(
        "/bills",
        json={
            "connection_id": connection_id,
            "billing_period_start": "2026-01-01",
            "billing_period_end": "2026-01-31",
            "due_date": "2026-01-15",
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Due date cannot be before billing period end date"
    )


def test_get_bill():
    customer_id, connection_id = create_test_data()

    add_meter_readings(connection_id)

    create_response = client.post(
        "/bills",
        json=bill_payload(connection_id),
    )

    assert create_response.status_code == 201

    bill_id = create_response.json()["id"]

    response = client.get(
        f"/bills/{bill_id}",
    )

    assert response.status_code == 200
    assert response.json()["id"] == bill_id


def test_get_bill_not_found():
    create_test_data()

    response = client.get("/bills/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Bill not found"


def test_list_bills():
    customer_id, connection_id = create_test_data()

    add_meter_readings(connection_id)

    create_response = client.post(
        "/bills",
        json=bill_payload(connection_id),
    )

    assert create_response.status_code == 201

    response = client.get("/bills")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_list_bills_by_customer():
    customer_id, connection_id = create_test_data()

    add_meter_readings(connection_id)

    create_response = client.post(
        "/bills",
        json=bill_payload(connection_id),
    )

    assert create_response.status_code == 201

    response = client.get(
        "/bills",
        params={"customer_id": customer_id},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["customer_id"] == customer_id


def test_update_bill_status():
    customer_id, connection_id = create_test_data()

    add_meter_readings(connection_id)

    create_response = client.post(
        "/bills",
        json=bill_payload(connection_id),
    )

    assert create_response.status_code == 201

    bill_id = create_response.json()["id"]

    response = client.patch(
        f"/bills/{bill_id}/status",
        json={"status": "Paid"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Paid"


def test_update_bill_status_invalid():
    customer_id, connection_id = create_test_data()

    add_meter_readings(connection_id)

    create_response = client.post(
        "/bills",
        json=bill_payload(connection_id),
    )

    assert create_response.status_code == 201

    bill_id = create_response.json()["id"]

    response = client.patch(
        f"/bills/{bill_id}/status",
        json={"status": "InvalidStatus"},
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Invalid status. Allowed values: "
        "Unpaid, Paid, Overdue, Cancelled"
    )


def test_update_bill_status_not_found():
    create_test_data()

    response = client.patch(
        "/bills/99999/status",
        json={"status": "Paid"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Bill not found"