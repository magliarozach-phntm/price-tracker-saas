from decimal import Decimal

from app.models import TrackedProduct


def get_product_stats(
    product: TrackedProduct,
) -> dict:
    prices = [
        history.price
        for history in product.price_history
    ]

    if not prices:
        return {
            "lowest_price": None,
            "highest_price": None,
            "average_price": None,
            "check_count": 0,
        }

    total = sum(
        prices,
        Decimal("0.00")
    )

    return {
        "lowest_price": min(prices),
        "highest_price": max(prices),
        "average_price": (
            total / Decimal(len(prices))
        ),
        "check_count": len(prices),
    }