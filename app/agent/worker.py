"""LiveKit voice agent worker: Sarvam STT + OpenAI LLM + Sarvam TTS.

Joins a room only when explicitly dispatched with agent_name="voice-agent".
Persona + optional user context arrive via the dispatch job metadata (JSON).

Run: uv run python -m app.agent dev
"""

import json
import logging

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    TurnHandlingOptions,
    function_tool,
    inference,
    room_io,
)
from livekit.plugins import openai, sarvam

from app.agent.instructions import build_instructions
from app.core.config import AGENT_DISPATCH_NAME

logger = logging.getLogger("agent")

server = AgentServer()

# Topic for custom structured UI payloads pushed to the frontend. The frontend
# registers a text-stream handler for this topic and renders the openui-lang
# content using OpenUI's <Renderer> component.
# Kept off the reserved "lk.transcription" topic so the live transcript is
# unaffected.
UI_TOPIC = "ui.render"

# Sarvam STT `prompt` (saaras:v3): domain-specific hint that biases the
# recognizer toward banking vocabulary and preserves proper nouns. Transcribes
# the CALLER's speech.
STT_PROMPT = (
    "A caller is talking to MakeMyTrip's voice travel assistant. The caller "
    "speaks English, Hindi, or Bengali and often mixes them (Hinglish, "
    "Banglish). Recognize and preserve city names, airport codes, airline and "
    "hotel names, dates, and PNRs accurately."
)


async def send_ui_text(room, text: str, topic: str = UI_TOPIC) -> None:
    """Push raw openui-lang text to the frontend on a custom topic."""
    await room.local_participant.send_text(text, topic=topic)


class TravelAgent(Agent):
    def __init__(self, instructions: str) -> None:
        super().__init__(instructions=instructions)

    @function_tool()
    async def render_ui(
        self,
        context: RunContext,
        openui_lang: str,
    ) -> str:
        """Display rich visual content on the user's screen using openui-lang.

        Use when results are best shown visually (flight/hotel search results,
        booking confirmations and e-tickets, trip itineraries, comparisons)
        rather than read aloud.

        Args:
            openui_lang: The openui-lang code describing the UI to render.
                Must start with a `root = Card(...)` statement.
        """
        await send_ui_text(context.session.room_io.room, openui_lang)
        return "Showing UI on screen. Briefly tell the user to check the display."


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

    # VAD: AgentSession bundles silero VAD by default; no explicit vad= needed.
    session = AgentSession(
        stt=sarvam.STT(
            model="saaras:v3",
            mode="codemix",
            language="unknown",  # auto-detect from speech
            prompt=STT_PROMPT,
            # Noise rejection (saaras:v3 VAD) — tune against real recordings.
            high_vad_sensitivity=False,
            positive_speech_threshold=0.85,
            negative_speech_threshold=0.35,
            min_speech_frames=8,
            num_initial_ignored_frames=4,
        ),
        llm=openai.LLM(
            model="gpt-4o-mini",
            parallel_tool_calls=False,  # serialize tool calls; avoids racing UI packets
        ),
        tts=sarvam.TTS(model="bulbul:v3", target_language_code="en-IN"),
        use_tts_aligned_transcript=True,
        turn_handling=TurnHandlingOptions(
            # v1-mini runs the bundled local model (no cloud inference gateway);
            # drop version= to auto-use cloud v1 if LIVEKIT_INFERENCE_URL is set.
            turn_detection=inference.TurnDetector(version="v1-mini"),
            endpointing={"min_delay": 0.3, "max_delay": 0.6},
            interruption={
                "enabled": True,
                "min_words": 0,  # interrupt on voice activity → instant barge-in stop
                "min_duration": 0.3,
                "resume_false_interruption": True,  # noise-only pause → resume
                "false_interruption_timeout": 0.7,
            },
            preemptive_generation={},  # default-on; speculative LLM start
        ),
    )

    await session.start(
        room=ctx.room,
        agent=TravelAgent(instructions=build_instructions(agent_name, user)),
        room_options=room_io.RoomOptions(
            text_input=True,
            audio_input=True,
            audio_output=True,
            close_on_disconnect=True,
            delete_room_on_close=True,
        ),
    )
    await session.generate_reply(instructions="Greet the user and offer help.")
