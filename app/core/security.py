from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    user = db.get(User, user_id)

    if user is None:
        request.session.clear()

        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user

def get_session_user(
    request: Request,
    db: Session,
) -> User | None:
    user_id = request.session.get("user_id")

    if user_id is None:
        return None

    user = db.get(User, user_id)

    if user is None:
        request.session.clear()
        return None

    return user


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(
        password_hash,
        password
    )