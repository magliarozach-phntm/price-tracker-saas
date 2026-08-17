import logging
import re
from decimal import Decimal, InvalidOperation

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from app.services.scrapers.base import (
    ScrapeResult,
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
    "sold out",
]


def _parse_price(
    text: str,
) -> Decimal | None:
    if not text:
        return None

    match = re.search(
        r"\$([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?)",
        text,
    )

    if not match:
        return None

    try:
        return Decimal(
            match.group(1).replace(",", "")
        )

    except (
        InvalidOperation,
        ValueError,
    ):
        return None


def _find_rendered_price(
    page,
) -> Decimal | None:

    for selector in PRICE_SELECTORS:

        locator = page.locator(
            selector
        ).first

        try:
            if locator.count() == 0:
                continue

            text = locator.inner_text(
                timeout=2000
            )

        except Exception:
            continue

        price = _parse_price(
            text
        )

        if price is not None:
            logger.info(
                "Target rendered price found | "
                "selector=%s | price=%s",
                selector,
                price,
            )

            return price

    # Fallback to rendered page text,
    # not the original requests HTML.
    body_text = page.locator(
        "body"
    ).inner_text(
        timeout=5000
    )

    price_matches = re.findall(
        r"\$([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2}))",
        body_text,
    )

    logger.warning(
        "TARGET RENDERED PRICE VALUES | values=%s",
        price_matches[:20],
    )

    if not price_matches:
        return None

    # Temporary fallback.
    # Once we see Target's actual rendered DOM
    # on Railway, we can tighten this further.
    for value in price_matches:

        price = _parse_price(
            f"${value}"
        )

        if price is not None:
            return price

    return None


def _get_stock_status(
    page,
) -> bool | None:

    try:
        body_text = page.locator(
            "body"
        ).inner_text(
            timeout=5000
        ).lower()

    except Exception:
        return None

    for phrase in OUT_OF_STOCK_PHRASES:

        if phrase in body_text:
            return False

    if (
        "add to cart" in body_text
        or "pick it up" in body_text
        or "ship it" in body_text
    ):
        return True

    return None


def scrape_target(
    url: str,
) -> ScrapeResult:

    browser = None

    try:

        with sync_playwright() as playwright:

            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/150.0.0.0 Safari/537.36"
                ),
                locale="en-US",
                viewport={
                    "width": 1440,
                    "height": 1000,
                },
            )

            page = context.new_page()

            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # Give Target's client-side product
            # data time to populate.
            try:
                page.wait_for_load_state(
                    "networkidle",
                    timeout=10000,
                )
            except PlaywrightTimeoutError:
                logger.info(
                    "Target networkidle timed out; "
                    "continuing with rendered page."
                )

            title = page.title()

            logger.warning(
                "TARGET PLAYWRIGHT DIAGNOSTIC | "
                "status=%s | "
                "title=%r | "
                "final_url=%s",
                (
                    response.status
                    if response
                    else None
                ),
                title,
                page.url,
            )

            price = _find_rendered_price(
                page
            )

            in_stock = _get_stock_status(
                page
            )

            if price is not None:

                logger.info(
                    "Target Playwright scrape successful | "
                    "price=%s | in_stock=%s | "
                    "title=%s",
                    price,
                    in_stock,
                    title,
                )

                return ScrapeResult(
                    success=True,
                    retailer="Target",
                    price=price,
                    in_stock=(
                        True
                        if in_stock is None
                        else in_stock
                    ),
                    status_code=(
                        response.status
                        if response
                        else None
                    ),
                    page_title=title,
                    error=None,
                )

            if in_stock is False:

                return ScrapeResult(
                    success=True,
                    retailer="Target",
                    price=None,
                    in_stock=False,
                    status_code=(
                        response.status
                        if response
                        else None
                    ),
                    page_title=title,
                    error=None,
                )

            return ScrapeResult(
                success=False,
                retailer="Target",
                price=None,
                in_stock=None,
                status_code=(
                    response.status
                    if response
                    else None
                ),
                page_title=title,
                error=(
                    "Target loaded the product page, "
                    "but the current price could not "
                    "be determined."
                ),
            )

    except PlaywrightTimeoutError:

        logger.exception(
            "Target browser timed out | url=%s",
            url,
        )

        return ScrapeResult(
            success=False,
            retailer="Target",
            price=None,
            in_stock=None,
            error=(
                "Target took too long to load. "
                "Please try again shortly."
            ),
        )

    except Exception as exc:

        logger.exception(
            "Target browser scrape failed | "
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

    finally:

        if browser is not None:

            try:
                browser.close()
            except Exception:
                pass