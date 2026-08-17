import logging
import re
from decimal import Decimal, InvalidOperation

from app.services.scrapers.base import (
    ScrapeResult,
    fetch_page,
    get_page_title,
    clean_price,
)


logger = logging.getLogger(__name__)


PRICE_SELECTORS = [
    '[data-test="product-price"]',
    '[data-test="product-price"] span',
    '[data-test="current-price"]',
    '[data-test="current-price"] span',
    '[data-test="offerPrice"]',
    '[itemprop="price"]',
]


OUT_OF_STOCK_PHRASES = [
    "out of stock",
    "currently unavailable",
    "not available",
    "sold out",
]


BOT_PAGE_PHRASES = [
    "access denied",
    "verify you are human",
    "verify your identity",
    "captcha",
    "unusual traffic",
]


def _is_bot_page(
    title: str,
    page_text: str,
) -> bool:
    combined = f"{title} {page_text}".lower()

    return any(
        phrase in combined
        for phrase in BOT_PAGE_PHRASES
    )


def _is_out_of_stock(
    page_text: str,
) -> bool:
    text = page_text.lower()

    return any(
        phrase in text
        for phrase in OUT_OF_STOCK_PHRASES
    )


def _extract_price_from_text(
    text: str,
) -> Decimal | None:
    matches = re.findall(
        r"\$([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?)",
        text,
    )

    if not matches:
        return None

    for match in matches:
        try:
            return clean_price(
                f"${match}"
            )

        except (
            InvalidOperation,
            ValueError,
        ):
            continue

    return None


def _find_price(
    soup,
    page_text: str,
) -> Decimal | None:

    # ---------------------------------------------
    # STRUCTURED / SELECTOR-BASED PRICE
    # ---------------------------------------------

    for selector in PRICE_SELECTORS:
        element = soup.select_one(
            selector
        )

        if element is None:
            continue

        # Some structured elements store
        # the price in an attribute.
        content = (
            element.get("content")
            or element.get("value")
        )

        if content:
            try:
                return clean_price(
                    str(content)
                )

            except (
                InvalidOperation,
                ValueError,
            ):
                pass

        text = element.get_text(
            " ",
            strip=True,
        )

        if not text:
            continue

        price = _extract_price_from_text(
            text
        )

        if price is not None:
            logger.info(
                "Target price found | "
                "selector=%s | price=%s",
                selector,
                price,
            )

            return price

    # ---------------------------------------------
    # FALLBACK: PAGE TEXT
    # ---------------------------------------------

    price = _extract_price_from_text(
        page_text
    )

    if price is not None:
        logger.info(
            "Target price found using text fallback | "
            "price=%s",
            price,
        )

        return price

    return None


def scrape_target(
    url: str,
) -> ScrapeResult:

    try:
        response, soup = fetch_page(
            url
        )

        title = get_page_title(
            soup
        )

        page_text = soup.get_text(
            " ",
            strip=True,
        )

        logger.warning(
            "TARGET RESPONSE DIAGNOSTIC | "
            "status=%s | "
            "final_url=%s | "
            "content_length=%s | "
            "title=%r | "
            "has_product_price=%s | "
            "has_itemprop_price=%s",
            response.status_code,
            response.url,
            len(response.content),
            title,
            soup.select_one(
                '[data-test="product-price"]'
            ) is not None,
            soup.select_one(
                '[itemprop="price"]'
            ) is not None,
        )

        # ---------------------------------------------
        # BOT / CHALLENGE DETECTION
        # ---------------------------------------------

        if _is_bot_page(
            title,
            page_text,
        ):
            logger.warning(
                "Target bot/challenge page | "
                "status=%s | title=%s | url=%s",
                response.status_code,
                title,
                url,
            )

            return ScrapeResult(
                success=False,
                retailer="Target",
                price=None,
                in_stock=None,
                status_code=response.status_code,
                page_title=title,
                error=(
                    "Target temporarily blocked the "
                    "price check. Please try again later."
                ),
            )

        # ---------------------------------------------
        # PRICE
        # ---------------------------------------------

        price = _find_price(
            soup,
            page_text,
        )

        # ---------------------------------------------
        # STOCK
        # ---------------------------------------------

        out_of_stock = _is_out_of_stock(
            page_text
        )

        if (
            price is not None
            and not out_of_stock
        ):
            logger.info(
                "Target scrape successful | "
                "status=%s | price=%s | "
                "title=%s",
                response.status_code,
                price,
                title,
            )

            return ScrapeResult(
                success=True,
                retailer="Target",
                price=price,
                in_stock=True,
                status_code=response.status_code,
                page_title=title,
                error=None,
            )

        # ---------------------------------------------
        # EXPLICITLY OUT OF STOCK
        # ---------------------------------------------

        if out_of_stock:
            logger.info(
                "Target product out of stock | "
                "status=%s | "
                "price=%s | "
                "title=%s",
                response.status_code,
                price,
                title,
            )

            return ScrapeResult(
                success=True,
                retailer="Target",
                price=price,
                in_stock=False,
                status_code=response.status_code,
                page_title=title,
                error=None,
            )

        # ---------------------------------------------
        # UNKNOWN
        # ---------------------------------------------

        logger.warning(
            "Target price not found | "
            "status=%s | "
            "title=%s | "
            "url=%s",
            response.status_code,
            title,
            url,
        )

        return ScrapeResult(
            success=False,
            retailer="Target",
            price=None,
            in_stock=None,
            status_code=response.status_code,
            page_title=title,
            error=(
                "Target returned the product page, "
                "but the current price could not "
                "be determined."
            ),
        )

    except Exception as exc:
        logger.exception(
            "Target scraper exception | "
            "url=%s",
            url,
        )

        return ScrapeResult(
            success=False,
            retailer="Target",
            price=None,
            in_stock=None,
            error=(
                "Target price check failed: "
                f"{type(exc).__name__}"
            ),
        )