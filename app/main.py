"""FastAPI application factory.

Run (dev): uv run uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, token
from app.core.exceptions import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="Vani MakeMyTrip token API")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(token.router)
    app.include_router(health.router)
    register_exception_handlers(app)
    return app


app = create_app()
