from fastapi import APIRouter, Depends, Request, Form
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
from app.web.flash import add_flash
from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models import User
from app.web import templates
from app.web.context import template_context

router = APIRouter()


@router.get('/login')
def login_page(
        request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=template_context(
            current_user=None
        )
    )

@router.post('/login')
def login(
        request: Request,
        email: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db),
):
    email = email.strip().lower()

    existing_user = db.execute(
        select(User).where(
            User.email == email
        )
    ).scalar_one_or_none()

    if (
        existing_user is None
        or not verify_password(
        password,
        existing_user.password_hash
        )
    ):
        return templates.TemplateResponse(
            request=request,
            name='login.html',
            context={
                'error': 'Incorrect email or password',
            },
            status_code=401
        )
    request.session['user_id'] = existing_user.id

    return RedirectResponse(
        url='/dashboard',
        status_code=303
    )

@router.get('/register')
def register_page(
        request: Request,
):
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context=template_context(
            request=request,
            current_user=None
        )
    )

@router.post('/register')
def register(
        request: Request,
        name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        confirm_password: str = Form(...),
        db: Session = Depends(get_db)
):
    email = email.strip().lower()

    existing_user = db.execute(
        select(User).where(
            User.email == email
        )
    ).scalar_one_or_none()

    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name='register.html',
            context={
                'error': 'Email already registered'
            },
            status_code=409
        )

    new_user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
    )
    if password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context=template_context(
                request=request,
                error="Passwords do not match.",
            ),
        )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception:
        db.rollback()
        raise

    request.session['user_id'] = new_user.id

    return RedirectResponse(
        url='/dashboard',
        status_code=303
    )

@router.post('/logout')
def logout(
        request: Request,
):
    request.session.clear()

    return RedirectResponse(
        url='/login',
        status_code=303
    )