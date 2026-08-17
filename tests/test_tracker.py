from decimal import Decimal

from sqlalchemy import select

from app.models import PriceHistory
from app.services.scrapers.base import ScrapeResult
from app.services.tracking.tracker import check_product


def test_price_check_updates_current_price(
    db,
    product,
    monkeypatch,
):
    def fake_scrape_product(url):
        return ScrapeResult(
            success=True,
            retailer="Amazon",
            price=Decimal("125.00"),
            in_stock=True,
        )

    monkeypatch.setattr(
        "app.services.tracking.tracker.scrape_product",
        fake_scrape_product,
    )

    result = check_product(
        product,
        db,
    )

    assert product.current_price == Decimal("125.00")
    assert product.is_in_stock is True

    assert result.price == Decimal("125.00")
    assert result.in_stock is True


def test_price_history_created(
    db,
    product,
    monkeypatch,
):
    def fake_scrape_product(url):
        return ScrapeResult(
            success=True,
            retailer="Amazon",
            price=Decimal("125.00"),
            in_stock=True,
        )

    monkeypatch.setattr(
        "app.services.tracking.tracker.scrape_product",
        fake_scrape_product,
    )

    check_product(
        product,
        db,
    )

    history = db.execute(
        select(PriceHistory).where(
            PriceHistory.product_id == product.id
        )
    ).scalars().all()

    assert len(history) == 1
    assert history[0].price == Decimal("125.00")


def test_price_below_target_sends_alert(
    db,
    product,
    monkeypatch,
):
    def fake_scrape_product(url):
        return ScrapeResult(
            success=True,
            retailer="Amazon",
            price=Decimal("90.00"),
            in_stock=True,
        )

    sent_emails = []

    def fake_send_email(**kwargs):
        sent_emails.append(kwargs)

    monkeypatch.setattr(
        "app.services.tracking.tracker.scrape_product",
        fake_scrape_product,
    )

    monkeypatch.setattr(
        "app.services.tracking.tracker.send_email",
        fake_send_email,
    )

    result = check_product(
        product,
        db,
    )

    assert len(sent_emails) == 1

    assert sent_emails[0]["recipient"] == "test@example.com"
    assert sent_emails[0]["price"] == Decimal("90.00")

    assert product.last_alerted_price == Decimal("90.00")
    assert product.last_alerted_at is not None

    assert result.price_alert_sent is True


def test_same_price_does_not_send_duplicate_alert(
    db,
    product,
    monkeypatch,
):
    product.last_alerted_price = Decimal("90.00")
    db.commit()

    def fake_scrape_product(url):
        return ScrapeResult(
            success=True,
            retailer="Amazon",
            price=Decimal("90.00"),
            in_stock=True,
        )

    sent_emails = []

    def fake_send_email(**kwargs):
        sent_emails.append(kwargs)

    monkeypatch.setattr(
        "app.services.tracking.tracker.scrape_product",
        fake_scrape_product,
    )

    monkeypatch.setattr(
        "app.services.tracking.tracker.send_email",
        fake_send_email,
    )

    result = check_product(
        product,
        db,
    )

    assert len(sent_emails) == 0
    assert result.price_alert_sent is False


def test_lower_price_sends_new_alert(
    db,
    product,
    monkeypatch,
):
    product.last_alerted_price = Decimal("90.00")
    db.commit()

    def fake_scrape_product(url):
        return ScrapeResult(
            success=True,
            retailer="Amazon",
            price=Decimal("85.00"),
            in_stock=True,
        )

    sent_emails = []

    def fake_send_email(**kwargs):
        sent_emails.append(kwargs)

    monkeypatch.setattr(
        "app.services.tracking.tracker.scrape_product",
        fake_scrape_product,
    )

    monkeypatch.setattr(
        "app.services.tracking.tracker.send_email",
        fake_send_email,
    )

    result = check_product(
        product,
        db,
    )

    assert len(sent_emails) == 1

    assert product.last_alerted_price == Decimal("85.00")
    assert result.price_alert_sent is True


def test_out_of_stock_does_not_create_price_history(
    db,
    product,
    monkeypatch,
):
    product.is_in_stock = True
    db.commit()

    def fake_scrape_product(url):
        return ScrapeResult(
            success=True,
            retailer="Amazon",
            price=None,
            in_stock=False,
        )

    monkeypatch.setattr(
        "app.services.tracking.tracker.scrape_product",
        fake_scrape_product,
    )

    result = check_product(
        product,
        db,
    )

    history = db.execute(
        select(PriceHistory).where(
            PriceHistory.product_id == product.id
        )
    ).scalars().all()

    assert history == []

    assert product.is_in_stock is False
    assert result.in_stock is False


def test_back_in_stock_sends_stock_alert(
    db,
    product,
    monkeypatch,
):
    product.is_in_stock = False
    db.commit()

    def fake_scrape_product(url):
        return ScrapeResult(
            success=True,
            retailer="Amazon",
            price=Decimal("95.00"),
            in_stock=True,
        )

    stock_emails = []

    def fake_send_stock_email(**kwargs):
        stock_emails.append(kwargs)

    monkeypatch.setattr(
        "app.services.tracking.tracker.scrape_product",
        fake_scrape_product,
    )

    monkeypatch.setattr(
        "app.services.tracking.tracker.send_stock_email",
        fake_send_stock_email,
    )

    monkeypatch.setattr(
        "app.services.tracking.tracker.send_email",
        lambda **kwargs: None,
    )

    result = check_product(
        product,
        db,
    )

    assert len(stock_emails) == 1

    assert stock_emails[0]["recipient"] == "test@example.com"
    assert stock_emails[0]["product_name"] == "Test Product"

    assert product.is_in_stock is True
    assert product.last_stock_alert_at is not None

    assert result.stock_alert_sent is True


def test_in_stock_to_in_stock_does_not_send_stock_alert(
    db,
    product,
    monkeypatch,
):
    product.is_in_stock = True
    db.commit()

    def fake_scrape_product(url):
        return ScrapeResult(
            success=True,
            retailer="Amazon",
            price=Decimal("125.00"),
            in_stock=True,
        )

    stock_emails = []

    def fake_send_stock_email(**kwargs):
        stock_emails.append(kwargs)

    monkeypatch.setattr(
        "app.services.tracking.tracker.scrape_product",
        fake_scrape_product,
    )

    monkeypatch.setattr(
        "app.services.tracking.tracker.send_stock_email",
        fake_send_stock_email,
    )

    result = check_product(
        product,
        db,
    )

    assert len(stock_emails) == 0
    assert result.stock_alert_sent is False