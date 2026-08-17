from decimal import Decimal
from app.services.product_stats import get_product_stats
from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
)
from app.services.product_validation import (
    ProductValidationError,
    validate_product_form, normalize_product_url
)

import logging
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.web.context import template_context
from app.core.database import get_db
from app.core.security import get_session_user
from app.models import TrackedProduct
from app.services.tracking.tracker import check_product
from app.web import templates
from app.web.flash import add_flash


router = APIRouter(
    prefix="/products"
)

logger = logging.getLogger(__name__)

@router.get("")
def products_page(
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

    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context=template_context(
            request=request,
            current_user=current_user,
            products=products,
            active_page='products',
        ),
    )


@router.get("/add")
def add_product_page(
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

    return templates.TemplateResponse(
        request=request,
        name="add_product.html",
        context=template_context(
            request=request,
            current_user=current_user,
            active_page='add_product',
        ),
    )


@router.post("/add")
def add_product(
    request: Request,
    name: str = Form(...),
    url: str = Form(...),
    target_price: Decimal = Form(...),
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

    try:
        validated = validate_product_form(
            name=name,
            url=url,
            target_price=target_price,
        )

        normalized_url = normalize_product_url(
            validated["url"]
        )

    except ProductValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="add_product.html",
            context=template_context(
                request=request,
                current_user=current_user,
                active_page="add_product",
                error=str(exc),
                form_data={
                    "name": name,
                    "url": url,
                    "target_price": target_price,
                },
            ),
            status_code=422,
        )

    new_product = TrackedProduct(
        name=validated["name"],
        url=normalized_url,
        target_price=validated["target_price"],
        user_id=current_user.id,
    )

    existing_product = db.execute(
        select(TrackedProduct).where(
            TrackedProduct.user_id == current_user.id,
            TrackedProduct.url == normalized_url,
        )
    ).scalar_one_or_none()

    if existing_product:
        return templates.TemplateResponse(
            request=request,
            name="add_product.html",
            context=template_context(
                request=request,
                current_user=current_user,
                active_page="add_product",
                error="You're already tracking this product.",
                form_data={
                    "name": name,
                    "url": url,
                    "target_price": target_price,
                },
            ),
            status_code=409,
        )

    try:
        db.add(new_product)
        db.commit()
        db.refresh(new_product)

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to create product for user_id=%s",
            current_user.id,
        )

        return templates.TemplateResponse(
            request=request,
            name="add_product.html",
            context=template_context(
                request=request,
                current_user=current_user,
                active_page="add_product",
                error=(
                    "We couldn't save this product right now. "
                    "Please try again."
                ),
                form_data={
                    "name": name,
                    "url": url,
                    "target_price": target_price,
                },
            ),
            status_code=500,
        )

    add_flash(
        request,
        f"{new_product.name} is now being tracked.",
        "success",
    )

    return RedirectResponse(
        url=f"/products/{new_product.id}",
        status_code=303,
    )


@router.get("/{product_id}")
def product_detail(
    request: Request,
    product_id: int,
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

    product = db.execute(
        select(TrackedProduct).where(
            TrackedProduct.id == product_id,
            TrackedProduct.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product_stats = get_product_stats(
        product
    )

    chart_labels = [
        history.checked_at.strftime(
            "%b %d, %Y %I:%M %p"
        )
        for history in product.price_history
    ]

    chart_prices = [
        float(history.price)
        for history in product.price_history
    ]

    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context=template_context(
            request=request,
            current_user=current_user,
            product=product,
            product_stats=product_stats,
            chart_labels=chart_labels,
            chart_prices=chart_prices,
            active_page="products",
        ),
    )


@router.post("/{product_id}/check")
def check_product_now(
    request: Request,
    product_id: int,
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

    try:
        result = check_product(
            product,
            db,
        )

        if result.in_stock is False:
            add_flash(
                request,
                f"{product.name} is currently out of stock. "
                "We'll alert you when it's available again.",
                "warning",
            )

        else:
            add_flash(
                request,
                f"{product.name} was checked successfully.",
                "success",
            )

    except ValueError as exc:
        add_flash(
            request,
            str(exc),
            "danger",
        )

    except Exception:
        logger.exception(
            "Unexpected check failure for product '%s'",
            product.name,
        )

        add_flash(
            request,
            "We couldn't check this product right now. "
            "Please try again later.",
            "danger",
        )

    return RedirectResponse(
        url=f"/products/{product.id}",
        status_code=303,
    )


@router.post("/{product_id}/delete")
def delete_product(
    request: Request,
    product_id: int,
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

    product = db.execute(
        select(TrackedProduct).where(
            TrackedProduct.id == product_id,
            TrackedProduct.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    try:
        product_name = product.name

        db.delete(product)
        db.commit()

        add_flash(
            request,
            f"{product_name} was removed from your tracked products.",
            "success",
        )
    except Exception:
        db.rollback()
        raise

    return RedirectResponse(
        url="/products",
        status_code=303
    )

@router.get("/{product_id}/edit")
def edit_product_page(
    request: Request,
    product_id: int,
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

    product = db.execute(
        select(TrackedProduct).where(
            TrackedProduct.id == product_id,
            TrackedProduct.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return templates.TemplateResponse(
        request=request,
        name="edit_product.html",
        context=template_context(
            request=request,
            current_user=current_user,
            product=product,
            active_page="products",
        ),
    )

@router.post("/{product_id}/edit")
def edit_product(
    request: Request,
    product_id: int,
    name: str = Form(...),
    url: str = Form(...),
    target_price: Decimal = Form(...),
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

    product = db.execute(
        select(TrackedProduct).where(
            TrackedProduct.id == product_id,
            TrackedProduct.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    try:
        validated = validate_product_form(
            name=name,
            url=url,
            target_price=target_price,
        )

        normalized_url = normalize_product_url(
            validated["url"]
        )

    except ProductValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="edit_product.html",
            context=template_context(
                request=request,
                current_user=current_user,
                product=product,
                active_page="products",
                error=str(exc),
                form_data={
                    "name": name,
                    "url": url,
                    "target_price": target_price,
                },
            ),
            status_code=422,
        )

    existing_product = db.execute(
        select(TrackedProduct).where(
            TrackedProduct.user_id == current_user.id,
            TrackedProduct.url == normalized_url,
            TrackedProduct.id != product.id,
        )
    ).scalar_one_or_none()

    if existing_product:
        return templates.TemplateResponse(
            request=request,
            name="edit_product.html",
            context=template_context(
                request=request,
                current_user=current_user,
                product=product,
                active_page="products",
                error="You're already tracking this product.",
                form_data={
                    "name": name,
                    "url": url,
                    "target_price": target_price,
                },
            ),
            status_code=409,
        )

    old_target_price = product.target_price
    old_url = product.url

    product.name = validated["name"]
    product.url = normalized_url
    product.target_price = validated["target_price"]

    # Reset price-alert state only when the target changed.
    if validated["target_price"] != old_target_price:
        product.last_alerted_price = None
        product.last_alerted_at = None

    # If the actual product URL changes, previous stock state
    # should not carry over to the new product page.
    if normalized_url != old_url:
        product.is_in_stock = None
        product.current_price = None
        product.last_checked = None
        product.last_alerted_price = None
        product.last_alerted_at = None
        product.last_stock_alert_at = None

    try:
        db.commit()
        db.refresh(product)

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to update product id=%s for user_id=%s",
            product.id,
            current_user.id,
        )

        return templates.TemplateResponse(
            request=request,
            name="edit_product.html",
            context=template_context(
                request=request,
                current_user=current_user,
                product=product,
                active_page="products",
                error=(
                    "We couldn't update this product right now. "
                    "Please try again."
                ),
                form_data={
                    "name": name,
                    "url": url,
                    "target_price": target_price,
                },
            ),
            status_code=500,
        )

    add_flash(
        request,
        f"{product.name} was updated successfully.",
        "success",
    )

    return RedirectResponse(
        url=f"/products/{product.id}",
        status_code=303
    )