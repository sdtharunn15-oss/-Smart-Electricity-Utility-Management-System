Smart Electricity Utility Management System

Project Overview

Smart Electricity Utility is a FastAPI-based backend application for managing electricity utility operations. The system provides APIs for customer management, electricity connections, meter readings, tariffs, billing, payments, service requests, complaints, notifications, technicians, authentication, and analytics.

The application follows a layered architecture using FastAPI, SQLAlchemy, Pydantic, SQLite, and Alembic.

The project includes automated API tests using pytest and currently has 139 passing tests.

Technology Stack

* Python 3.10+
* FastAPI
* SQLAlchemy
* Pydantic
* Pydantic Settings
* SQLite
* Alembic
* Uvicorn
* Pytest
* Passlib
* Bcrypt
* JWT Authentication

Project Structure

```text
smart-electricity-utility/
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   ├── script.py.mako
│   └── README
│
├── app/
│   ├── models/
│   │   ├── user.py
│   │   ├── customer.py
│   │   ├── connection.py
│   │   ├── meter_reading.py
│   │   ├── tariff.py
│   │   ├── bill.py
│   │   ├── payment.py
│   │   ├── service_request.py
│   │   ├── notification.py
│   │   ├── technician.py
│   │   └── complaint.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── customer.py
│   │   ├── connection.py
│   │   ├── meter_reading.py
│   │   ├── tariff.py
│   │   ├── bill.py
│   │   ├── payment.py
│   │   ├── service_request.py
│   │   ├── notification.py
│   │   ├── technician.py
│   │   ├── complaint.py
│   │   └── analytics.py
│   │
│   ├── repositories/
│   │   ├── customer_repository.py
│   │   ├── connection_repository.py
│   │   ├── meter_reading_repository.py
│   │   ├── tariff_repository.py
│   │   ├── bill_repository.py
│   │   ├── payment_repository.py
│   │   ├── service_request_repository.py
│   │   ├── notification_repository.py
│   │   ├── technician_repository.py
│   │   └── complaint_repository.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── customer_service.py
│   │   ├── connection_service.py
│   │   ├── meter_reading_service.py
│   │   ├── tariff_service.py
│   │   ├── bill_service.py
│   │   ├── payment_service.py
│   │   ├── service_request_service.py
│   │   ├── notification_service.py
│   │   ├── technician_service.py
│   │   ├── complaint_service.py
│   │   └── analytics_service.py
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── customers.py
│   │   ├── connections.py
│   │   ├── meter_readings.py
│   │   ├── tariffs.py
│   │   ├── bills.py
│   │   ├── payments.py
│   │   ├── service_requests.py
│   │   ├── notifications.py
│   │   ├── technicians.py
│   │   ├── complaints.py
│   │   └── analytics.py
│   │
│   ├── utils/
│   │   └── security.py
│   │
│   ├── database.py
│   └── main.py
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_customers.py
│   ├── test_connections.py
│   ├── test_meter_readings.py
│   ├── test_tariffs.py
│   ├── test_bills.py
│   ├── test_payments.py
│   ├── test_service_requests.py
│   ├── test_notifications.py
│   ├── test_technicians.py
│   ├── test_complaints.py
│   └── test_analytics.py
│
├── create_admin.py
├── alembic.ini
├── requirements.txt
├── .env
├── .env.example
└── electricity_utility.db
```

Architecture

The application follows a layered architecture.

Client

The client communicates with the FastAPI application through REST APIs.

API Routes

The route layer handles HTTP requests, validates input through Pydantic schemas, calls the appropriate service functions, and returns API responses.

Services

The service layer contains the application's business logic. It handles operations such as creating customers, calculating meter consumption, creating bills, processing payments, changing request statuses, and generating analytics.

Repositories

The repository layer handles database operations using SQLAlchemy.

Models

SQLAlchemy models represent the database tables and relationships.

Database

SQLite is used as the application database.

Authentication and Security

The application provides authentication functionality using JWT-based authentication and password hashing.

Authentication functionality includes:

* User registration
* User login
* Access token generation
* Refresh token handling
* Current user information
* Password hashing
* Active/inactive user validation
* Role-based user information

Passwords are stored using password hashes rather than plain-text passwords.

Main Functional Modules

Authentication

Provides user registration, login, token handling, and authenticated user information.

Customer Management

Provides functionality for:

* Creating customers
* Viewing customers
* Updating customer information
* Listing customers
* Customer status management
* Customer-related electricity information

Electricity Connections

Provides functionality for:

* Creating electricity connections
* Viewing connections
* Updating connections
* Listing connections
* Filtering connections
* Pagination
* Connection status management
* Deleting connections

Meter Readings

Provides functionality for:

* Creating meter readings
* Viewing meter readings
* Listing meter readings
* Filtering readings by connection
* Updating readings
* Deleting readings
* Automatic consumption calculation

Meter consumption is calculated using the current meter reading and the previous reading.

For example:

```text
Previous Reading = 100
Current Reading  = 150
Consumption      = 50 units
```

Tariff Management

Provides functionality for:

* Creating tariffs
* Viewing tariffs
* Listing tariffs
* Filtering tariffs by connection type
* Filtering tariffs by effective date
* Updating tariffs
* Deleting tariffs

Billing

Provides functionality for:

* Creating bills
* Viewing bills
* Listing bills
* Filtering bills
* Filtering by customer
* Filtering by connection
* Filtering by billing month
* Filtering overdue bills
* Filtering by amount
* Pagination
* Sorting
* Updating bill status

Payment Management

Provides functionality for:

* Creating payments
* Viewing payments
* Listing payments
* Filtering payments by bill
* Filtering payments by status
* Pagination

Service Requests

Provides functionality for:

* Creating service requests
* Viewing service requests
* Listing service requests
* Filtering service requests
* Approving requests
* Rejecting requests
* Completing requests
* Moving requests to review status
* Pagination

Complaint Management

Provides functionality for:

* Creating complaints
* Viewing complaints
* Listing complaints
* Filtering complaints by customer
* Filtering complaints by status
* Filtering complaints by priority
* Pagination
* Updating complaints
* Deleting complaints

Notification Management

Provides functionality for managing customer notifications related to utility operations.

Technician Management

Provides functionality for managing technicians and technician-related utility operations.

Analytics

The analytics module provides utility-level and customer-level usage information.

Available analytics include:

* Dashboard statistics
* Monthly consumption by connection
* Yearly consumption
* Connection usage
* Customer usage
* Highest consuming connections
* Average monthly consumption

Dashboard information includes:

* Total customers
* Active connections
* Total units consumed
* Total bills
* Paid bills
* Unpaid bills
* Total revenue
* Open service requests

API Documentation

FastAPI automatically provides interactive API documentation.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

Running the Application

Create and activate the virtual environment.

Windows PowerShell:

```powershell
python -m venv venv
```

Activate the environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Environment Configuration

Create a `.env` file in the project root.

Example configuration:

```text
DATABASE_URL=sqlite:///./electricity_utility.db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Database Migration

Check the current Alembic migration:

```powershell
alembic current
```

Check the latest migration:

```powershell
alembic heads
```

Apply migrations:

```powershell
alembic upgrade head
```

Create a new migration after model changes:

```powershell
alembic revision --autogenerate -m "update database"
```

Run the Application

Start the FastAPI server using Uvicorn:

```powershell
uvicorn app.main:app --reload
```

The application will be available at:

```text
http://127.0.0.1:8000
```

API documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

Creating an Admin User

The project includes a `create_admin.py` script for creating an administrator account.

Run:

```powershell
python create_admin.py
```

Testing

The project uses pytest for automated testing.

Run the complete test suite:

```powershell
pytest -q
```

Current test result:

```text
139 passed, 122 warnings
```

The test suite covers the main application modules, including:

* Authentication
* Customers
* Electricity connections
* Meter readings
* Tariffs
* Bills
* Payments
* Service requests
* Notifications
* Technicians
* Complaints
* Analytics

Test Database

Tests use an isolated SQLite test database with SQLAlchemy and StaticPool where required.

Test data is created and cleaned for individual test modules so that tests remain independent.

Database

The application uses SQLite for development and assignment purposes.

Main database file:

```text
electricity_utility.db
```

The database contains entities related to:

* Users
* Customers
* Electricity connections
* Meter readings
* Tariffs
* Bills
* Payments
* Service requests
* Notifications
* Technicians
* Complaints

Database migrations are managed through Alembic.

Current Migration Status

Current Alembic revision:

```text
ed8d5ed6a0dd
```

Migration head:

```text
ed8d5ed6a0dd
```

The current database revision is synchronized with the Alembic head.

API Endpoint Groups

Authentication:

```text
/auth
```

Users:

```text
/users
```

Customers:

```text
/customers
```

Electricity Connections:

```text
/connections
```

Meter Readings:

```text
/meter-readings
```

Tariffs:

```text
/tariffs
```

Bills:

```text
/bills
```

Payments:

```text
/payments
```

Service Requests:

```text
/service-requests
```

Notifications:

```text
/notifications
```

Technicians:

```text
/technicians
```

Complaints:

```text
/complaints
```

Analytics:

```text
/analytics
```

Example API Flow

A typical electricity usage workflow is:

```text
Customer
    |
    v
Electricity Connection
    |
    v
Meter Reading
    |
    v
Consumption Calculation
    |
    v
Bill Generation
    |
    v
Payment
    |
    v
Revenue and Analytics
```

Service request workflow:

```text
Customer
    |
    v
Service Request
    |
    v
Under Review
    |
    +----> Approved
    |
    +----> Rejected
    |
    v
Completed
```

Development Guidelines

The project separates responsibilities between different layers.

Routes should handle:

* HTTP requests
* Request parameters
* Dependency injection
* Response models
* HTTP errors

Services should handle:

* Business logic
* Validation rules
* Status transitions
* Calculations

Repositories should handle:

* Database queries
* Database filtering
* Pagination
* Sorting
* CRUD operations

Models should handle:

* Database table definitions
* Relationships
* Database constraints

Schemas should handle:

* Request validation
* Response serialization
* API data structures

Error Handling

The API uses standard HTTP status codes.

Common status codes include:

```text
200 OK
201 Created
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
422 Unprocessable Entity
500 Internal Server Error
```

Validation errors are handled through FastAPI and Pydantic validation.

Security Considerations

The application implements:

* Password hashing
* JWT authentication
* Active user validation
* Role information
* Request validation
* Database constraints
* Input validation through Pydantic

Sensitive configuration values should be stored in environment variables and should not be committed to source control.

Project Verification

The application has been verified using the automated test suite.

Latest verification:

```text
139 passed
122 warnings
0 failed
```

Database migration verification:

```text
Current revision: ed8d5ed6a0dd
Head revision:    ed8d5ed6a0dd
```

The successful test suite confirms that the implemented API functionality covered by the tests is working as expected.

Future Improvements

Possible future improvements include:

* PostgreSQL production database support
* Redis-based caching
* Background notification processing
* SMS and email notifications
* Online payment gateway integration
* Advanced consumption forecasting
* Role-specific dashboards
* Real-time meter data integration
* Docker deployment
* CI/CD pipeline
* Production monitoring and logging

Project Status

The core Smart Electricity Utility backend implementation is complete and the automated test suite is passing.

The remaining submission activities are documentation and project artifacts such as the final README, ER diagram, architecture diagram, and final submission packaging.

License

This project was developed as an academic/assignment project.
