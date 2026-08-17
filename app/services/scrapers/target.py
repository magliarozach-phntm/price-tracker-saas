import json
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
    '[data-test="current-price"]',
    '[data-test="offerPrice"]',
    '[itemprop="price"]',
]


OUT_OF_STOCK_PHRASES = [
    "out of stock",
    "currently unavailable",
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
    title: str,
) -> bool:

    product_name = title.split(
        " : Target"
    )[0].strip()

    start_index = page_text.find(
        product_name
    )

    if start_index == -1:
        return False

    product_section = page_text[
        start_index:start_index + 2000
    ].lower()

    return any(
        phrase in product_section
        for phrase in OUT_OF_STOCK_PHRASES
    )


def _extract_decimal(
    value,
) -> Decimal | None:
    if value is None:
        return None

    try:
        return Decimal(
            str(value)
            .replace("$", "")
            .replace(",", "")
            .strip()
        )

    except (
        InvalidOperation,
        ValueError,
    ):
        return None


def _find_price_from_json_ld(
    soup,
) -> Decimal | None:
    scripts = soup.find_all(
        "script",
        type="application/ld+json",
    )

    for script in scripts:

        if not script.string:
            continue

        try:
            data = json.loads(
                script.string
            )

        except json.JSONDecodeError:
            continue

        objects = (
            data
            if isinstance(data, list)
            else [data]
        )

        for obj in objects:

            if not isinstance(
                obj,
                dict,
            ):
                continue

            offers = obj.get(
                "offers"
            )

            if isinstance(
                offers,
                dict,
            ):
                price = (
                    offers.get("price")
                    or offers.get(
                        "lowPrice"
                    )
                )

                parsed = _extract_decimal(
                    price
                )

                if parsed is not None:
                    logger.info(
                        "Target price found in JSON-LD | "
                        "price=%s",
                        parsed,
                    )

                    return parsed

            elif isinstance(
                offers,
                list,
            ):
                for offer in offers:

                    if not isinstance(
                        offer,
                        dict,
                    ):
                        continue

                    price = (
                        offer.get("price")
                        or offer.get(
                            "lowPrice"
                        )
                    )

                    parsed = (
                        _extract_decimal(
                            price
                        )
                    )

                    if parsed is not None:
                        logger.info(
                            "Target price found in JSON-LD offer | "
                            "price=%s",
                            parsed,
                        )

                        return parsed

    return None


def _find_price_from_scripts(
    soup,
) -> Decimal | None:

    patterns = [
        r'"current_retail"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
        r'"currentRetail"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
        r'"offer_price"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
        r'"price"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
    ]

    for script in soup.find_all(
        "script"
    ):

        script_text = (
            script.string
            or script.get_text()
        )

        if not script_text:
            continue

        for pattern in patterns:

            match = re.search(
                pattern,
                script_text,
            )

            if match:
                parsed = (
                    _extract_decimal(
                        match.group(1)
                    )
                )

                if parsed is not None:
                    logger.info(
                        "Target price found in script data | "
                        "pattern=%s | price=%s",
                        pattern,
                        parsed,
                    )

                    return parsed

    return None


def _find_price_from_selectors(
    soup,
) -> Decimal | None:

    for selector in PRICE_SELECTORS:

        element = soup.select_one(
            selector
        )

        if element is None:
            continue

        content = (
            element.get("content")
            or element.get("value")
        )

        if content:
            parsed = _extract_decimal(
                content
            )

            if parsed is not None:
                return parsed

        text = element.get_text(
            " ",
            strip=True,
        )

        match = re.search(
            r"\$([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?)",
            text,
        )

        if match:
            return _extract_decimal(
                match.group(1)
            )

    return None


def _find_price(
    soup,
    page_text: str,
    title: str,
) -> Decimal | None:

    price = _find_price_from_json_ld(
        soup
    )

    if price is not None:
        return price

    price = _find_price_from_scripts(
        soup
    )

    if price is not None:
        return price

    price = _find_price_from_selectors(
        soup
    )

    if price is not None:
        return price

    return _find_price_from_page_text(
        page_text,
        title,
    )


def scrape_target(
    url: str,
) -> ScrapeResult:

    try:
        response, soup = fetch_page(
            url
        )

        raw_html = response.text

        money_matches = re.findall(
            r'\$[0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?',
            raw_html,
        )

        unique_money = list(
            dict.fromkeys(
                money_matches
            )
        )

        logger.warning(
            "TARGET RAW PRICE DIAGNOSTIC | "
            "money_values=%s",
            unique_money[:30],
        )

        selected_tcin = None

        match = re.search(
            r"[?&]preselect=(\d+)",
            url,
        )

        if match:
            selected_tcin = (
                match.group(1)
            )

        logger.warning(
            "TARGET TCIN DIAGNOSTIC | "
            "selected_tcin=%s | "
            "tcin_present_in_html=%s",
            selected_tcin,
            (
                selected_tcin in raw_html
                if selected_tcin
                else False
            ),
        )

        if (
            selected_tcin
            and selected_tcin in raw_html
        ):
            tcin_index = raw_html.find(
                selected_tcin
            )

            snippet = raw_html[
                max(
                    0,
                    tcin_index - 500,
                ):
                tcin_index + 1500
            ]

            logger.warning(
                "TARGET TCIN SNIPPET | %s",
                snippet,
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
            "json_ld=%s | "
            "scripts=%s",
            response.status_code,
            response.url,
            len(response.content),
            title,
            len(
                soup.find_all(
                    "script",
                    type="application/ld+json",
                )
            ),
            len(
                soup.find_all(
                    "script"
                )
            ),
        )

        if _is_bot_page(
            title,
            page_text,
        ):
            return ScrapeResult(
                success=False,
                retailer="Target",
                price=None,
                in_stock=None,
                status_code=response.status_code,
                page_title=title,
                error=(
                    "Target temporarily blocked "
                    "the price check."
                ),
            )

        price = _find_price(
            soup,
            page_text,
            title,
        )

        out_of_stock = _is_out_of_stock(
            page_text,
            title,
        )

        if price is not None:
            return ScrapeResult(
                success=True,
                retailer="Target",
                price=price,
                in_stock=not out_of_stock,
                status_code=response.status_code,
                page_title=title,
                error=None,
            )

        if out_of_stock:
            return ScrapeResult(
                success=True,
                retailer="Target",
                price=None,
                in_stock=False,
                status_code=response.status_code,
                page_title=title,
                error=None,
            )

        logger.warning(
            "Target price not found | "
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

def _find_price_from_page_text(
    page_text: str,
    title: str,
) -> Decimal | None:

    # Target's HTML contains the selected product's
    # visible price near the product title.
    product_name = title.split(" : Target")[0].strip()

    start_index = page_text.find(
        product_name
    )

    if start_index == -1:
        return None

    # Only inspect the area immediately following
    # the product title so prices from recommended
    # products aren't accidentally selected.
    product_section = page_text[
        start_index:start_index + 1500
    ]

    match = re.search(
        r"\$([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2}))",
        product_section,
    )

    if not match:
        return None

    price = _extract_decimal(
        match.group(1)
    )

    if price is not None:
        logger.info(
            "Target price found in product text | "
            "price=%s",
            price,
        )

    return price