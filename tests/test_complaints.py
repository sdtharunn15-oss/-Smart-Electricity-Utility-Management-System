from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_customer():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Test Customer",
            "email": "complaint@example.com",
            "phone": "9876543210",
            "password": "Test@123",
            "role": "Customer",
        },
    )

    assert response.status_code in [201, 400]

    return 1


def create_complaint():
    create_customer()

    response = client.post(
        "/complaints",
        json={
            "customer_id": 1,
            "subject": "Power outage",
            "description": "Power is not available in my area.",
            "priority": "High",
        },
    )

    return response


def test_create_complaint():
    response = create_complaint()

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == 1
    assert data["subject"] == "Power outage"
    assert data["description"] == (
        "Power is not available in my area."
    )
    assert data["priority"] == "High"
    assert data["status"] == "Open"


def test_get_complaint():
    response = create_complaint()

    assert response.status_code == 201

    complaint_id = response.json()["id"]

    response = client.get(
        f"/complaints/{complaint_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == complaint_id


def test_get_complaint_not_found():
    response = client.get(
        "/complaints/99999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Complaint not found"
    )


def test_list_complaints():
    response = create_complaint()

    assert response.status_code == 201

    response = client.get(
        "/complaints"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_update_complaint():
    response = create_complaint()

    assert response.status_code == 201

    complaint_id = response.json()["id"]

    response = client.put(
        f"/complaints/{complaint_id}",
        json={
            "status": "Resolved",
            "priority": "High",
            "resolution": (
                "Power issue has been resolved."
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Resolved"
    assert data["priority"] == "High"
    assert data["resolution"] == (
        "Power issue has been resolved."
    )


def test_delete_complaint():
    response = create_complaint()

    assert response.status_code == 201

    complaint_id = response.json()["id"]

    response = client.delete(
        f"/complaints/{complaint_id}"
    )

    assert response.status_code == 204

    response = client.get(
        f"/complaints/{complaint_id}"
    )

    assert response.status_code == 404