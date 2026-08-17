import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.server import app
from app.core.database import (
    Base,
    get_db,
)
from app.core.security import hash_password
from app.models import (
    User,
    TrackedProduct,
)


TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"


engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)


TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture
def db():
    Base.metadata.create_all(
        bind=engine
    )

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.close()

        Base.metadata.drop_all(
            bind=engine
        )


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db

        finally:
            pass

    app.dependency_overrides[
        get_db
    ] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def user(db):
    new_user = User(
        name="Test User",
        email="test@example.com",
        password_hash=hash_password(
            "password123"
        ),
        timezone="America/New_York",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@pytest.fixture
def product(
    db,
    user,
):
    new_product = TrackedProduct(
        user_id=user.id,
        name="Test Product",
        url="https://www.amazon.com/test-product",
        target_price="100.00",
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@pytest.fixture
def authenticated_client(
    client,
    user,
):
    response = client.post(
        "/login",
        data={
            "email": user.email,
            "password": "password123",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303

    return client