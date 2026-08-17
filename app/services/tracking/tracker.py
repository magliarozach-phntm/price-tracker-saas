from datetime import datetime, UTC
from decimal import Decimal
import logging

from sqlalchemy.orm import Session
from app.core.emailer import (
    send_email,
    send_stock_email,
)
from app.core.emailer import send_email
from app.models import TrackedProduct, PriceHistory
from app.services.scraper import scrape_product
from app.services.tracking.models import ProductCheckResult


logger = logging.getLogger(__name__)


def check_product(
    product: TrackedProduct,
    db: Session,
) -> ProductCheckResult:

    # Save old stock state BEFORE scraping
    previous_stock_status = product.is_in_stock

    # One scrape only
    result = scrape_product(
        product.url
    )

    now = datetime.now(UTC)

    product.is_in_stock = result.in_stock
    product.last_checked = now

    if result.price is not None:
        product.current_price = result.price

    # Only create price history when we actually have a price
    if result.price is not None:
        history = PriceHistory(
            product_id=product.id,
            price=result.price,
            checked_at=now,
        )

        db.add(history)

    try:
        db.commit()
        db.refresh(product)

    except Exception:
        db.rollback()
        raise

    price_alert_sent = False
    stock_alert_sent = False

    # =============================================
    # PRICE ALERT
    # =============================================

    if (
        result.price is not None
        and result.price <= product.target_price
    ):
        should_alert = (
            product.last_alerted_price is None
            or result.price < product.last_alerted_price
        )

        if should_alert:
            try:
                savings = max(
                    Decimal("0.00"),
                    product.target_price - result.price,
                )

                send_email(
                    recipient=product.user.email,
                    product_name=product.name,
                    price=result.price,
                    target_price=product.target_price,
                    savings=savings,
                    url=product.url,
                )

                product.last_alerted_price = result.price
                product.last_alerted_at = now

                db.commit()
                db.refresh(product)

                price_alert_sent = True

            except Exception:
                logger.exception(
                    "Failed to send price alert for '%s'",
                    product.name,
                )

    # =============================================
    # BACK-IN-STOCK ALERT
    # =============================================

    back_in_stock = (
            previous_stock_status is False
            and result.in_stock is True
    )

    if back_in_stock:
        try:
            send_stock_email(
                recipient=product.user.email,
                product_name=product.name,
                price=result.price,
                url=product.url,
            )

            product.last_stock_alert_at = now

            db.commit()
            db.refresh(product)

            stock_alert_sent = True

        except Exception:
            logger.exception(
                "Failed to send stock alert for '%s'",
                product.name,
            )

    return ProductCheckResult(
        product_name=product.name,
        success=True,
        price=result.price,
        target_price=product.target_price,
        in_stock=result.in_stock,
        last_checked=product.last_checked,
        price_alert_sent=price_alert_sent,
        stock_alert_sent=stock_alert_sent,
    )