# Target product data failures

An HTTP 200 product page is not proof that Target supplied price or availability.
During investigation of product A-1012568523, Chromium loaded the title, images,
and description, but the product-price module stayed empty after 30 seconds.
The page's own PDP enrichment requests returned HTTP 435, and related Target
responses contained a bot-verification challenge. The same missing-price symptom
was reported from both Railway's website and its Cron worker.

The scraper now watches Target PDP response statuses (401, 403, 429, 435) and
reports a blocked/rate-limited check instead of interpreting an empty page as a
price or stock update. It never logs challenge payloads or request query strings.
Ad/tracking failures and unrelated store-lookup responses do not fail the check.

When requests are allowed, the scraper polls for a product price for up to 20
seconds after navigation instead of relying on network-idle. It supports the
observed `module-product-detail-price-v2` container and price metadata. It rejects
ambiguous price containers and no longer takes an arbitrary dollar amount from
the body. Unknown availability stays unknown; it does not imply in-stock and does
not erase the database's last known stock state.

This change does **not** bypass Target's verification or restore pricing when
Target refuses access. Do not solve this by increasing Cron frequency or adding
aggressive retries. Reliable monitoring requires Target to allow these requests
or a permitted data provider/integration. The failure leaves existing prices,
history, and alert state intact. The worker still processes other products and
exits with a failure count.

Deploy the updated code to both the website and worker. Confirm the new error
message in a blocked check. A successful price/history/alert test still requires
an accessible product response; do not treat a deployed error-handling fix as
proof that live monitoring has recovered.
