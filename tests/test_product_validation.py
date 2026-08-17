from decimal import Decimal

import pytest

from app.services.product_validation import (
    ProductValidationError,
    get_retailer,
    normalize_product_url,
    validate_product_form,
)


def test_valid_amazon_product():
    result = validate_product_form(
        name="DJI Mavic 4 Pro",
        url=(
            "https://www.amazon.com/"
            "DJI-Mavic-4-Pro/dp/B0DS49VDHG"
        ),
        target_price=Decimal("3500.00"),
    )

    assert result["name"] == "DJI Mavic 4 Pro"
    assert "amazon.com" in result["url"]
    assert result["target_price"] == Decimal("3500.00")
    assert result["retailer"] == "Amazon"


def test_valid_target_product():
    result = validate_product_form(
        name="Target Product",
        url=(
            "https://www.target.com/"
            "p/test-product/-/A-12345678"
        ),
        target_price=Decimal("25.00"),
    )

    assert result["name"] == "Target Product"
    assert "target.com" in result["url"]
    assert result["target_price"] == Decimal("25.00")
    assert result["retailer"] == "Target"


def test_amazon_retailer_detection():
    retailer = get_retailer(
        "https://www.amazon.com/test-product"
    )

    assert retailer == "Amazon"


def test_target_retailer_detection():
    retailer = get_retailer(
        "https://www.target.com/"
        "p/test-product/-/A-12345678"
    )

    assert retailer == "Target"


def test_product_name_is_trimmed():
    result = validate_product_form(
        name="   Test Product   ",
        url=(
            "https://www.target.com/"
            "p/test-product/-/A-12345678"
        ),
        target_price=Decimal("25.00"),
    )

    assert result["name"] == "Test Product"


def test_empty_product_name_rejected():
    with pytest.raises(
        ProductValidationError,
        match="Product name cannot be empty",
    ):
        validate_product_form(
            name="   ",
            url=(
                "https://www.target.com/"
                "p/test-product/-/A-12345678"
            ),
            target_price=Decimal("25.00"),
        )


def test_zero_target_price_rejected():
    with pytest.raises(
        ProductValidationError,
        match="Target price must be greater than zero",
    ):
        validate_product_form(
            name="Test Product",
            url=(
                "https://www.target.com/"
                "p/test-product/-/A-12345678"
            ),
            target_price=Decimal("0.00"),
        )


def test_negative_target_price_rejected():
    with pytest.raises(
        ProductValidationError,
        match="Target price must be greater than zero",
    ):
        validate_product_form(
            name="Test Product",
            url=(
                "https://www.target.com/"
                "p/test-product/-/A-12345678"
            ),
            target_price=Decimal("-10.00"),
        )


def test_invalid_url_rejected():
    with pytest.raises(
        ProductValidationError,
        match="valid product URL",
    ):
        validate_product_form(
            name="Test Product",
            url="www.target.com/test-product",
            target_price=Decimal("25.00"),
        )


def test_empty_url_rejected():
    with pytest.raises(
        ProductValidationError,
        match="Product URL is required",
    ):
        validate_product_form(
            name="Test Product",
            url="",
            target_price=Decimal("25.00"),
        )


def test_unsupported_retailer_rejected(
    authenticated_client,
):
    response = authenticated_client.post(
        "/products/add",
        data={
            "name": "Walmart Product",
            "url": "https://www.walmart.com/test-product",
            "target_price": "50.00",
        },
        follow_redirects=False,
    )

    assert response.status_code == 422

    assert (
        "currently supported retailers"
        in response.text.lower()
    )


def test_normalize_url_removes_fragment():
    result = normalize_product_url(
        "https://www.target.com/"
        "p/test-product/-/A-12345678#reviews"
    )

    assert result == (
        "https://www.target.com/"
        "p/test-product/-/A-12345678"
    )