"""GET /health — liveness probe."""

from fastapi import APIRouter

from app.core.responses import ok
from app.api.schemas import Envelope

router = APIRouter()


@router.get("/health", response_model=Envelope)
async def health() -> Envelope:
    return ok({"ok": True})
