from app.services.scrapers.base import (
    ScrapeResult,
    fetch_page,
    get_page_title,
    clean_price,
)


PRICE_SELECTORS = [
    "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
    "#corePrice_feature_div .a-price .a-offscreen",
    "#apex_desktop .a-price .a-offscreen",
    "#price_inside_buybox",
]

AVAILABILITY_SELECTORS = [
    "#availability",
    "#outOfStock",
    "#availabilityInsideBuyBox_feature_div",
]

BUY_BUTTON_SELECTORS = [
    "#add-to-cart-button",
    "#buy-now-button",
    "#submit.add-to-cart",
]


def scrape_amazon(
    url: str,
) -> ScrapeResult:

    try:
        response, soup = fetch_page(url)

        title = get_page_title(soup)


        # ==========================================
        # BOT / CHALLENGE DETECTION
        # ==========================================

        page_text = soup.get_text(
            " ",
            strip=True,
        ).lower()

        bot_phrases = (
            "enter the characters you see below",
            "sorry, we just need to make sure",
            "type the characters you see",
        )

        if any(
            phrase in page_text
            for phrase in bot_phrases
        ):
            return ScrapeResult(
                success=False,
                retailer="Amazon",
                status_code=response.status_code,
                page_title=title,
                error="Amazon returned a bot/challenge page",
            )

        # ==========================================
        # AVAILABILITY TEXT
        # ==========================================

        availability_text = ""

        for selector in AVAILABILITY_SELECTORS:

            element = soup.select_one(selector)

            if element:

                text = element.get_text(
                    " ",
                    strip=True,
                )

                if text:
                    availability_text = text.lower()
                    break

        # ==========================================
        # BUY BUTTON
        # ==========================================

        has_buy_button = any(
            soup.select_one(selector) is not None
            for selector in BUY_BUTTON_SELECTORS
        )

        # ==========================================
        # DETERMINE STOCK
        # ==========================================

        in_stock = None

        out_of_stock_phrases = (
            "currently unavailable",
            "temporarily out of stock",
            "out of stock",
            "we don't know when or if this item will be back in stock",
            "no featured offers available",
        )

        in_stock_phrases = (
            "in stock",
            "available to ship",
        )

        if any(
            phrase in availability_text
            for phrase in out_of_stock_phrases
        ):
            in_stock = False

        elif any(
            phrase in availability_text
            for phrase in in_stock_phrases
        ):
            in_stock = True

        elif has_buy_button:
            in_stock = True

        # ==========================================
        # PRICE
        # ==========================================

        price = None

        for selector in PRICE_SELECTORS:

            price_element = soup.select_one(
                selector
            )

            if price_element:

                raw_price = price_element.get_text(
                    strip=True
                )

                try:

                    price = clean_price(
                        raw_price
                    )

                    break

                except Exception:
                    continue

        # ==========================================
        # OUT OF STOCK
        # ==========================================

        if in_stock is False:

            return ScrapeResult(
                success=True,
                retailer="Amazon",
                price=None,
                in_stock=False,
                status_code=response.status_code,
                page_title=title,
            )

        # ==========================================
        # IN STOCK
        # ==========================================

        if in_stock is True and price is not None:

            return ScrapeResult(
                success=True,
                retailer="Amazon",
                price=price,
                in_stock=True,
                status_code=response.status_code,
                page_title=title,
            )

        # ==========================================
        # UNKNOWN AVAILABILITY + PRICE
        # ==========================================

        if price is not None:

            return ScrapeResult(
                success=True,
                retailer="Amazon",
                price=price,
                in_stock=None,
                status_code=response.status_code,
                page_title=title,
            )

        # ==========================================
        # NOTHING RELIABLE
        # ==========================================

        return ScrapeResult(
            success=False,
            retailer="Amazon",
            price=None,
            in_stock=in_stock,
            status_code=response.status_code,
            page_title=title,
            error=(
                "Amazon price and availability "
                "could not be determined"
            ),
        )

    except Exception as exc:

        return ScrapeResult(
            success=False,
            retailer="Amazon",
            error=str(exc),
        )