# app/services/scrapers/base.py

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional
import logging
import time

import requests
from bs4 import BeautifulSoup
from requests import Response


logger = logging.getLogger(__name__)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/150.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
}


@dataclass(slots=True)
class ScrapeResult:
    success: bool
    retailer: str
    price: Decimal | None = None
    in_stock: bool | None = None
    status_code: int | None = None
    page_title: str | None = None
    error: str | None = None


def fetch_page(
    url: str,
    retries: int = 2,
    timeout: int = 15,
) -> tuple[Response, BeautifulSoup]:

    last_error = None

    for attempt in range(retries + 1):

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=timeout,
                allow_redirects=True,
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.content,
                "html.parser",
            )

            if is_block_page(response, soup):
                title = get_page_title(soup)

                logger.warning(
                    "Possible block page | status=%s | title=%r | final_url=%s",
                    response.status_code,
                    title,
                    response.url,
                )

                with open(
                        "walmart_debug.html",
                        "w",
                        encoding="utf-8",
                ) as debug_file:
                    debug_file.write(response.text)

                raise RuntimeError(
                    f"Retailer returned a bot/challenge page: {title}"
                )

            return response, soup

        except requests.RequestException as exc:
            last_error = exc

            logger.warning(
                "Request failed for %s "
                "(attempt %s/%s): %s",
                url,
                attempt + 1,
                retries + 1,
                exc,
            )

            if attempt < retries:
                time.sleep(2 ** attempt)

    raise RuntimeError(
        f"Unable to fetch page: {last_error}"
    )


def get_page_title(
    soup: BeautifulSoup,
) -> str:

    if soup.title:
        return soup.title.get_text(
            strip=True
        )

    return ""


def clean_price(
    price_text: str,
) -> Decimal:

    cleaned = (
        price_text
        .replace("$", "")
        .replace(",", "")
        .replace("USD", "")
        .strip()
    )

    try:
        return Decimal(cleaned)

    except InvalidOperation as exc:
        raise ValueError(
            f"Unable to parse price: {price_text!r}"
        ) from exc


def is_block_page(
    response: Response,
    soup: BeautifulSoup,
) -> bool:

    title = get_page_title(soup).lower()

    visible_text = soup.get_text(
        " ",
        strip=True
    ).lower()

    title_indicators = (
        "robot check",
        "access denied",
        "verify your identity",
        "captcha",
    )

    visible_indicators = (
        "verify you are human",
        "please verify you are a human",
        "unusual traffic",
        "complete the captcha",
        "access denied",
    )

    if any(
        indicator in title
        for indicator in title_indicators
    ):
        return True

    if any(
        indicator in visible_text
        for indicator in visible_indicators
    ):
        return True

    return False