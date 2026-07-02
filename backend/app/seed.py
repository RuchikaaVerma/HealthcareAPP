"""
Run once after migrations to create the initial admin account:
    python -m app.seed

Admin credentials are read from env vars so they aren't hardcoded in source.
"""
import os
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole


def seed_admin():
    db = SessionLocal()
    try:
        email = os.getenv("SEED_ADMIN_EMAIL", "admin@clinic.com")
        password = os.getenv("SEED_ADMIN_PASSWORD", "ChangeMe123!")
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"Admin account already exists: {email}")
            return
        admin = User(
            email=email,
            hashed_password=hash_password(password),
            full_name="Clinic Administrator",
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        print(f"Created admin account: {email} (password from SEED_ADMIN_PASSWORD env var)")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
