"""Helpers for building the standard success envelope."""

from app.api.schemas import Envelope


def ok(data: dict | None = None, message: str = "ok") -> Envelope:
    """Wrap a payload in a success envelope."""
    return Envelope(success=True, message=message, data=data)
