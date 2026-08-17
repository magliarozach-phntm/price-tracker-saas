from sqlalchemy import select
from werkzeug.security import generate_password_hash

from app.core.database import SessionLocal
from app.models import User


db = SessionLocal()

try:
    stmt = select(User).where(
        User.email == "admin@admin.com"
    )

    existing_user = db.execute(
        stmt
    ).scalar_one_or_none()

    if existing_user:
        print(
            f"User already exists with ID {existing_user.id}"
        )

    else:
        admin_user = User(
            email="admin@admin.com",
            password_hash=generate_password_hash(
                "unhashed_password"
            ),
            name="admin",
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print(
            f"Created admin user with ID {admin_user.id}"
        )

except Exception as e:
    db.rollback()
    print(e)

finally:
    db.close()