
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.utils.security import hash_password

# Import all models before creating the test database tables.
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

    db = TestingSessionLocal()

    # Clear users before every test.
    db.query(User).delete()
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


def register_customer(
    email="customer@example.com",
    password="Test@12345",
):
    return client.post(
        "/auth/register",
        json={
            "full_name": "Test Customer",
            "email": email,
            "phone": "9876543210",
            "password": password,
        },
    )


def login(
    email="customer@example.com",
    password="Test@12345",
):
    return client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def test_register_customer():
    response = register_customer()

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Test Customer"
    assert data["email"] == "customer@example.com"
    assert data["role"] == "Customer"
    assert data["is_active"] is True


def test_duplicate_email_is_rejected():
    first = register_customer()

    assert first.status_code == 201

    second = register_customer()

    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"


def test_duplicate_phone_is_rejected():
    first = register_customer()

    assert first.status_code == 201

    second = register_customer(
        email="another@example.com",
    )

    assert second.status_code == 400
    assert second.json()["detail"] == "Phone already registered"


def test_login_success():
    register_customer()

    response = login()

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    register_customer()

    response = login(
        password="WrongPassword@123",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_unknown_email():
    response = login(
        email="unknown@example.com",
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_get_current_user():
    register_customer()

    login_response = login()

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "customer@example.com"
    assert data["role"] == "Customer"


def test_me_without_token():
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_refresh_token():
    register_customer()

    login_response = login()

    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data


def test_access_token_cannot_be_used_as_refresh_token():
    register_customer()

    login_response = login()

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": access_token,
        },
    )

    assert response.status_code == 401


def test_change_password():
    register_customer()

    login_response = login()

    access_token = login_response.json()["access_token"]

    response = client.put(
        "/auth/change-password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "Test@12345",
            "new_password": "NewTest@12345",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"

    new_login = login(
        password="NewTest@12345",
    )

    assert new_login.status_code == 200


def test_change_password_wrong_current_password():
    register_customer()

    login_response = login()

    access_token = login_response.json()["access_token"]

    response = client.put(
        "/auth/change-password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "WrongPassword@123",
            "new_password": "NewTest@12345",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect"


def test_change_password_same_password():
    register_customer()

    login_response = login()

    access_token = login_response.json()["access_token"]

    response = client.put(
        "/auth/change-password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "Test@12345",
            "new_password": "Test@12345",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "New password must be different"


def create_admin():
    db = TestingSessionLocal()

    admin = User(
        full_name="System Administrator",
        email="admin@test.com",
        phone="9000000000",
        password_hash=hash_password("Admin@12345"),
        role="Super Admin",
        is_active=True,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    admin_id = admin.id

    db.close()

    return admin_id
