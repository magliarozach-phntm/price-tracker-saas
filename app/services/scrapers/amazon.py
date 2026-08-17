import logging
from decimal import Decimal, InvalidOperation

from app.services.scrapers.base import (
    ScrapeResult,
    clean_price,
    fetch_page,
    get_page_title,
)


logger = logging.getLogger(__name__)


PRICE_SELECTORS = [
    "#corePrice_feature_div .a-offscreen",
    "#corePriceDisplay_desktop_feature_div .a-offscreen",
    "#corePriceDisplay_mobile_feature_div .a-offscreen",
    "#apex_desktop .a-offscreen",
    "#apex_mobile .a-offscreen",
    ".priceToPay .a-offscreen",
    ".reinventPricePriceToPayMargin .a-offscreen",
    ".a-price .a-offscreen",
]


OUT_OF_STOCK_PHRASES = [
    "currently unavailable",
    "temporarily out of stock",
    "we don't know when or if this item will be back in stock",
    "no featured offers available",
]


BOT_PAGE_PHRASES = [
    "robot check",
    "sorry! something went wrong!",
    "enter the characters you see below",
    "type the characters you see in this image",
]


def _is_bot_page(
    title: str,
    page_text: str,
) -> bool:
    combined = (
        f"{title} {page_text}"
        .lower()
    )

    return any(
        phrase in combined
        for phrase in BOT_PAGE_PHRASES
    )


def _get_availability_text(
    soup,
) -> str:
    selectors = [
        "#availability",
        "#outOfStock",
        "#availabilityInsideBuyBox_feature_div",
    ]

    availability_parts = []

    for selector in selectors:
        element = soup.select_one(
            selector
        )

        if element:
            text = element.get_text(
                " ",
                strip=True,
            )

            if text:
                availability_parts.append(
                    text
                )

    return " ".join(
        availability_parts
    ).lower()


def _is_out_of_stock(
    soup,
) -> bool:
    availability_text = (
        _get_availability_text(
            soup
        )
    )

    if any(
        phrase in availability_text
        for phrase in OUT_OF_STOCK_PHRASES
    ):
        return True

    add_to_cart = soup.select_one(
        "#add-to-cart-button"
    )

    buy_now = soup.select_one(
        "#buy-now-button"
    )

    # If Amazon explicitly says unavailable AND
    # there are no purchase controls, treat it
    # as out of stock.
    if (
        "unavailable"
        in availability_text
        and add_to_cart is None
        and buy_now is None
    ):
        return True

    return False


def _find_price(
    soup,
) -> Decimal | None:
    for selector in PRICE_SELECTORS:
        price_element = soup.select_one(
            selector
        )

        if price_element is None:
            continue

        price_text = price_element.get_text(
            strip=True
        )

        if not price_text:
            continue

        try:
            return clean_price(
                price_text
            )

        except (
            InvalidOperation,
            ValueError,
        ):
            logger.debug(
                "Amazon price parse failed | "
                "selector=%s | text=%s",
                selector,
                price_text,
            )

    return None


def scrape_amazon(
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

        # -------------------------------------------------
        # BOT / CHALLENGE DETECTION
        # -------------------------------------------------

        if _is_bot_page(
            title,
            page_text,
        ):
            logger.warning(
                "Amazon bot/challenge page | "
                "status=%s | title=%s | url=%s",
                response.status_code,
                title,
                url,
            )

            return ScrapeResult(
                success=False,
                retailer="Amazon",
                price=None,
                in_stock=None,
                status_code=response.status_code,
                page_title=title,
                error=(
                    "Amazon temporarily blocked the "
                    "price check. Please try again later."
                ),
            )

        # -------------------------------------------------
        # STOCK DETECTION
        # -------------------------------------------------

        if _is_out_of_stock(
            soup
        ):
            logger.info(
                "Amazon product out of stock | "
                "status=%s | title=%s | url=%s",
                response.status_code,
                title,
                url,
            )

            return ScrapeResult(
                success=True,
                retailer="Amazon",
                price=None,
                in_stock=False,
                status_code=response.status_code,
                page_title=title,
                error=None,
            )

        # -------------------------------------------------
        # PRICE DETECTION
        # -------------------------------------------------

        price = _find_price(
            soup
        )

        if price is None:
            availability = (
                _get_availability_text(
                    soup
                )
            )

            logger.warning(
                "Amazon price not found | "
                "status=%s | title=%s | "
                "availability=%s | url=%s",
                response.status_code,
                title,
                availability[:250],
                url,
            )

            return ScrapeResult(
                success=False,
                retailer="Amazon",
                price=None,
                in_stock=None,
                status_code=response.status_code,
                page_title=title,
                error=(
                    "Amazon returned the product page, "
                    "but the current price could not "
                    "be determined."
                ),
            )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        logger.info(
            "Amazon scrape successful | "
            "status=%s | price=%s | "
            "title=%s",
            response.status_code,
            price,
            title,
        )

        return ScrapeResult(
            success=True,
            retailer="Amazon",
            price=price,
            in_stock=True,
            status_code=response.status_code,
            page_title=title,
            error=None,
        )

    except Exception as exc:
        logger.exception(
            "Amazon scraper exception | "
            "url=%s",
            url,
        )

        return ScrapeResult(
            success=False,
            retailer="Amazon",
            price=None,
            in_stock=None,
            error=(
                "Amazon price check failed: "
                f"{type(exc).__name__}"
            ),
        )