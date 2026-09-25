from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_user():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Technician Test User",
            "email": "technician_test@example.com",
            "phone": "9876501111",
            "password": "Test@123",
            "role": "Technician",
        },
    )

    if response.status_code == 201:
        return response.json()

    return None


def test_create_technician():
    user = create_user()

    assert user is not None

    response = client.post(
        "/technicians",
        json={
            "user_id": user["id"],
            "employee_code": "TECH001",
            "specialization": "Electrical",
            "phone": "9876502222",
            "status": "Available",
            "notes": "Experienced technician",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == user["id"]
    assert data["employee_code"] == "TECH001"
    assert data["specialization"] == "Electrical"
    assert data["phone"] == "9876502222"
    assert data["status"] == "Available"
    assert data["notes"] == "Experienced technician"


def test_create_technician_invalid_status():
    user = create_user()

    assert user is not None

    response = client.post(
        "/technicians",
        json={
            "user_id": user["id"],
            "employee_code": "TECH002",
            "specialization": "Electrical",
            "phone": "9876503333",
            "status": "Invalid",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid technician status"


def test_create_duplicate_employee_code():
    user1 = create_user()

    assert user1 is not None

    response = client.post(
        "/technicians",
        json={
            "user_id": user1["id"],
            "employee_code": "TECH003",
            "specialization": "Electrical",
            "phone": "9876504444",
            "status": "Available",
        },
    )

    assert response.status_code == 201

    user2 = client.post(
        "/auth/register",
        json={
            "full_name": "Second Technician",
            "email": "technician_second@example.com",
            "phone": "9876505555",
            "password": "Test@123",
            "role": "Technician",
        },
    )

    assert user2.status_code == 201

    response = client.post(
        "/technicians",
        json={
            "user_id": user2.json()["id"],
            "employee_code": "TECH003",
            "specialization": "Meter",
            "phone": "9876506666",
            "status": "Available",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Employee code already exists"


def test_create_duplicate_technician_for_user():
    user = create_user()

    assert user is not None

    response = client.post(
        "/technicians",
        json={
            "user_id": user["id"],
            "employee_code": "TECH004",
            "specialization": "Electrical",
            "phone": "9876507777",
            "status": "Available",
        },
    )

    assert response.status_code == 201

    response = client.post(
        "/technicians",
        json={
            "user_id": user["id"],
            "employee_code": "TECH005",
            "specialization": "Meter",
            "phone": "9876508888",
            "status": "Available",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Technician profile already exists for this user"
    )


def test_get_technician():
    user = create_user()

    assert user is not None

    response = client.post(
        "/technicians",
        json={
            "user_id": user["id"],
            "employee_code": "TECH006",
            "specialization": "Electrical",
            "phone": "9876509999",
            "status": "Available",
        },
    )

    assert response.status_code == 201

    technician_id = response.json()["id"]

    response = client.get(
        f"/technicians/{technician_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == technician_id


def test_get_technician_not_found():
    response = client.get(
        "/technicians/99999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Technician not found"


def test_list_technicians():
    user = create_user()

    assert user is not None

    response = client.post(
        "/technicians",
        json={
            "user_id": user["id"],
            "employee_code": "TECH007",
            "specialization": "Electrical",
            "phone": "9876510000",
            "status": "Available",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/technicians"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_technicians_by_status():
    user = create_user()

    assert user is not None

    response = client.post(
        "/technicians",
        json={
            "user_id": user["id"],
            "employee_code": "TECH008",
            "specialization": "Electrical",
            "phone": "9876511111",
            "status": "Busy",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/technicians?status=Busy"
    )

    assert response.status_code == 200

    data = response.json()

    for technician in data:
        assert technician["status"] == "Busy"


def test_list_technicians_by_specialization():
    user = create_user()

    assert user is not None

    response = client.post(
        "/technicians",
        json={
            "user_id": user["id"],
            "employee_code": "TECH009",
            "specialization": "Meter",
            "phone": "9876512222",
            "status": "Available",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/technicians?specialization=Meter"
    )

    assert response.status_code == 200

    data = response.json()

    for technician in data:
        assert technician["specialization"] == "Meter"


def test_update_technician():
    user = create_user()

    assert user is not None

    response = client.post(
        "/technicians",
        json={
            "user_id": user["id"],
            "employee_code": "TECH010",
            "specialization": "Electrical",
            "phone": "9876513333",
            "status": "Available",
        },
    )

    assert response.status_code == 201

    technician_id = response.json()["id"]

    response = client.put(
        f"/technicians/{technician_id}",
        json={
            "specialization": "Meter",
            "phone": "9876514444",
            "status": "Busy",
            "notes": "Currently assigned to field work",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["specialization"] == "Meter"
    assert data["phone"] == "9876514444"
    assert data["status"] == "Busy"
    assert data["notes"] == "Currently assigned to field work"


def test_update_technician_invalid_status():
    user = create_user()

    assert user is not None

    response = client.post(
        "/technicians",
        json={
            "user_id": user["id"],
            "employee_code": "TECH011",
            "specialization": "Electrical",
            "phone": "9876515555",
            "status": "Available",
        },
    )

    assert response.status_code == 201

    technician_id = response.json()["id"]

    response = client.put(
        f"/technicians/{technician_id}",
        json={
            "status": "Invalid",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid technician status"


def test_update_technician_not_found():
    response = client.put(
        "/technicians/99999",
        json={
            "status": "Busy",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Technician not found"


def test_delete_technician():
    user = create_user()

    assert user is not None

    response = client.post(
        "/technicians",
        json={
            "user_id": user["id"],
            "employee_code": "TECH012",
            "specialization": "Electrical",
            "phone": "9876516666",
            "status": "Available",
        },
    )

    assert response.status_code == 201

    technician_id = response.json()["id"]

    response = client.delete(
        f"/technicians/{technician_id}"
    )

    assert response.status_code == 204

    response = client.get(
        f"/technicians/{technician_id}"
    )

    assert response.status_code == 404


def test_delete_technician_not_found():
    response = client.delete(
        "/technicians/99999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Technician not found"