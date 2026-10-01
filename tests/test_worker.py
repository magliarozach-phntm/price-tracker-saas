from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app import worker
from app.models import PriceHistory, TrackedProduct
from app.services.scrapers.base import ScrapeResult


@pytest.fixture
def worker_db(db, monkeypatch):
    monkeypatch.setattr(worker, "SessionLocal", sessionmaker(bind=db.get_bind()))
    return db


@pytest.mark.parametrize("url,expected", [
    ("https://www.target.com/p/test", True),
    ("https://TARGET.COM/p/test", True),
    ("https://www.amazon.com/p/test", False),
    ("https://target.com.example.org/p/test", False),
    ("https://nottarget.com/p/test", False),
    ("https://[invalid", False),
])
def test_target_selection(url, expected):
    assert worker.is_target_url(url) is expected


def test_empty_cycle(worker_db):
    assert worker.check_all_products() == worker.CycleResult()


def test_cycle_preserves_history_and_alerts(worker_db, product, monkeypatch):
    product.url = "https://www.target.com/p/test"
    product.is_in_stock = False
    worker_db.commit()
    price_email, stock_email = Mock(), Mock()
    monkeypatch.setattr("app.services.tracking.tracker.send_email", price_email)
    monkeypatch.setattr("app.services.tracking.tracker.send_stock_email", stock_email)
    monkeypatch.setattr("app.services.tracking.tracker.scrape_product", lambda url: ScrapeResult(
        success=True, retailer="Target", price=Decimal("90.00"), in_stock=True,
    ))

    assert worker.check_all_products() == worker.CycleResult(checked=1)
    assert worker.check_all_products() == worker.CycleResult(checked=1)
    worker_db.expire_all()
    assert product.current_price == Decimal("90.00")
    assert product.last_checked is not None
    assert product.last_alerted_price == Decimal("90.00")
    assert product.last_stock_alert_at is not None
    assert len(worker_db.scalars(select(PriceHistory)).all()) == 2
    price_email.assert_called_once()
    stock_email.assert_called_once()


def test_failed_product_does_not_stop_cycle(worker_db, product, monkeypatch):
    product.url = "https://www.target.com/p/fails"
    worker_db.add_all([
        TrackedProduct(user_id=product.user_id, name="Good", target_price=100,
                       url="https://www.target.com/p/good"),
        TrackedProduct(user_id=product.user_id, name="Amazon", target_price=100,
                       url="https://www.amazon.com/p/saved"),
    ])
    worker_db.commit()

    def scrape(url):
        if url.endswith("fails"):
            raise ValueError("Retailer unavailable")
        return ScrapeResult(success=True, retailer="Target", price=Decimal("125"), in_stock=True)

    monkeypatch.setattr("app.services.tracking.tracker.scrape_product", scrape)
    assert worker.check_all_products() == worker.CycleResult(checked=1, skipped=1, failed=1)
    assert len(worker_db.scalars(select(PriceHistory)).all()) == 1


@pytest.mark.parametrize("failed,exit_code", [(0, 0), (1, 1)])
def test_main_exit_and_cleanup(monkeypatch, failed, exit_code):
    monkeypatch.setattr(worker, "check_all_products", lambda: worker.CycleResult(failed=failed))
    dispose = Mock()
    monkeypatch.setattr(worker.engine, "dispose", dispose)
    assert worker.main() == exit_code
    dispose.assert_called_once()


def test_database_failure_exits_and_cleans_up(monkeypatch):
    monkeypatch.setattr(worker, "SessionLocal", Mock(side_effect=RuntimeError("Database unavailable")))
    dispose = Mock()
    monkeypatch.setattr(worker.engine, "dispose", dispose)
    assert worker.main() == 1
    dispose.assert_called_once()


def test_website_does_not_run_cycle(client, monkeypatch):
    cycle = Mock(side_effect=AssertionError("Website must not schedule checks"))
    monkeypatch.setattr(worker, "check_all_products", cycle)
    assert client.get("/").status_code == 200
    cycle.assert_not_called()


def test_manual_check_still_saves_history(authenticated_client, product, db, monkeypatch):
    product.url = "https://www.target.com/p/manual"
    db.commit()
    monkeypatch.setattr("app.services.tracking.tracker.scrape_product", lambda url: ScrapeResult(
        success=True, retailer="Target", price=Decimal("125.00"), in_stock=True,
    ))
    response = authenticated_client.post(f"/products/{product.id}/check", follow_redirects=False)
    assert response.status_code == 303
    db.refresh(product)
    assert product.current_price == Decimal("125.00")
    assert len(db.scalars(select(PriceHistory)).all()) == 1
