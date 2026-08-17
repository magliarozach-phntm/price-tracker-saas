from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import TrackedProduct, User
from app.services.tracking.tracker import check_product


router = APIRouter(
    prefix="/tracker",
    tags=["Tracker"],
)


@router.post("/products/{product_id}/check")
def check_one_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.execute(
        select(TrackedProduct).where(
            TrackedProduct.id == product_id,
            TrackedProduct.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return check_product(
        product,
        db,
    )


@router.post("/check")
def check_all_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    products = db.execute(
        select(TrackedProduct).where(
            TrackedProduct.user_id == current_user.id
        )
    ).scalars().all()

    results = []

    for product in products:
        result = check_product(
            product,
            db,
        )

        results.append(result)

    return results