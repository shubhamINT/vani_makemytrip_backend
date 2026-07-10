"""Caller-context lookup by id."""

import logging

import httpx

from app.core.config import USER_API_URL

logger = logging.getLogger("context")


async def fetch_user(user_id: str) -> dict | None:
    """Fetch caller context by id. ponytail: stub — returns None on any failure
    or when USER_API_URL is unset, so a missing/bad lookup never fails the call.
    Wire the real endpoint by setting USER_API_URL."""
    if not USER_API_URL:
        return None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{USER_API_URL.rstrip('/')}/{user_id}")
            r.raise_for_status()
            return r.json()
    except Exception as e:  # noqa: BLE001 - best-effort enrichment
        logger.warning("user fetch failed for id=%s: %s", user_id, e)
        return None
