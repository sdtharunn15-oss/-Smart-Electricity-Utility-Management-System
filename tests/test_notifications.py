from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_user():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Notification Test User",
            "email": "notification_test@example.com",
            "phone": "9876501234",
            "password": "Test@123",
            "role": "Customer",
        },
    )

    if response.status_code == 201:
        return response.json()

    return None


def test_create_notification():
    user = create_user()

    assert user is not None

    user_id = user["id"]

    response = client.post(
        "/notifications",
        json={
            "user_id": user_id,
            "title": "Test Notification",
            "message": "This is a test notification.",
            "notification_type": "System",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == user_id
    assert data["title"] == "Test Notification"
    assert data["message"] == "This is a test notification."
    assert data["notification_type"] == "System"
    assert data["is_read"] is False


def test_create_notification_user_not_found():
    response = client.post(
        "/notifications",
        json={
            "user_id": 99999,
            "title": "Test Notification",
            "message": "User does not exist.",
            "notification_type": "System",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_notification():
    user = create_user()

    assert user is not None

    response = client.post(
        "/notifications",
        json={
            "user_id": user["id"],
            "title": "Get Test",
            "message": "Testing get notification.",
            "notification_type": "System",
        },
    )

    assert response.status_code == 201

    notification_id = response.json()["id"]

    response = client.get(
        f"/notifications/{notification_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == notification_id


def test_get_notification_not_found():
    response = client.get(
        "/notifications/99999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"


def test_list_notifications():
    user = create_user()

    assert user is not None

    response = client.post(
        "/notifications",
        json={
            "user_id": user["id"],
            "title": "List Test",
            "message": "Testing notification list.",
            "notification_type": "System",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/notifications"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["items"], list)
    assert data["total"] >= 1
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_list_notifications_by_user():
    user = create_user()

    assert user is not None

    response = client.post(
        "/notifications",
        json={
            "user_id": user["id"],
            "title": "User Filter Test",
            "message": "Testing user filter.",
            "notification_type": "System",
        },
    )

    assert response.status_code == 201

    response = client.get(
        f"/notifications?user_id={user['id']}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    for notification in data["items"]:
        assert notification["user_id"] == user["id"]


def test_list_unread_notifications():
    user = create_user()

    assert user is not None

    response = client.post(
        "/notifications",
        json={
            "user_id": user["id"],
            "title": "Unread Test",
            "message": "Testing unread filter.",
            "notification_type": "Alert",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/notifications?is_read=false"
    )

    assert response.status_code == 200

    data = response.json()

    for notification in data["items"]:
        assert notification["is_read"] is False


def test_list_notifications_by_type():
    user = create_user()

    assert user is not None

    response = client.post(
        "/notifications",
        json={
            "user_id": user["id"],
            "title": "Type Test",
            "message": "Testing notification type.",
            "notification_type": "Billing",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/notifications?notification_type=Billing"
    )

    assert response.status_code == 200

    data = response.json()

    for notification in data["items"]:
        assert notification["notification_type"] == "Billing"


def test_mark_notification_as_read():
    user = create_user()

    assert user is not None

    response = client.post(
        "/notifications",
        json={
            "user_id": user["id"],
            "title": "Read Test",
            "message": "Testing mark as read.",
            "notification_type": "System",
        },
    )

    assert response.status_code == 201

    notification_id = response.json()["id"]

    assert response.json()["is_read"] is False

    response = client.patch(
        f"/notifications/{notification_id}/read"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == notification_id
    assert data["is_read"] is True


def test_mark_notification_as_read_not_found():
    response = client.patch(
        "/notifications/99999/read"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"


def test_delete_notification():
    user = create_user()

    assert user is not None

    response = client.post(
        "/notifications",
        json={
            "user_id": user["id"],
            "title": "Delete Test",
            "message": "Testing notification deletion.",
            "notification_type": "System",
        },
    )

    assert response.status_code == 201

    notification_id = response.json()["id"]

    response = client.delete(
        f"/notifications/{notification_id}"
    )

    assert response.status_code == 204

    response = client.get(
        f"/notifications/{notification_id}"
    )

    assert response.status_code == 404


def test_delete_notification_not_found():
    response = client.delete(
        "/notifications/99999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Notification not found"