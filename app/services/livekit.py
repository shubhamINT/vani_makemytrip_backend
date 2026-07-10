"""LiveKit interactions: dispatch the voice agent and mint room-join tokens."""

import logging
from datetime import timedelta

from fastapi import HTTPException
from livekit import api

from app.core import config

logger = logging.getLogger("livekit")


async def dispatch_agent(room: str, metadata: str) -> None:
    """Dispatch the voice agent into `room` (auto-creates the room).

    Raises HTTPException(502) if the LiveKit dispatch fails.
    """
    try:
        lkapi = api.LiveKitAPI(config.LIVEKIT_URL, config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET)
        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(agent_name=config.AGENT_DISPATCH_NAME, room=room, metadata=metadata)
        )
        await lkapi.aclose()
    except Exception as e:  # noqa: BLE001
        logger.error("agent dispatch failed: %s", e)
        raise HTTPException(status_code=502, detail="agent dispatch failed") from e


def mint_token(identity: str, room: str) -> str:
    """Create a JWT that lets `identity` join `room`."""
    return (
        api.AccessToken(config.LIVEKIT_API_KEY, config.LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(api.VideoGrants(room_join=True, room=room))
        .with_ttl(timedelta(seconds=config.TOKEN_TTL_SECONDS))
        .to_jwt()
    )
