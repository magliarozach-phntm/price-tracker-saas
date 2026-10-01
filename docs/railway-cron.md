# Railway hourly monitoring migration

Use two services from the same repository and the **existing PostgreSQL database**.
The web service serves FastAPI and manual Check Now requests. The worker runs
`python -m app.worker` once per hour and exits. Both call the same tracking service,
so price history, price alerts, stock alerts, and saved alert state use the same tables.
No database schema change or data migration is needed for this split.

| Setting | Existing website | New monitoring worker |
| --- | --- | --- |
| Railway Config File | `/railway.web.toml` | `/railway.worker.toml` |
| Start command | `bash start.sh` | `python -m app.worker` |
| Cron schedule | None | `0 * * * *` (hourly, UTC) |
| Restart policy | On failure | Never |
| Replicas | Keep existing | 1 |
| Public domain | Keep existing | None required |
| HTTP healthcheck | Keep existing | None |

Both configs build the Dockerfile, which installs the pinned Python packages and
Chromium with its Linux dependencies. The web image needs Chromium too, because
manual Check Now continues to scrape products. Do not set the website's start
command to the worker command. Config filenames must be selected in Railway;
committing these files alone does not create or configure a second service.

## Variables

- Set `DATABASE_URL` on both services to a reference to the **same existing**
  PostgreSQL service, for example `${{Postgres.DATABASE_URL}}` if named `Postgres`.
  Use the actual service name, in the same Railway environment.
- Give both services the existing `GMAIL_USER`, `GMAIL_PASS`, and optional
  `GMAIL_SERVER` values. Prefer shared/reference variables over duplicate secrets.
- Preserve the website's `SECRET_KEY` and `HTTPS_ONLY` values and its domain.
  The worker does not need the website's session secret or a port.
- The Dockerfile supplies `PLAYWRIGHT_BROWSERS_PATH=/ms-playwright`. Remove any
  conflicting service-level override so Chromium can be found in both services.

## Cutover

1. Configure the new worker service with its config path and variables before
   activating it. Clear inherited HTTP healthchecks and pre-deploy/start command
   overrides if duplicating the website. Keep it inactive until the next step.
2. Deploy this revision to the existing website using the web config. `start.sh`
   still applies Alembic migrations. Confirm login, product pages, and manual
   Check Now work. Wait for the old website deployment to stop; it still contains
   APScheduler. Automatic monitoring pauses until the new worker starts.
3. Deploy/activate the worker using the same revision after web migrations finish.
   Do not add migration commands to each hourly worker run.
4. Verify a run logs `Cycle finished checked=... skipped=... failed=...` and exits.
   Confirm the website shows its updated last-checked time and price history.
   Check that configured alert delivery works when an alert condition is met.
5. Verify another scheduled run, then inspect Railway usage over a full day.

The worker skips Amazon and other non-Target URLs without modifying them. Target
errors are logged per product and do not prevent later products from running.
Exit code 1 indicates a product/cycle failure; 0 means the cycle completed without
tracking failures, including an empty inventory. Email failures retain the existing
tracking service behavior: they are logged and do not fail an otherwise successful
price check. Restart policy Never avoids replaying a partially completed cycle
immediately; the next scheduled run will try again.

Railway skips a scheduled execution if the previous one has not exited. Monitor
run durations and failed runs; keep batches below an hour. Database sessions are
closed per product and the worker disposes its connection pool before exit.
Manual and scheduled checks may overlap, as with the previous scheduler; existing
alert suppression is based on saved state, not an exactly-once delivery guarantee.

The optimization removes the in-process scheduler and ends worker compute between
runs. The website and PostgreSQL still incur their own resource usage; this is not
a guarantee of free hosting. Website sleeping/serverless settings are unchanged.

## Local run and rollback

With dependencies, Chromium, a migrated development database, and email variables
configured, run `python -m app.worker` from the repository root. This writes real
history and may send alerts; use a development database for experiments.

To roll back, first stop the Cron worker, then redeploy the previous website
revision/build configuration with APScheduler. Never leave both automatic
schedulers active. No database rollback is necessary for this change.

References: [Railway Cron](https://docs.railway.com/cron-jobs),
[config as code](https://docs.railway.com/config-as-code/reference), and
[restart policies](https://docs.railway.com/deployments/restart-policy).
