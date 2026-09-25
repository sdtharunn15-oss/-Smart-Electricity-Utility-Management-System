import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

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
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_database():
    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clean_database():
    db = TestingSessionLocal()

    for model in [
        Payment,
        Bill,
        MeterReading,
        ServiceRequest,
        Notification,
        Complaint,
        Connection,
        Tariff,
        Technician,
        Customer,
        User,
    ]:
        db.query(model).delete()

    db.commit()
    db.close()