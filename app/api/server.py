from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.api.api_products import router as products_router
from app.api.api_tracker import router as tracker_router
from app.api.api_auth import router as auth_router
from os import environ
from app.web.home import router as home_router
from app.web.dashboard import router as dashboard_router
from app.web.products import router as web_products_router
from app.web.auth import router as web_auth_router
import logging
from app.web.settings import router as settings_router
from fastapi import Request
from contextlib import asynccontextmanager

from app.services.scheduler.scheduler import (
    start_scheduler,
    stop_scheduler,
)
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.web import templates
from app.web.context import template_context


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting MAG PriceWatch"
    )

    start_scheduler()

    yield

    logger.info(
        "Shutting down MAG PriceWatch"
    )

    stop_scheduler()

app = FastAPI(
    title="Price Tracker SaaS",
    version="3.0",
    lifespan=lifespan,
)

@app.exception_handler(404)
def not_found_handler(
    request: Request,
    exc: StarletteHTTPException,
):
    return templates.TemplateResponse(
        request=request,
        name="errors/404.html",
        context=template_context(
            request=request,
            current_user=None,
        ),
        status_code=404,
    )


@app.exception_handler(Exception)
def internal_error_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Unhandled application error",
        exc_info=exc,
    )

    return templates.TemplateResponse(
        request=request,
        name="errors/500.html",
        context=template_context(
            request=request,
            current_user=None,
        ),
        status_code=500,
    )

HTTPS_ONLY = environ.get(
    "HTTPS_ONLY",
    "False",
).lower() == "true"

app.add_middleware(
    SessionMiddleware,
    secret_key=environ["SECRET_KEY"],
    https_only=HTTPS_ONLY,
    same_site="lax",
)

app.include_router(home_router)
app.include_router(settings_router)

app.include_router(
    products_router,
    prefix="/api/v1",
    tags=["Products"]
)

app.include_router(
    tracker_router,
    prefix="/api/v1",
    tags=["Tracker"]
)

app.include_router(
    auth_router,
    prefix="/api/v1",
    tags=["Authentication"]
)

app.mount(
    "/static",
    StaticFiles(directory='app/static'),
    name='static'
)

app.include_router(dashboard_router)
app.include_router(web_products_router)
app.include_router(web_auth_router)
