import logging
import re
import time
from urllib.parse import urlsplit
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
    '[data-test="module-product-detail-price-v2"]',
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

            content = locator.get_attribute("content", timeout=1000)
            text = f"${content}" if content else locator.inner_text(timeout=1000)

        except Exception:
            continue

        # A price range or regular/sale pair in a broad container is ambiguous.
        amounts = set(re.findall(r"\$[0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?", text))
        if len(amounts) != 1:
            continue
        price = _parse_price(text)

        if price is not None:
            logger.info(
                "Target rendered price found | "
                "selector=%s | price=%s",
                selector,
                price,
            )

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


BLOCK_STATUSES = {401, 403, 429, 435}


def _record_product_block(response, blocked_responses):
    """Only inspect status/path; never log request query strings or challenge tokens."""
    parsed = urlsplit(response.url)
    if parsed.hostname not in {"www.target.com", "target.com", "redsky.target.com"}:
        return
    is_product_data = (
        parsed.path.startswith("/cdui_orchestrations/v1/pages/pdp/")
        or (parsed.path.startswith("/redsky_aggregations/") and "/pdp_" in parsed.path)
    )
    if is_product_data and response.status in BLOCK_STATUSES and not blocked_responses:
        blocked_responses.append((response.status, parsed.path))


def _failure(message, status, title):
    return ScrapeResult(success=False, retailer="Target", status_code=status,
                        page_title=title, error=message)


def _blocked_failure(blocked_responses, title):
    status, endpoint = blocked_responses[0]
    logger.warning("Target product data blocked | status=%s | endpoint=%s", status, endpoint)
    return _failure(
        f"Target blocked or rate-limited automated product data (HTTP {status}). "
        "No price or stock update was saved. Please try again later.",
        status, title,
    )


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

            try:
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

                blocked_responses = []
                page.on("response", lambda response: _record_product_block(response, blocked_responses))

                response = page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30000,
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

                if response is not None and response.status >= 400:
                    return _failure(f"Target returned HTTP {response.status}.", response.status, title)

                # Network silence does not mean the product modules have loaded.
                deadline = time.monotonic() + 20
                price = None
                while True:
                    if blocked_responses:
                        return _blocked_failure(blocked_responses, title)
                    price = _find_rendered_price(page)
                    if blocked_responses:
                        continue
                    if price is not None or time.monotonic() >= deadline:
                        break
                    page.wait_for_timeout(500)

                in_stock = _get_stock_status(page)
                if blocked_responses:
                    return _blocked_failure(blocked_responses, title)

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
                        in_stock=in_stock,
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
            finally:
                browser.close()

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
