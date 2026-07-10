"""FastAPI application factory.

Run (dev): uv run uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.api.routes import health, token
from app.core.exceptions import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="Vani SBI token API")
    app.include_router(token.router)
    app.include_router(health.router)
    register_exception_handlers(app)
    return app


app = create_app()
