from decimal import Decimal
from urllib.parse import urlparse, urlunparse



SUPPORTED_RETAILERS = {
    "amazon.": "Amazon",
}


class ProductValidationError(ValueError):
    pass


def validate_product_form(
    name: str,
    url: str,
    target_price: Decimal,
):
    clean_name = name.strip()
    clean_url = url.strip()

    if not clean_name:
        raise ProductValidationError(
            "Product name cannot be empty."
        )

    if len(clean_name) > 255:
        raise ProductValidationError(
            "Product name must be 255 characters or fewer."
        )

    if target_price <= 0:
        raise ProductValidationError(
            "Target price must be greater than $0."
        )

    if len(clean_url) > 1000:
        raise ProductValidationError(
            "Product URL is too long."
        )

    parsed = urlparse(clean_url)

    if parsed.scheme not in {"http", "https"}:
        raise ProductValidationError(
            "Please enter a valid product URL."
        )

    if not parsed.netloc:
        raise ProductValidationError(
            "Please enter a valid product URL."
        )

    domain = parsed.netloc.lower()

    retailer = None

    for retailer_domain, retailer_name in SUPPORTED_RETAILERS.items():
        if retailer_domain in domain:
            retailer = retailer_name
            break

    if retailer is None:
        raise ProductValidationError(
            "This retailer is not supported yet. "
            "MAG PriceWatch currently supports Amazon."
        )

    return {
        "name": clean_name,
        "url": clean_url,
        "target_price": target_price,
        "retailer": retailer,
    }


def normalize_product_url(url: str) -> str:
    parsed = urlparse(url.strip())

    clean = parsed._replace(
        fragment="",
    )

    return urlunparse(clean)