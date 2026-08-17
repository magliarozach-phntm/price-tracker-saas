import logging
from urllib.parse import urlparse

from app.services.scrapers.target import (
    scrape_target,
)


logger = logging.getLogger(__name__)


SCRAPERS = {
    "target.": scrape_target,
}


def scrape_product(
    url: str,
):

    domain = urlparse(
        url
    ).netloc.lower()

    logger.warning(
        "SCRAPER DISPATCH | "
        "domain=%s | url=%s",
        domain,
        url,
    )


    # -------------------------------------------------
    # AMAZON
    # -------------------------------------------------

    if "amazon." in domain:

        raise ValueError(
            "Amazon live price tracking is "
            "coming soon. You can save Amazon "
            "products now, but automatic price "
            "checks are not yet available."
        )


    # -------------------------------------------------
    # ACTIVE RETAILERS
    # -------------------------------------------------

    for (
        retailer_domain,
        scraper_func,
    ) in SCRAPERS.items():

        if retailer_domain in domain:

            logger.warning(
                "SCRAPER MATCH | "
                "domain=%s | scraper=%s",
                domain,
                scraper_func.__name__,
            )

            result = scraper_func(
                url
            )

            if result is None:

                raise ValueError(
                    f"Retailer '{domain}' "
                    "returned no scrape result."
                )


            logger.warning(
                "SCRAPE RESULT | "
                "retailer=%s | "
                "success=%s | "
                "price=%s | "
                "in_stock=%s | "
                "status=%s | "
                "title=%r | "
                "error=%r",
                result.retailer,
                result.success,
                result.price,
                result.in_stock,
                result.status_code,
                result.page_title,
                result.error,
            )


            if not result.success:

                raise ValueError(
                    result.error
                    or (
                        f"{result.retailer} "
                        "price check failed."
                    )
                )


            return result


    raise ValueError(
        f"Unsupported retailer: {domain}"
    )