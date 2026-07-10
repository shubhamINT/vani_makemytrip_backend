"""LiveKit voice agent worker: Sarvam STT + OpenAI LLM + Sarvam TTS.

Joins a room only when explicitly dispatched with agent_name="voice-agent".
Persona + optional user context arrive via the dispatch job metadata (JSON).

Run: uv run python -m app.agent dev
"""

import json
import logging

from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import openai, sarvam

from app.agent.instructions import build_instructions
from app.core.config import AGENT_DISPATCH_NAME

logger = logging.getLogger("agent")

server = AgentServer()


@server.rtc_session(agent_name=AGENT_DISPATCH_NAME)
async def entrypoint(ctx: JobContext) -> None:
    meta = {}
    if ctx.job.metadata:
        try:
            meta = json.loads(ctx.job.metadata)
        except json.JSONDecodeError:
            logger.warning("bad job metadata, ignoring: %r", ctx.job.metadata)

    agent_name = meta.get("agent_name") or "Assistant"
    user = meta.get("user")
    logger.info("starting session agent=%s user=%s", agent_name, bool(user))

    await ctx.connect()

    session = AgentSession(
        stt=sarvam.STT(language="en-IN", model="saaras:v3"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=sarvam.TTS(target_language_code="en-IN", model="bulbul:v3"),
    )
    await session.start(room=ctx.room, agent=Agent(instructions=build_instructions(agent_name, user)))
    await session.generate_reply(instructions="Greet the user and offer help.")
