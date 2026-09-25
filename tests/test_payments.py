from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import app
from app.models.bill import Bill
from app.models.connection import Connection
from app.models.customer import Customer
from app.models.meter_reading import MeterReading
from app.models.user import User

from tests.conftest import TestingSessionLocal


client = TestClient(app)


def create_test_bill():
    db = TestingSessionLocal()

    user = User(
        full_name="Payment Test User",
        email="payment@test.com",
        phone="9876543210",
        password_hash="test_password_hash",
        role="Customer",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    customer = Customer(
        user_id=user.id,
        customer_number="CUS-PAY-001",
        full_name="Payment Test Customer",
        email="payment@test.com",
        phone="9876543210",
        address="Chennai",
        connection_type="Domestic",
        connection_number="CON-PAY-001",
        registration_date=date.today(),
        status="Active",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    connection = Connection(
        customer_id=customer.id,
        connection_number="CONNECTION-PAY-001",
        connection_type="Domestic",
        tariff_type="Domestic",
        meter_number="METER-PAY-001",
        meter_type="Digital",
        sanctioned_load=5.0,
        status="Active",
        connection_date=date.today(),
    )

    db.add(connection)
    db.commit()
    db.refresh(connection)

    previous_reading = MeterReading(
        connection_id=connection.id,
        reading_value=100.0,
        reading_date=date.today() - timedelta(days=30),
    )

    current_reading = MeterReading(
        connection_id=connection.id,
        reading_value=250.0,
        reading_date=date.today(),
    )

    db.add(previous_reading)
    db.add(current_reading)
    db.commit()

    bill = Bill(
        customer_id=customer.id,
        connection_id=connection.id,
        bill_number="BILL-PAY-001",
        billing_period_start=date.today() - timedelta(days=30),
        billing_period_end=date.today(),
        previous_reading=100.0,
        current_reading=250.0,
        units_consumed=150.0,
        energy_charge=975.0,
        fixed_charge=100.0,
        tax_amount=53.75,
        total_amount=1128.75,
        due_date=date.today() + timedelta(days=15),
        status="Unpaid",
    )

    db.add(bill)
    db.commit()
    db.refresh(bill)

    result = {
        "user_id": user.id,
        "customer_id": customer.id,
        "connection_id": connection.id,
        "bill_id": bill.id,
        "bill_amount": bill.total_amount,
    }

    db.close()

    return result


def test_create_payment():
    data = create_test_bill()

    response = client.post(
        "/payments",
        json={
            "bill_id": data["bill_id"],
            "amount": data["bill_amount"],
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 201

    result = response.json()

    assert result["bill_id"] == data["bill_id"]
    assert result["amount"] == data["bill_amount"]
    assert result["payment_method"] == "UPI"
    assert result["status"] == "Successful"
    assert result["payment_reference"].startswith("PAY-")
    assert result["transaction_id"].startswith("TXN-")


def test_create_payment_wrong_amount():
    data = create_test_bill()

    response = client.post(
        "/payments",
        json={
            "bill_id": data["bill_id"],
            "amount": 100.00,
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == (
            f"Payment amount must be exactly "
            f"{data['bill_amount']:.2f}"
        )
    )


def test_create_payment_already_paid():
    data = create_test_bill()

    response = client.post(
        "/payments",
        json={
            "bill_id": data["bill_id"],
            "amount": data["bill_amount"],
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 201

    response = client.post(
        "/payments",
        json={
            "bill_id": data["bill_id"],
            "amount": data["bill_amount"],
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Bill is already paid"
    )


def test_create_payment_cancelled_bill():
    data = create_test_bill()

    db = TestingSessionLocal()

    bill = (
        db.query(Bill)
        .filter(Bill.id == data["bill_id"])
        .first()
    )

    bill.status = "Cancelled"

    db.commit()
    db.close()

    response = client.post(
        "/payments",
        json={
            "bill_id": data["bill_id"],
            "amount": data["bill_amount"],
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Cannot pay a cancelled bill"
    )


def test_get_payment():
    data = create_test_bill()

    response = client.post(
        "/payments",
        json={
            "bill_id": data["bill_id"],
            "amount": data["bill_amount"],
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 201

    payment_id = response.json()["id"]

    response = client.get(
        f"/payments/{payment_id}"
    )

    assert response.status_code == 200

    result = response.json()

    assert result["id"] == payment_id
    assert result["bill_id"] == data["bill_id"]


def test_get_payment_not_found():
    response = client.get(
        "/payments/99999"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Payment not found"
    )


def test_list_payments():
    data = create_test_bill()

    response = client.post(
        "/payments",
        json={
            "bill_id": data["bill_id"],
            "amount": data["bill_amount"],
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 201

    response = client.get("/payments")

    assert response.status_code == 200

    result = response.json()

    assert "items" in result
    assert "total" in result
    assert "page" in result
    assert "page_size" in result
    assert "pages" in result

    assert result["total"] >= 1
    assert len(result["items"]) >= 1


def test_list_payments_by_bill():
    data = create_test_bill()

    response = client.post(
        "/payments",
        json={
            "bill_id": data["bill_id"],
            "amount": data["bill_amount"],
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/payments",
        params={
            "bill_id": data["bill_id"],
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["total"] >= 1

    for payment in result["items"]:
        assert payment["bill_id"] == data["bill_id"]


def test_list_payments_by_status():
    data = create_test_bill()

    response = client.post(
        "/payments",
        json={
            "bill_id": data["bill_id"],
            "amount": data["bill_amount"],
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/payments",
        params={
            "status": "Successful",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["total"] >= 1

    for payment in result["items"]:
        assert payment["status"] == "Successful"


def test_payment_marks_bill_as_paid():
    data = create_test_bill()

    response = client.post(
        "/payments",
        json={
            "bill_id": data["bill_id"],
            "amount": data["bill_amount"],
            "payment_method": "UPI",
        },
    )

    assert response.status_code == 201

    db = TestingSessionLocal()

    bill = (
        db.query(Bill)
        .filter(Bill.id == data["bill_id"])
        .first()
    )

    assert bill is not None
    assert bill.status == "Paid"

    db.close()