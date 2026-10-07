from database import SessionLocal
from models.user import UserModel

def create_admin():
    db = SessionLocal()

    existing = db.query(UserModel).filter(UserModel.username == "admin").first()
    if existing:
        print("Admin already exists:", existing.username)
        db.close()
        return

    admin = UserModel(
        username="admin",
        email="admin@wheezes.com",
        role="admin"
    )
    admin.set_password("123")

    db.add(admin)
    db.commit()
    db.refresh(admin)

    print("Admin created successfully:")
    print("  username:", admin.username)
    print("  email:", admin.email)
    print("  role:", admin.role)

    db.close()

if __name__ == "__main__":
    create_admin()
