# app/services/models.py

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime


@dataclass(slots=True)
class ProductCheckResult:
    product_name: str
    success: bool
    price: Decimal | None = None
    target_price: Decimal | None = None
    in_stock: bool | None = None
    last_checked: datetime | None = None
    price_alert_sent: bool = False
    stock_alert_sent: bool = False
    error: str | None = None