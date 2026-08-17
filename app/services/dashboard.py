# app/services/dashboard.py

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TrackedProduct, User


def get_dashboard_stats(
    user: User,
    db: Session,
) -> dict:
    products = db.execute(
        select(TrackedProduct).where(
            TrackedProduct.user_id == user.id
        )
    ).scalars().all()

    active_alerts = sum(
        1
        for product in products
        if (
            product.current_price is not None
            and product.current_price <= product.target_price
        )
    )

    today = datetime.now(timezone.utc).date()

    checked_today = sum(
        1
        for product in products
        if (
            product.last_checked is not None
            and product.last_checked.date() == today
        )
    )

    last_check = max(
        (
            product.last_checked
            for product in products
            if product.last_checked is not None
        ),
        default=None,
    )

    return {
        "product_count": len(products),
        "active_alerts": active_alerts,
        "checked_today": checked_today,
        "last_check": last_check,
    }