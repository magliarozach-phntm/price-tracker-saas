from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.models import (
    User,
    TrackedProduct,
)


def test_products_page_requires_login(
    client,
):
    response = client.get(
        "/products",
        follow_redirects=False,
    )

    assert response.status_code == 303

    assert response.headers[
        "location"
    ] == "/login"


def test_authenticated_user_can_view_products(
    authenticated_client,
    product,
):
    response = authenticated_client.get(
        "/products"
    )

    assert response.status_code == 200

    assert "Test Product" in response.text


def test_add_product(
    authenticated_client,
    db,
    user,
):
    response = authenticated_client.post(
        "/products/add",
        data={
            "name": "DJI Camera",
            "url": (
                "https://www.amazon.com/"
                "test-dji-camera"
            ),
            "target_price": "249.99",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    product = db.execute(
        select(TrackedProduct).where(
            TrackedProduct.name
            == "DJI Camera"
        )
    ).scalar_one_or_none()

    assert product is not None

    assert product.user_id == user.id

    assert (
        product.target_price
        == Decimal("249.99")
    )


def test_duplicate_product_rejected(
    authenticated_client,
    product,
):
    response = authenticated_client.post(
        "/products/add",
        data={
            "name": "Duplicate Product",
            "url": product.url,
            "target_price": "75.00",
        },
        follow_redirects=False,
    )

    assert response.status_code == 409


def test_unsupported_retailer_rejected(
    authenticated_client,
):
    response = authenticated_client.post(
        "/products/add",
        data={
            "name": "Walmart Product",
            "url": (
                "https://www.walmart.com/"
                "test-product"
            ),
            "target_price": "50.00",
        },
        follow_redirects=False,
    )

    assert response.status_code == 422

    assert (
            "currently supported retailers"
            in response.text.lower()
    )


def test_edit_product(
    authenticated_client,
    db,
    product,
):
    response = authenticated_client.post(
        f"/products/{product.id}/edit",
        data={
            "name": "Updated Product",
            "url": product.url,
            "target_price": "80.00",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    db.refresh(product)

    assert (
        product.name
        == "Updated Product"
    )

    assert (
        product.target_price
        == Decimal("80.00")
    )


def test_delete_product(
    authenticated_client,
    db,
    product,
):
    product_id = product.id

    response = authenticated_client.post(
        f"/products/{product_id}/delete",
        follow_redirects=False,
    )

    assert response.status_code == 303

    deleted_product = db.get(
        TrackedProduct,
        product_id,
    )

    assert deleted_product is None

def test_user_cannot_access_another_users_product(
    authenticated_client,
    db,
):
    other_user = User(
        name="Other User",
        email="other@example.com",
        password_hash=hash_password(
            "password123"
        ),
        timezone="America/New_York",
    )

    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    private_product = TrackedProduct(
        user_id=other_user.id,
        name="Private Product",
        url=(
            "https://www.amazon.com/"
            "private-product"
        ),
        target_price="100.00",
    )

    db.add(private_product)
    db.commit()
    db.refresh(private_product)

    response = authenticated_client.get(
        f"/products/{private_product.id}",
        follow_redirects=False,
    )

    assert response.status_code == 404

def test_user_cannot_edit_another_users_product(
    authenticated_client,
    db,
):
    other_user = User(
        name="Other User",
        email="other2@example.com",
        password_hash=hash_password(
            "password123"
        ),
        timezone="America/New_York",
    )

    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    private_product = TrackedProduct(
        user_id=other_user.id,
        name="Private Product",
        url=(
            "https://www.amazon.com/"
            "private-product-2"
        ),
        target_price="100.00",
    )

    db.add(private_product)
    db.commit()
    db.refresh(private_product)

    response = authenticated_client.post(
        f"/products/{private_product.id}/edit",
        data={
            "name": "Hacked Name",
            "url": private_product.url,
            "target_price": "1.00",
        },
        follow_redirects=False,
    )

    assert response.status_code == 404

    db.refresh(private_product)

    assert (
        private_product.name
        == "Private Product"
    )

def test_user_cannot_delete_another_users_product(
    authenticated_client,
    db,
):
    other_user = User(
        name="Other User",
        email="other3@example.com",
        password_hash=hash_password(
            "password123"
        ),
        timezone="America/New_York",
    )

    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    private_product = TrackedProduct(
        user_id=other_user.id,
        name="Private Product",
        url=(
            "https://www.amazon.com/"
            "private-product-3"
        ),
        target_price="100.00",
    )

    db.add(private_product)
    db.commit()
    db.refresh(private_product)

    product_id = private_product.id

    response = authenticated_client.post(
        f"/products/{product_id}/delete",
        follow_redirects=False,
    )

    assert response.status_code == 404

    assert db.get(
        TrackedProduct,
        product_id,
    ) is not None