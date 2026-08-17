from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import TrackedProduct, User
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductDetailResponse,
)


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
)
def add_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_product = TrackedProduct(
        name=product.name,
        url=str(product.url),
        target_price=product.target_price,
        user_id=current_user.id,
    )

    try:
        db.add(new_product)
        db.commit()
        db.refresh(new_product)

    except Exception:
        db.rollback()
        raise

    return new_product


@router.get(
    "",
    response_model=list[ProductResponse],
)
def list_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    products = db.execute(
        select(TrackedProduct)
        .where(
            TrackedProduct.user_id
            == current_user.id
        )
        .order_by(
            TrackedProduct.name.asc()
        )
    ).scalars().all()

    return products


@router.get(
    "/{product_id}",
    response_model=ProductDetailResponse,
)
def product_detail(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.execute(
        select(TrackedProduct).where(
            TrackedProduct.id == product_id,
            TrackedProduct.user_id
            == current_user.id,
        )
    ).scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.execute(
        select(TrackedProduct).where(
            TrackedProduct.id == product_id,
            TrackedProduct.user_id
            == current_user.id,
        )
    ).scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    product_name = product.name

    try:
        db.delete(product)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": f"{product_name} removed"
    }