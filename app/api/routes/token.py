"""POST /token — mint a LiveKit room-join token and dispatch the voice agent."""

import json
import secrets

from fastapi import APIRouter

from app.core import config
from app.core.responses import ok
from app.api.schemas import Envelope, TokenData, TokenRequest
from app.services.context import fetch_user
from app.services.livekit import dispatch_agent, mint_token

router = APIRouter()


@router.post("/token", response_model=Envelope)
async def create_token(req: TokenRequest) -> Envelope:
    user = await fetch_user(req.id) if req.id else None

    suffix = secrets.token_hex(3)
    room = f"{req.agent_name}-{req.id or 'web'}-{suffix}"
    identity = f"web-{suffix}"
    metadata = json.dumps({"agent_name": req.agent_name, "user": user})

    await dispatch_agent(room, metadata)
    token = mint_token(identity, room)

    data = TokenData(token=token, url=config.LIVEKIT_URL, room=room)
    return ok(data.model_dump(), "token created")
