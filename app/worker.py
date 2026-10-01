"""Run one Target monitoring cycle: python -m app.worker."""

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

from sqlalchemy import select

from app.core.database import SessionLocal, engine
from app.models import TrackedProduct
from app.services.tracking.tracker import check_product

logger = logging.getLogger(__name__)


@dataclass
class CycleResult:
    checked: int = 0
    skipped: int = 0
    failed: int = 0


def is_target_url(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
    except ValueError:
        return False
    return host == "target.com" or host.endswith(".target.com")


def check_all_products() -> CycleResult:
    result = CycleResult()
    # Release the inventory connection before launching any browsers.
    with SessionLocal() as db:
        product_ids = list(db.scalars(select(TrackedProduct.id).order_by(TrackedProduct.id)))

    logger.info("Starting automatic check for %s saved products", len(product_ids))
    for product_id in product_ids:
        # A fresh session prevents one failed transaction affecting later products.
        try:
            with SessionLocal() as db:
                product = db.get(TrackedProduct, product_id)
                if product is None or not is_target_url(product.url):
                    result.skipped += 1
                    continue
                check = check_product(product, db)
                result.checked += 1
                logger.info(
                    "Check completed product_id=%s price=%s in_stock=%s "
                    "price_alert_sent=%s stock_alert_sent=%s",
                    product_id, check.price, check.in_stock,
                    check.price_alert_sent, check.stock_alert_sent,
                )
        except Exception:
            # The session context rolls back and closes even when scraping fails.
            result.failed += 1
            logger.exception("Automatic check failed product_id=%s", product_id)

    logger.info("Cycle finished checked=%s skipped=%s failed=%s",
                result.checked, result.skipped, result.failed)
    return result


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        result = check_all_products()
        return 1 if result.failed else 0
    except Exception:
        logger.exception("Automatic monitoring cycle failed")
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
