from contextlib import contextmanager
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy import select

from app.models import PriceHistory
from app.services import scraper
from app.services.scrapers import target
from app.services.scrapers.base import ScrapeResult
from app.services.tracking.tracker import check_product


def response(status=435, path='/cdui_orchestrations/v1/pages/pdp/deferred_enrichment/modules', host='www.target.com'):
    return SimpleNamespace(status=status, url=f'https://{host}{path}?secret=not-for-logs')


@pytest.mark.parametrize('status', [401, 403, 429, 435])
def test_product_data_block_statuses(status):
    blocked = []
    target._record_product_block(response(status), blocked)
    assert blocked == [(status, '/cdui_orchestrations/v1/pages/pdp/deferred_enrichment/modules')]


@pytest.mark.parametrize('item', [
    response(200), response(host='ads.example.com'),
    response(path='/analytics'),
    response(host='redsky.target.com', path='/redsky_aggregations/v1/web/nearby_stores_v1'),
])
def test_unrelated_responses_do_not_mark_product_blocked(item):
    blocked = []
    target._record_product_block(item, blocked)
    assert blocked == []


def price_page(text=None, content=None, selector='[data-test="product-price"]'):
    page = Mock()
    def locator(query):
        node = Mock()
        node.first = node
        node.count.return_value = int(query == selector)
        node.inner_text.return_value = text
        node.get_attribute.return_value = content
        return node
    page.locator.side_effect = locator
    return page


def test_modern_price_module():
    page = price_page('$129.99', selector='[data-test="module-product-detail-price-v2"]')
    assert target._find_rendered_price(page) == Decimal('129.99')


def test_metadata_price():
    assert target._find_rendered_price(price_page(content='129.99', selector='[itemprop="price"]')) == Decimal('129.99')


def test_ambiguous_container_rejected():
    page = price_page('$99.99 - $149.99', selector='[data-test="module-product-detail-price-v2"]')
    assert target._find_rendered_price(page) is None


def test_no_whole_page_price_fallback():
    page = price_page('Recommended product $9.99', selector='body')
    assert target._find_rendered_price(page) is None
    assert all(call.args[0] != 'body' for call in page.locator.call_args_list)


@pytest.fixture
def browser_page(monkeypatch):
    page = Mock()
    page.goto.return_value = response(200)
    page.title.return_value = 'Product : Target'
    page.url = 'https://www.target.com/p/item/-/A-123'
    browser = Mock()
    browser.new_context.return_value.new_page.return_value = page
    playwright = SimpleNamespace(chromium=SimpleNamespace(launch=lambda **kw: browser))
    @contextmanager
    def driver():
        try:
            yield playwright
        finally:
            browser.close.assert_called_once()
    monkeypatch.setattr(target, 'sync_playwright', driver)
    monkeypatch.setattr(target, '_get_stock_status', lambda page: None)
    return page, browser


def test_http_200_shell_with_blocked_data_fails(browser_page, monkeypatch):
    page, browser = browser_page
    def goto(*args, **kwargs):
        page.on.call_args.args[1](response())
        return response(200)
    page.goto.side_effect = goto
    extract = Mock()
    monkeypatch.setattr(target, '_find_rendered_price', extract)
    result = target.scrape_target(page.url)
    assert not result.success
    assert result.status_code == 435
    assert 'blocked' in result.error
    assert result.price is None and result.in_stock is None
    extract.assert_not_called()


def test_waits_for_delayed_price_without_networkidle(browser_page, monkeypatch):
    page, browser = browser_page
    monkeypatch.setattr(target, '_find_rendered_price', Mock(side_effect=[None, Decimal('129.99')]))
    result = target.scrape_target(page.url)
    assert result.success and result.price == Decimal('129.99')
    assert result.in_stock is None
    page.wait_for_timeout.assert_called_once_with(500)
    page.wait_for_load_state.assert_not_called()


def test_missing_data_wait_is_bounded(browser_page, monkeypatch):
    page, browser = browser_page
    monkeypatch.setattr(target, '_find_rendered_price', lambda page: None)
    monkeypatch.setattr(target.time, 'monotonic', Mock(side_effect=[0, 21]))
    assert not target.scrape_target(page.url).success
    page.wait_for_timeout.assert_not_called()


def test_http_error_cannot_become_a_price(browser_page):
    page, browser = browser_page
    page.goto.return_value = response(403)
    result = target.scrape_target(page.url)
    assert not result.success and result.status_code == 403


def test_block_arriving_during_extraction_rejects_price(browser_page, monkeypatch):
    page, browser = browser_page
    def extract(page):
        page.on.call_args.args[1](response())
        return Decimal('9.99')
    monkeypatch.setattr(target, '_find_rendered_price', extract)
    result = target.scrape_target(page.url)
    assert not result.success and result.price is None
    assert result.status_code == 435


def test_navigation_timeout_closes_browser(browser_page):
    page, browser = browser_page
    page.goto.side_effect = target.PlaywrightTimeoutError('timeout')
    assert not target.scrape_target(page.url).success


def test_block_leaves_history_and_alerts_untouched(db, product, monkeypatch):
    product.current_price = Decimal('125.00')
    product.is_in_stock = True
    db.commit()
    monkeypatch.setitem(scraper.SCRAPERS,
                        'target.', lambda url: target._failure('Target blocked', 435, 'Target'))
    product.url = 'https://www.target.com/p/item/-/A-123'
    db.commit()
    email = Mock()
    monkeypatch.setattr('app.services.tracking.tracker.send_email', email)
    with pytest.raises(ValueError, match='Target blocked'):
        check_product(product, db)
    db.refresh(product)
    assert product.current_price == Decimal('125.00')
    assert product.is_in_stock is True and product.last_checked is None
    assert not db.scalars(select(PriceHistory)).all()
    email.assert_not_called()


def test_unknown_stock_preserves_last_known_state(db, product, monkeypatch):
    product.is_in_stock = False
    db.commit()
    monkeypatch.setattr('app.services.tracking.tracker.scrape_product', lambda url: ScrapeResult(
        success=True, retailer='Target', price=Decimal('125.00'), in_stock=None))
    check_product(product, db)
    db.refresh(product)
    assert product.is_in_stock is False
