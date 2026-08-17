from app.services.scrapers.base import (
    ScrapeResult,
    fetch_page,
    get_page_title,
    clean_price,
)


PRICE_SELECTORS = [
    ".a-price .a-offscreen",
    "#corePriceDisplay_desktop_feature_div .a-offscreen",
    "#apex_desktop .a-offscreen",
]


def scrape_ebay(
    url: str,
) -> ScrapeResult:

    try:
        response, soup = fetch_page(url)

        title = get_page_title(soup)

        for selector in PRICE_SELECTORS:
            price_element = soup.select_one(selector)

            if price_element:
                return ScrapeResult(
                    success=True,
                    retailer="Ebay",
                    price=clean_price(
                        price_element.get_text(strip=True)
                    ),
                    status_code=response.status_code,
                    page_title=title,
                )

        return ScrapeResult(
            success=False,
            retailer="Ebay",
            status_code=response.status_code,
            page_title=title,
            error="Price element not found",
        )

    except Exception as e:
        return ScrapeResult(
            success=False,
            retailer="Ebay",
            error=str(e),
        )