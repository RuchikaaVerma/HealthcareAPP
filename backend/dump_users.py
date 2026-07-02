from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    users = db.query(User).all()
    print("Users in database:")
    for u in users:
        print(f" - {u.email} (Role: {u.role})")
finally:
    db.close()
