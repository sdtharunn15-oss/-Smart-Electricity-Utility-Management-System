from app.database import Base, SessionLocal, engine
from app.models.user import User
from app.utils.security import hash_password


Base.metadata.create_all(bind=engine)

db = SessionLocal()

existing_admin = (
    db.query(User)
    .filter(User.email == "admin@electricity.com")
    .first()
)

if existing_admin:
    print("Super Admin already exists.")
else:
    admin = User(
        full_name="System Administrator",
        email="admin@electricity.com",
        phone="9000000000",
        password_hash=hash_password("Admin@12345"),
        role="Super Admin",
        is_active=True,
    )

    db.add(admin)
    db.commit()

    print("Super Admin created successfully.")

db.close()
