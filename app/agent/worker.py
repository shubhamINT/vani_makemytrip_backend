"""LiveKit voice agent worker: Sarvam STT + OpenAI LLM + Sarvam TTS.

Joins a room only when explicitly dispatched with agent_name="voice-agent".
Persona + optional user context arrive via the dispatch job metadata (JSON).

Run: uv run python -m app.agent dev
"""

import hashlib
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

from app.agent import openui_build as ob
from app.agent import travel_data as td
from app.agent.instructions import build_instructions
from app.agent.openui_render import stream_openui
from app.agent.travel_data import flights_for
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
EXPERIENCES_TOPIC = "experiences.list"
FOOD_TOPIC = "food.list"
DETAIL_TOPIC = "detail.view"
BOOKING_TOPIC = "booking.confirmation"

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


async def publish_lang(room, lang: str, tab: str) -> None:
    """Stream a full openui-lang string on ui.render, filed under `tab`.

    title="" so the frontend shows no extra <h2> — the lang's own CardHeader is
    the panel heading (avoids the doubled-header bug).
    """

    async def _one():
        yield lang

    await stream_ui_text(room, _one(), attributes={"tab": tab, "title": ""})


# Dispatch registry for the generic `show` tool: kind -> async fn(room, dest).
# Reuses publish_json / publish_lang + travel_data + openui_build — adding a new
# kind of screen is one row here, not a new @function_tool.
_SHOW = {
    "overview":    lambda room, d: publish_json(room, HERO_TOPIC,        td.hero_for(d)),
    "hotels":      lambda room, d: publish_json(room, HOTELS_TOPIC,      td.hotels_for(d)),
    "experiences": lambda room, d: publish_json(room, EXPERIENCES_TOPIC, td.experiences_for(d)),
    "food":        lambda room, d: publish_json(room, FOOD_TOPIC,        td.food_for(d)),
    "itinerary":   lambda room, d: publish_lang(room, ob.itinerary_lang(td.itinerary_for(d)), "itinerary"),
    "budget":      lambda room, d: publish_lang(room, ob.budget_lang(d, td.budget_for(d)), "budget"),
    "visa":        lambda room, d: publish_lang(room, ob.visa_lang(d, td.visa_for(d)), "visa"),
}


def _pnr(seed: str) -> str:
    """Stable, PNR-looking 6-char code from a seed (deterministic per booking)."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"
    n = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    out = ""
    for _ in range(6):
        out += alphabet[n % len(alphabet)]
        n //= len(alphabet)
    return out


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
        """Display rich visual content on the user's screen — FALLBACK ONLY.

        Use only for something the dedicated tools don't cover, best shown
        rather than read aloud. A dedicated UI author turns your description
        into the visual; you write no markup. NOTE: overview/hotels/experiences/
        food/itinerary/budget/visa go through show(kind, destination); flights
        through show_flights; item details through show_details; bookings
        through confirm_booking — use those, not this, for those result types.

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
    async def show(
        self,
        context: RunContext,
        kind: Literal[
            "overview",
            "hotels",
            "experiences",
            "food",
            "itinerary",
            "budget",
            "visa",
        ],
        destination: str,
    ) -> str:
        """Show trip content for a destination on the user's screen.

        The one tool for destination-keyed screens — prefer it over render_ui.
        Flights, item details, and bookings have their own tools.

        Args:
            kind: What to show —
                "overview": destination hero/at-a-glance (call when a place is
                    picked, before drilling in — also drives live weather),
                "hotels": where to stay,
                "experiences": things to do / activities / sightseeing,
                "food": restaurants / where to eat,
                "itinerary": day-by-day plan,
                "budget": estimated cost breakdown,
                "visa": entry / visa requirements.
            destination: Clean city name, e.g. "Kolkata".
        """
        await _SHOW[kind](context.session.room_io.room, destination)
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
    async def show_details(self, context: RunContext, name: str) -> str:
        """Show a full detail view (image gallery + description + facts) for one
        hotel, restaurant or experience.

        Call this for "show me more details / tell me more about X" — it shows a
        richer view than the card list, with multiple photos.

        Args:
            name: The item to detail, e.g. "Taj Bengal" or "Victoria Memorial Tour".
        """
        await publish_json(
            context.session.room_io.room, DETAIL_TOPIC, td.details_for(name)
        )
        return "Shown on screen. Say one short line only — do not read it aloud."

    @function_tool()
    async def confirm_booking(
        self,
        context: RunContext,
        item: str,
        kind: Literal["flight", "hotel", "experience"],
        when: str,
        price: str,
        seat: str = "",
        ticket_url: str = "",
    ) -> str:
        """Render a booking confirmation / e-ticket card after a "Book …" request.

        Call this once you have confirmed the booking details. Generates a PNR
        and pins the confirmation card (with e-ticket link) on the screen.

        Args:
            item: What was booked, self-sufficient, e.g. "IndiGo 6E 2041, Delhi
                to Kolkata 06:20" or "Taj Bengal, Alipore".
            kind: "flight", "hotel" or "experience".
            when: Date/time, e.g. "Fri 24 May · 06:20 DEL → 08:45 CCU".
            price: Total paid, e.g. "₹5,600".
            seat: Optional seat/room detail, e.g. "Seat 14A · Window".
            ticket_url: Optional e-ticket URL; a demo link is generated if empty.
        """
        pnr = _pnr(f"{item}|{when}")
        headline = {
            "flight": "You're all set to fly!",
            "hotel": "Your stay is booked!",
            "experience": "Your booking is confirmed!",
        }[kind]
        details = [{"label": "When", "value": when}]
        if seat:
            details.insert(0, {"label": "Room" if kind == "hotel" else "Seat", "value": seat})
        details.append({"label": "Total paid", "value": price})
        payload = {
            "kind": kind,
            "title": f"{kind.capitalize()} Booking Confirmation",
            "status": "Booking confirmed",
            "reference": f"PNR {pnr}",
            "headline": headline,
            "subhead": item,
            "details": details,
            "actions": [
                {"label": "View e-ticket", "url": ticket_url or f"https://makemytrip.com/booking/{pnr}", "variant": "primary"},
                {"label": "Add to calendar", "action": f"Add {item} to my calendar", "variant": "secondary"},
            ],
        }
        await publish_json(context.session.room_io.room, BOOKING_TOPIC, payload)
        return f"Booked. PNR {pnr}. Say one short line only — do not read it aloud."

    @function_tool()
    async def set_trip_summary(
        self,
        context: RunContext,
        destination: str,
        dates: str,
        duration: str,
        travelers: str,
        budget: str,
        full_plan_action: str = "",
    ) -> str:
        """Pin or update the trip summary card in the user's side panel.

        Call this as soon as you know the destination — it also drives the live
        Weather card, so send it early and keep `destination` a clean city name
        (e.g. "Kolkata"). Update whenever any detail changes. Short human values.

        Args:
            destination: City or place, e.g. "Kolkata".
            dates: Travel dates, e.g. "24–26 May 2025" (or "Next weekend").
            duration: e.g. "2 nights / 3 days".
            travelers: e.g. "2 adults".
            budget: Estimated budget range, e.g. "₹28,000 – ₹32,000".
            full_plan_action: Optional message the "View Full Plan →" button
                sends, e.g. "Show me the full trip plan for Kolkata".
        """
        payload = {
            "destination": destination,
            "dates": dates,
            "duration": duration,
            "travelers": travelers,
            "budget": budget,
        }
        if full_plan_action:
            payload["fullPlanAction"] = full_plan_action
        await publish_json(context.session.room_io.room, "trip.summary", payload)
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
            model="gpt-5.4-mini",
            # Fire tools together in one turn (e.g. show + set_trip_summary).
            # Safe: each tool writes its own topic, so concurrent writes don't race.
            parallel_tool_calls=True,
        ),
        tts=sarvam.TTS(model="bulbul:v3", target_language_code="en-IN", speaker = 'simran'),
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
