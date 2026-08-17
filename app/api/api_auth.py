from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import verify_password, get_current_user
from app.core.database import get_db
from app.core.security import hash_password
from app.models import User
from app.schemas.user import UserCreate, UserLogin

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register")
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = db.execute(
        select(User).where(
            User.email == user.email
        )
    ).scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    new_user = User(
        email=user.email,
        password_hash=hash_password(
            user.password
        ),
        name=user.name,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception:
        db.rollback()
        raise

    return {
        "id": new_user.id,
        "email": new_user.email,
        "name": new_user.name,
    }

@router.post("/login")
def login(
    request: Request,
    user: UserLogin,
    db: Session = Depends(get_db),
):
    existing_user = db.execute(
        select(User).where(
            User.email == user.email
        )
    ).scalar_one_or_none()

    if existing_user is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    if not verify_password(
        user.password,
        existing_user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    request.session["user_id"] = existing_user.id


    return {
        "id": existing_user.id,
        "email": existing_user.email,
        "name": existing_user.name,
    }

@router.post("/logout")
def logout(request: Request):
    request.session.clear()

    return {
        "message": "Logged out"
    }

@router.get('/me')
def me(
        current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
    }