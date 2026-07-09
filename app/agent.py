"""LiveKit voice agent worker: Sarvam STT + OpenAI LLM + Sarvam TTS.

Joins a room only when explicitly dispatched with agent_name="voice-agent".
Persona + optional user context arrive via the dispatch job metadata (JSON).

Run: uv run python -m app.agent dev
"""

import json
import logging

from livekit.agents import Agent, AgentServer, AgentSession, JobContext, cli
from livekit.plugins import openai, sarvam

from app.config import AGENT_DISPATCH_NAME

logger = logging.getLogger("agent")


def build_instructions(agent_name: str, user: dict | None) -> str:
    """Persona instructions, enriched with fetched user context when present."""
    base = (
        f"You are {agent_name}, a helpful voice assistant for SBI. "
        "Speak naturally and concisely. Answer in the user's language."
    )
    if user:
        base += f"\n\nYou are speaking with a known customer. Their details:\n{json.dumps(user, ensure_ascii=False)}"
    else:
        base += "\n\nThe caller is not identified. Do not assume any account details."
    return base


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


if __name__ == "__main__":
    cli.run_app(server)
