"""LiveKit voice agent worker: Sarvam STT + OpenAI LLM + Sarvam TTS.

Joins a room only when explicitly dispatched with agent_name="voice-agent".
Persona + optional user context arrive via the dispatch job metadata (JSON).

Run: uv run python -m app.agent dev
"""

import json
import logging
from typing import Literal

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
from app.agent.openui_render import stream_openui
from app.agent.travel_data import flights_for, hero_for, hotels_for
from app.core.config import AGENT_DISPATCH_NAME

logger = logging.getLogger("agent")

server = AgentServer()

# Topic for custom structured UI payloads pushed to the frontend. The frontend
# registers a text-stream handler for this topic and renders the openui-lang
# content using OpenUI's <Renderer> component.
# Kept off the reserved "lk.transcription" topic so the live transcript is
# unaffected.
UI_TOPIC = "ui.render"

# Typed-JSON topics rendered by the frontend's purpose-built native components
# (HeroCard / HotelsSection / FlightsSection). Hotels, flights and the
# destination hero go here — NOT through openui-lang. Shapes are the frontend
# contract in makemytrip_frontend/src/lib/streamTypes.ts.
HERO_TOPIC = "trip.hero"
HOTELS_TOPIC = "hotels.list"
FLIGHTS_TOPIC = "flights.list"

# Sarvam STT `prompt` (saaras:v3): domain-specific hint that biases the
# recognizer toward banking vocabulary and preserves proper nouns. Transcribes
# the CALLER's speech.
STT_PROMPT = (
    "A caller is talking to MakeMyTrip's voice travel assistant. The caller "
    "speaks English, Hindi, or Bengali and often mixes them (Hinglish, "
    "Banglish). Recognize and preserve city names, airport codes, airline and "
    "hotel names, dates, and PNRs accurately."
)


async def stream_ui_text(
    room, chunks, topic: str = UI_TOPIC, attributes: dict[str, str] | None = None
) -> None:
    """Stream openui-lang chunks to the frontend on a custom topic.

    The frontend's <Renderer> consumes the stream incrementally and builds the
    UI live as statements arrive. `attributes` (e.g. tab, title) ride along on
    the stream info so the dashboard can file each render under the right tab.
    """
    writer = await room.local_participant.stream_text(topic=topic, attributes=attributes)
    async for chunk in chunks:
        await writer.write(chunk)
    await writer.aclose()


async def publish_json(room, topic: str, payload: dict) -> None:
    """Send one JSON snapshot on a topic (snapshot semantics: replaces prior)."""

    async def _one():
        yield json.dumps(payload, ensure_ascii=False)

    await stream_ui_text(room, _one(), topic=topic)


class TravelAgent(Agent):
    def __init__(self, instructions: str) -> None:
        super().__init__(instructions=instructions)

    @function_tool()
    async def render_ui(
        self,
        context: RunContext,
        request: str,
        tab: Literal[
            "experiences",
            "food",
            "itinerary",
            "budget",
            "visa",
        ],
        title: str,
    ) -> str:
        """Display rich visual content on the user's screen.

        Use for experiences, food, itineraries, budgets, visa info, and booking
        confirmations/e-tickets — anything best shown rather than read aloud. A
        dedicated UI author turns your description into the visual; you write no
        markup. NOTE: hotels, flights and destination overviews have their own
        dedicated tools (show_hotels / show_flights / show_hero) — use those,
        not this, for those result types.

        Args:
            request: A complete natural-language description of what to show,
                INCLUDING every concrete data point (names, times, prices, PNR,
                seat, e-ticket/checkout URLs). For booking buttons, say what
                each button should do (e.g. "a Book button for IndiGo 6E-231 at
                06:10"). Be exhaustive — the author only has what you write here.
            tab: Which dashboard tab this render belongs under: "experiences"
                for activities/tours, "food" for restaurants, "itinerary" for
                day-by-day plans, "budget" for cost breakdowns, "visa" for
                visa/entry info.
            title: Short human label for the panel, e.g. "3 days in Kolkata".
                Shown above the render.
        """
        await stream_ui_text(
            context.session.room_io.room,
            stream_openui(request),
            attributes={"tab": tab, "title": title},
        )
        return "Shown on screen. Say one short line only — do not read it aloud."

    @function_tool()
    async def show_hotels(self, context: RunContext, destination: str) -> str:
        """Show the hotels carousel for a destination on the user's screen.

        Use this for ANY "show/find hotels", "where to stay", or hotel-results
        request — not render_ui. Renders the native Hotels tab.

        Args:
            destination: City or place, e.g. "Kolkata".
        """
        await publish_json(
            context.session.room_io.room, HOTELS_TOPIC, hotels_for(destination)
        )
        return "Shown on screen. Say one short line only — do not read it aloud."

    @function_tool()
    async def show_flights(
        self, context: RunContext, origin: str, destination: str, date: str = ""
    ) -> str:
        """Show the flights list for a route on the user's screen.

        Use this for ANY flight-search or flight-results request — not
        render_ui. Renders the native Flights tab.

        Args:
            origin: Departure city, e.g. "Delhi".
            destination: Arrival city, e.g. "Kolkata".
            date: Optional travel date, e.g. "24 May".
        """
        await publish_json(
            context.session.room_io.room,
            FLIGHTS_TOPIC,
            flights_for(origin, destination, date or None),
        )
        return "Shown on screen. Say one short line only — do not read it aloud."

    @function_tool()
    async def show_hero(self, context: RunContext, destination: str) -> str:
        """Show the destination overview hero (banner + at-a-glance stats).

        Call when the user picks a place, before drilling into hotels/flights.
        Renders the native Overview tab and drives the side-panel live weather.

        Args:
            destination: City or place, e.g. "Kolkata".
        """
        await publish_json(
            context.session.room_io.room, HERO_TOPIC, hero_for(destination)
        )
        return "Shown on screen. Say one short line only — do not read it aloud."

    @function_tool()
    async def set_trip_summary(
        self,
        context: RunContext,
        destination: str,
        dates: str,
        duration: str,
        travelers: str,
        budget: str,
    ) -> str:
        """Pin or update the trip summary card in the user's side panel.

        Call this as soon as you know the trip's shape, and again whenever any
        detail changes. The panel also shows live weather for `destination`, so
        keep it a clean city/place name (e.g. "Kolkata"). Use short human values.

        Args:
            destination: City or place, e.g. "Kolkata".
            dates: Travel dates, e.g. "24–26 May 2025" (or "Next weekend").
            duration: e.g. "2 nights / 3 days".
            travelers: e.g. "2 adults".
            budget: Estimated budget range, e.g. "₹28,000 – ₹32,000".
        """
        await publish_json(
            context.session.room_io.room,
            "trip.summary",
            {
                "destination": destination,
                "dates": dates,
                "duration": duration,
                "travelers": travelers,
                "budget": budget,
            },
        )
        return "Trip summary updated on screen."


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
    await session.generate_reply(
        instructions="Greet in one short sentence and ask what trip they want."
    )
