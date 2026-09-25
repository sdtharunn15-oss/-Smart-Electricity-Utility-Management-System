from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models.connection import Connection
from app.models.customer import Customer
from app.models.user import User


client = TestClient(app)


def create_test_customer(
    db,
    full_name="Test Customer",
):
    unique_id = uuid4().hex[:8]

    user = User(
        full_name=full_name,
        email=f"customer_{unique_id}@example.com",
        phone=f"98765{unique_id[:5]}",
        password_hash="hashed_password",
        role="Customer",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    customer = Customer(
        user_id=user.id,
        customer_number=f"CUST{unique_id.upper()}",
        full_name=full_name,
        email=user.email,
        phone=user.phone,
        address="Chennai",
        connection_type="Domestic",
        connection_number=f"CONN{unique_id.upper()}",
        status="Active",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def create_test_connection(db, customer):
    unique_id = uuid4().hex[:8].upper()

    connection = Connection(
        customer_id=customer.id,
        connection_number=f"CONN-{unique_id}",
        meter_number=f"MTR-{unique_id}",
        meter_type="Digital",
        tariff_type="Domestic",
        connection_type="Domestic",
        sanctioned_load=5.0,
        status="Active",
    )

    db.add(connection)
    db.commit()
    db.refresh(connection)

    return connection


def get_test_db():
    override = app.dependency_overrides.get(get_db)

    if override is None:
        raise RuntimeError(
            "Test database override is not configured."
        )

    db_generator = override()
    db = next(db_generator)

    return db, db_generator


def test_create_service_request():
    db, db_generator = get_test_db()

    try:
        customer = create_test_customer(db)

        response = client.post(
            "/service-requests",
            json={
                "customer_id": customer.id,
                "request_type": "New Connection",
                "description": "I need a new electricity connection.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["customer_id"] == customer.id
        assert data["request_type"] == "New Connection"
        assert data["status"] == "Submitted"
        assert data["request_number"].startswith("SR-")

    finally:
        db_generator.close()


def test_create_service_request_with_connection():
    db, db_generator = get_test_db()

    try:
        customer = create_test_customer(db)
        connection = create_test_connection(db, customer)

        response = client.post(
            "/service-requests",
            json={
                "customer_id": customer.id,
                "connection_id": connection.id,
                "request_type": "Meter Replacement",
                "description": "My electricity meter needs replacement.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["customer_id"] == customer.id
        assert data["connection_id"] == connection.id
        assert data["request_type"] == "Meter Replacement"
        assert data["status"] == "Submitted"

    finally:
        db_generator.close()


def test_create_service_request_customer_not_found():
    response = client.post(
        "/service-requests",
        json={
            "customer_id": 99999,
            "request_type": "New Connection",
            "description": "I need a new electricity connection.",
            "requested_date": datetime.now().isoformat(),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_create_service_request_connection_not_found():
    db, db_generator = get_test_db()

    try:
        customer = create_test_customer(db)

        response = client.post(
            "/service-requests",
            json={
                "customer_id": customer.id,
                "connection_id": 99999,
                "request_type": "Meter Replacement",
                "description": "Please replace my meter.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Connection not found"

    finally:
        db_generator.close()


def test_create_service_request_invalid_type():
    db, db_generator = get_test_db()

    try:
        customer = create_test_customer(db)

        response = client.post(
            "/service-requests",
            json={
                "customer_id": customer.id,
                "request_type": "Invalid Request Type",
                "description": "This is an invalid service request.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Invalid service request type"
        )

    finally:
        db_generator.close()


def test_get_service_request():
    db, db_generator = get_test_db()

    try:
        customer = create_test_customer(db)

        response = client.post(
            "/service-requests",
            json={
                "customer_id": customer.id,
                "request_type": "Address Change",
                "description": "I need to update my address.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 201

        request_id = response.json()["id"]

        response = client.get(
            f"/service-requests/{request_id}"
        )

        assert response.status_code == 200
        assert response.json()["id"] == request_id

    finally:
        db_generator.close()


def test_get_service_request_not_found():
    response = client.get(
        "/service-requests/99999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Service request not found"
    )


def test_list_service_requests():
    db, db_generator = get_test_db()

    try:
        customer = create_test_customer(db)

        response = client.post(
            "/service-requests",
            json={
                "customer_id": customer.id,
                "request_type": "Name Change",
                "description": "I need to change the customer name.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 201

        response = client.get(
            "/service-requests"
        )

        assert response.status_code == 200

        data = response.json()

        assert isinstance(data["items"], list)
        assert data["total"] >= 1
        assert data["page"] == 1
        assert data["page_size"] == 10

    finally:
        db_generator.close()


def test_list_service_requests_by_customer():
    db, db_generator = get_test_db()

    try:
        customer = create_test_customer(db)

        client.post(
            "/service-requests",
            json={
                "customer_id": customer.id,
                "request_type": "Load Enhancement",
                "description": "I need higher sanctioned load.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        response = client.get(
            f"/service-requests?customer_id={customer.id}"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["total"] >= 1

        for item in data["items"]:
            assert item["customer_id"] == customer.id

    finally:
        db_generator.close()


def test_review_service_request():
    db, db_generator = get_test_db()

    try:
        customer = create_test_customer(db)

        response = client.post(
            "/service-requests",
            json={
                "customer_id": customer.id,
                "request_type": "Load Reduction",
                "description": "I need to reduce my sanctioned load.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 201

        request_id = response.json()["id"]

        response = client.put(
            f"/service-requests/{request_id}/review"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "Under Review"

    finally:
        db_generator.close()


def test_approve_service_request():
    db, db_generator = get_test_db()

    try:
        customer = create_test_customer(db)

        response = client.post(
            "/service-requests",
            json={
                "customer_id": customer.id,
                "request_type": "New Connection",
                "description": "Please provide a new connection.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 201

        request_id = response.json()["id"]

        response = client.put(
            f"/service-requests/{request_id}/review"
        )

        assert response.status_code == 200

        response = client.put(
            f"/service-requests/{request_id}/approve"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "Approved"

    finally:
        db_generator.close()


def test_reject_service_request():
    db, db_generator = get_test_db()

    try:
        customer = create_test_customer(db)

        response = client.post(
            "/service-requests",
            json={
                "customer_id": customer.id,
                "request_type": "Disconnection",
                "description": "Please disconnect my electricity.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 201

        request_id = response.json()["id"]

        response = client.put(
            f"/service-requests/{request_id}/review"
        )

        assert response.status_code == 200

        response = client.put(
            f"/service-requests/{request_id}/reject"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "Rejected"

    finally:
        db_generator.close()


def test_complete_service_request():
    db, db_generator = get_test_db()

    try:
        customer = create_test_customer(db)

        response = client.post(
            "/service-requests",
            json={
                "customer_id": customer.id,
                "request_type": "Meter Replacement",
                "description": "Please replace my damaged meter.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 201

        request_id = response.json()["id"]

        response = client.put(
            f"/service-requests/{request_id}/review"
        )

        assert response.status_code == 200

        response = client.put(
            f"/service-requests/{request_id}/approve"
        )

        assert response.status_code == 200

        response = client.put(
            f"/service-requests/{request_id}/complete"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "Completed"

    finally:
        db_generator.close()


def test_invalid_status_transition():
    db, db_generator = get_test_db()

    try:
        customer = create_test_customer(db)

        response = client.post(
            "/service-requests",
            json={
                "customer_id": customer.id,
                "request_type": "New Connection",
                "description": "Please provide a new connection.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 201

        request_id = response.json()["id"]

        response = client.put(
            f"/service-requests/{request_id}/complete"
        )

        assert response.status_code == 400

    finally:
        db_generator.close()


def test_connection_belongs_to_different_customer():
    db, db_generator = get_test_db()

    try:
        customer_one = create_test_customer(
            db,
            "Customer One",
        )

        customer_two = create_test_customer(
            db,
            "Customer Two",
        )

        connection = create_test_connection(
            db,
            customer_one,
        )

        response = client.post(
            "/service-requests",
            json={
                "customer_id": customer_two.id,
                "connection_id": connection.id,
                "request_type": "Meter Replacement",
                "description": "Please replace my meter.",
                "requested_date": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 400

        assert response.json()["detail"] == (
            "Connection does not belong to this customer"
        )

    finally:
        db_generator.close()