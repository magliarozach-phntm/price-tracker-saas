from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Price Tracker SaaS",
    version="2.0"
)

app.include_router(router)