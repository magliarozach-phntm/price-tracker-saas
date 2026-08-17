import re

from app.services.scrapers.base import (
    ScrapeResult,
    clean_price,
    fetch_page,
    get_page_title,
)


PRICE_SELECTORS = [
    '[itemprop="price"]',
    '[data-automation-id="product-price"]',
]

PRICE_PATTERNS = [
    r"Current price is USD\$(\d[\d,]*\.\d{2})",
    r"current price \$?(\d[\d,]*\.\d{2})",
]


def scrape_walmart(url: str) -> ScrapeResult:
    try:
        response, soup = fetch_page(url)

        title = get_page_title(soup)

        if "robot or human" in title.lower():
            return ScrapeResult(
                success=False,
                retailer="Walmart",
                status_code=response.status_code,
                page_title=title,
                error="Walmart blocked the automated request",
            )

        # normal parsing logic here...

    except Exception as exc:
        return ScrapeResult(
            success=False,
            retailer="Walmart",
            error=str(exc),
        )