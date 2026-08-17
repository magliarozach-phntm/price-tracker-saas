from decimal import Decimal
from urllib.parse import urlparse


class ProductValidationError(ValueError):
    pass


SUPPORTED_RETAILERS = {
    "amazon.com": {
        "name": "Amazon",
        "tracking_supported": False,
    },
    "target.com": {
        "name": "Target",
        "tracking_supported": True,
    },
}


def normalize_product_url(
    url: str,
) -> str:
    url = url.strip()

    if not url:
        raise ProductValidationError(
            "Product URL is required."
        )

    parsed = urlparse(url)

    if parsed.scheme not in (
        "http",
        "https",
    ):
        raise ProductValidationError(
            "Please enter a valid product URL."
        )

    normalized = parsed._replace(
        fragment=""
    )

    return normalized.geturl()


def get_retailer(
    url: str,
) -> str:
    parsed = urlparse(url)

    domain = parsed.netloc.lower()

    if domain.startswith("www."):
        domain = domain[4:]

    for (
        retailer_domain,
        retailer_info,
    ) in SUPPORTED_RETAILERS.items():

        if (
            domain == retailer_domain
            or domain.endswith(
                f".{retailer_domain}"
            )
        ):
            return retailer_info["name"]

    raise ProductValidationError(
        "Currently supported retailers are "
        "Target and Amazon."
    )


def validate_product_form(
    name: str,
    url: str,
    target_price: Decimal,
) -> dict:
    clean_name = name.strip()

    if not clean_name:
        raise ProductValidationError(
            "Product name cannot be empty."
        )

    if target_price <= Decimal("0"):
        raise ProductValidationError(
            "Target price must be greater than zero."
        )

    normalized_url = normalize_product_url(
        url
    )

    retailer = get_retailer(
        normalized_url
    )

    return {
        "name": clean_name,
        "url": normalized_url,
        "target_price": target_price,
        "retailer": retailer,
    }