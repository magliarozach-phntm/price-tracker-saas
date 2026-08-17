from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, HttpUrl, ConfigDict

from app.schemas.price_history import PriceHistoryResponse


class ProductCreate(BaseModel):
    name: str
    url: HttpUrl
    target_price: Decimal

class ProductResponse(BaseModel):
    id: int
    name: str
    url: HttpUrl
    current_price: Decimal | None
    target_price: Decimal
    created_at: datetime
    last_checked: datetime | None

    model_config = ConfigDict(
        from_attributes=True
    )

class ProductDetailResponse(BaseModel):
    id: int
    name: str
    url: HttpUrl
    current_price: Decimal | None
    target_price: Decimal
    created_at: datetime
    last_checked: datetime | None

    price_history: list[PriceHistoryResponse]

    model_config = ConfigDict(
        from_attributes=True
    )

