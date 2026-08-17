from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Request,
)
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import logging
from app.core.database import get_db
from app.core.security import (
    get_session_user,
    hash_password,
    verify_password,
)
from app.web import templates
from app.web.context import template_context
from app.web.flash import add_flash


router = APIRouter(
    prefix="/settings"
)

logger = logging.getLogger(__name__)

TIMEZONES = {
    "America/New_York": "Eastern Time (ET)",
    "America/Chicago": "Central Time (CT)",
    "America/Denver": "Mountain Time (MT)",
    "America/Phoenix": "Arizona Time",
    "America/Los_Angeles": "Pacific Time (PT)",
    "America/Anchorage": "Alaska Time",
    "Pacific/Honolulu": "Hawaii Time",
}


@router.get("")
def settings_page(
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = get_session_user(
        request,
        db,
    )

    if current_user is None:
        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context=template_context(
            request=request,
            current_user=current_user,
            timezones=TIMEZONES,
            active_page="settings",
        ),
    )


@router.post("/profile")
def update_profile(
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    current_user = get_session_user(
        request,
        db,
    )

    if current_user is None:
        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    name = name.strip()

    if not name:
        add_flash(
            request,
            "Your name cannot be empty.",
            "danger",
        )

        return RedirectResponse(
            url="/settings",
            status_code=303,
        )

    current_user.name = name

    try:
        db.commit()
        db.refresh(current_user)

    except Exception:
        db.rollback()
        raise

    add_flash(
        request,
        "Your profile was updated successfully.",
        "success",
    )

    return RedirectResponse(
        url="/settings",
        status_code=303,
    )


@router.post("/timezone")
def update_timezone(
    request: Request,
    timezone: str = Form(...),
    db: Session = Depends(get_db),
):
    current_user = get_session_user(
        request,
        db,
    )

    if current_user is None:
        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    if timezone not in TIMEZONES:
        add_flash(
            request,
            "Please select a valid time zone.",
            "danger",
        )

        return RedirectResponse(
            url="/settings",
            status_code=303,
        )

    try:
        ZoneInfo(timezone)

    except ZoneInfoNotFoundError:
        add_flash(
            request,
            "That time zone is not available.",
            "danger",
        )

        return RedirectResponse(
            url="/settings",
            status_code=303,
        )

    current_user.timezone = timezone

    try:
        db.commit()
        db.refresh(current_user)

    except Exception:
        db.rollback()
        raise

    add_flash(
        request,
        "Your time zone preference was updated.",
        "success",
    )

    return RedirectResponse(
        url="/settings",
        status_code=303,
    )

@router.post("/password")
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    current_user = get_session_user(
        request,
        db,
    )

    if current_user is None:
        return RedirectResponse(
            url="/login",
            status_code=303,
        )

    if not verify_password(
        current_password,
        current_user.password_hash,
    ):
        add_flash(
            request,
            "Your current password is incorrect.",
            "danger",
        )

        return RedirectResponse(
            url="/settings",
            status_code=303,
        )

    if len(new_password) < 8:
        add_flash(
            request,
            "Your new password must be at least 8 characters long.",
            "danger",
        )

        return RedirectResponse(
            url="/settings",
            status_code=303,
        )

    if new_password != confirm_password:
        add_flash(
            request,
            "Your new passwords do not match.",
            "danger",
        )

        return RedirectResponse(
            url="/settings",
            status_code=303,
        )

    if verify_password(
        new_password,
        current_user.password_hash,
    ):
        add_flash(
            request,
            "Your new password must be different from your current password.",
            "warning",
        )

        return RedirectResponse(
            url="/settings",
            status_code=303,
        )

    current_user.password_hash = hash_password(
        new_password
    )

    try:
        db.commit()
        db.refresh(current_user)

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to change password for user_id=%s",
            current_user.id,
        )

        add_flash(
            request,
            "We couldn't update your password right now. "
            "Please try again.",
            "danger",
        )

        return RedirectResponse(
            url="/settings",
            status_code=303,
        )

    request.session.clear()

    add_flash(
        request,
        "Your password was changed successfully. "
        "Please sign in again.",
        "success",
    )

    return RedirectResponse(
        url="/login",
        status_code=303,
    )