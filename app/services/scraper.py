from urllib.parse import urlparse

from app.services.scrapers.amazon import scrape_amazon


SCRAPERS = {
    "amazon.": scrape_amazon
}


def scrape_product(url: str):
    domain = urlparse(url).netloc.lower()

    for retailer_domain, scraper_func in SCRAPERS.items():

        if retailer_domain in domain:

            result = scraper_func(url)

            if result is None:
                raise ValueError(
                    f"Retailer '{domain}' is not supported yet."
                )

            if not result.success:
                raise ValueError(
                    result.error
                    or f"{result.retailer} scrape failed"
                )

            return result

    raise ValueError(
        f"Unsupported retailer: {domain}"
    )