"""FastAPI backend: mint a LiveKit room-join token for a web caller and
dispatch the voice agent into that room.

Run: uv run uvicorn app.api:app --reload
"""

import json
import logging
import secrets
from datetime import timedelta

from fastapi import FastAPI, HTTPException
from livekit import api
from pydantic import BaseModel, Field

from app import config
from app.context import fetch_user

logger = logging.getLogger("api")

app = FastAPI(title="Vani SBI token API")


class TokenRequest(BaseModel):
    agent_name: str = Field(min_length=1, max_length=64)
    id: str | None = None


class TokenResponse(BaseModel):
    token: str
    url: str
    room: str


@app.post("/token", response_model=TokenResponse)
async def create_token(req: TokenRequest) -> TokenResponse:
    user = await fetch_user(req.id) if req.id else None

    suffix = secrets.token_hex(3)
    room = f"{req.agent_name}-{req.id or 'web'}-{suffix}"
    identity = f"web-{suffix}"
    metadata = json.dumps({"agent_name": req.agent_name, "user": user})

    # Dispatch the agent into the room (auto-creates the room).
    try:
        lkapi = api.LiveKitAPI(config.LIVEKIT_URL, config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET)
        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(agent_name=config.AGENT_DISPATCH_NAME, room=room, metadata=metadata)
        )
        await lkapi.aclose()
    except Exception as e:  # noqa: BLE001
        logger.error("agent dispatch failed: %s", e)
        raise HTTPException(status_code=502, detail="agent dispatch failed") from e

    token = (
        api.AccessToken(config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(api.VideoGrants(room_join=True, room=room))
        .with_ttl(timedelta(seconds=config.TOKEN_TTL_SECONDS))
        .to_jwt()
    )
    return TokenResponse(token=token, url=config.LIVEKIT_URL, room=room)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
