import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import TrackedProduct
from app.services.tracking.tracker import check_product


logger = logging.getLogger(__name__)


def check_all_products():
    """
    Run one automatic tracking cycle.

    Each product is checked independently so one failed
    retailer/product does not stop the rest of the cycle.
    """

    db = SessionLocal()

    try:
        products = db.execute(
            select(TrackedProduct)
            .order_by(TrackedProduct.id.asc())
        ).scalars().all()

        logger.info(
            "Starting automatic product check for %s products",
            len(products),
        )

        for product in products:
            try:
                logger.info(
                    "Automatically checking product id=%s name=%s",
                    product.id,
                    product.name,
                )

                result = check_product(
                    product,
                    db,
                )

                logger.info(
                    "Automatic check completed "
                    "product_id=%s price=%s in_stock=%s "
                    "price_alert_sent=%s stock_alert_sent=%s",
                    product.id,
                    result.price,
                    result.in_stock,
                    result.price_alert_sent,
                    result.stock_alert_sent,
                )

            except Exception:
                # Important because check_product() may have left
                # the session in a failed transaction state.
                db.rollback()

                logger.exception(
                    "Automatic check failed for "
                    "product_id=%s name=%s",
                    product.id,
                    product.name,
                )



    except ValueError as exc:

        db.rollback()

        logger.warning(

            "Automatic check skipped | "

            "product_id=%s | name=%s | reason=%s",

            product.id,

            product.name,

            exc,

        )


    except Exception:

        db.rollback()

        logger.exception(

            "Automatic check failed | "

            "product_id=%s | name=%s | url=%s",

            product.id,

            product.name,

            product.url,

        )

    finally:
        db.close()


scheduler = BackgroundScheduler(
    timezone="UTC",
)


def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(
        check_all_products,
        trigger="interval",
        minutes=30,
        id="automatic_product_check",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()

    logger.info(
        "MAG PriceWatch scheduler started"
    )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(
            wait=False
        )

        logger.info(
            "MAG PriceWatch scheduler stopped"
        )