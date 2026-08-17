from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_session_user
from app.models import TrackedProduct
from app.services.dashboard import get_dashboard_stats
from app.web import templates
from app.web.context import template_context
from fastapi.responses import RedirectResponse


router = APIRouter()



@router.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    current_user = get_session_user(
        request,
        db
    )

    if current_user is None:
        return RedirectResponse(
            url="/login",
            status_code=303
        )

    products = db.execute(
        select(TrackedProduct)
        .where(
            TrackedProduct.user_id == current_user.id
        )
        .order_by(
            TrackedProduct.name.asc()
        )
    ).scalars().all()

    dashboard_stats = get_dashboard_stats(
        current_user,
        db
    )

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context=template_context(
            request=request,
            current_user=current_user,
            products=products,
            dashboard_stats=dashboard_stats,
            active_page="dashboard",
        ),
    )