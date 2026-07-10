"""API request/response schemas."""

from pydantic import BaseModel, Field


class Envelope(BaseModel):
    """Uniform response shape: {success, message, data}."""

    success: bool
    message: str
    data: dict | None = None


class TokenRequest(BaseModel):
    agent_name: str = Field(min_length=1, max_length=64)
    id: str | None = None


class TokenData(BaseModel):
    """Inner `data` payload returned on a successful /token call."""

    token: str
    url: str
    room: str
