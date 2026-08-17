from decimal import Decimal

import pytest

from app.services.product_validation import (
    ProductValidationError,
    normalize_product_url,
    validate_product_form,
)


def test_valid_amazon_product():
    result = validate_product_form(
        name="Sony Headphones",
        url="https://www.amazon.com/example-product",
        target_price=Decimal("299.99"),
    )

    assert result["name"] == "Sony Headphones"
    assert result["url"] == "https://www.amazon.com/example-product"
    assert result["target_price"] == Decimal("299.99")
    assert result["retailer"] == "Amazon"


def test_product_name_is_trimmed():
    result = validate_product_form(
        name="   Sony Headphones   ",
        url="https://www.amazon.com/example-product",
        target_price=Decimal("299.99"),
    )

    assert result["name"] == "Sony Headphones"


def test_empty_product_name_rejected():
    with pytest.raises(
        ProductValidationError,
        match="Product name cannot be empty",
    ):
        validate_product_form(
            name="   ",
            url="https://www.amazon.com/example-product",
            target_price=Decimal("299.99"),
        )


def test_zero_target_price_rejected():
    with pytest.raises(
        ProductValidationError,
        match="Target price must be greater than",
    ):
        validate_product_form(
            name="Sony Headphones",
            url="https://www.amazon.com/example-product",
            target_price=Decimal("0.00"),
        )


def test_negative_target_price_rejected():
    with pytest.raises(ProductValidationError):
        validate_product_form(
            name="Sony Headphones",
            url="https://www.amazon.com/example-product",
            target_price=Decimal("-10.00"),
        )


def test_invalid_url_rejected():
    with pytest.raises(ProductValidationError):
        validate_product_form(
            name="Sony Headphones",
            url="not-a-url",
            target_price=Decimal("299.99"),
        )


def test_unsupported_retailer_rejected():
    with pytest.raises(
        ProductValidationError,
        match="not supported",
    ):
        validate_product_form(
            name="Test Product",
            url="https://www.walmart.com/example",
            target_price=Decimal("50.00"),
        )


def test_normalize_url_removes_fragment():
    result = normalize_product_url(
        "https://www.amazon.com/example#reviews"
    )

    assert result == "https://www.amazon.com/example"