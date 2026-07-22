# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

LiveKit voice-agent backend for a **MakeMyTrip travel concierge**. Two cooperating processes:
1. **Token API** (`app.main:app`, FastAPI) — `POST /token` mints a short-lived LiveKit JWT, dispatches the voice agent into the room, returns `{token, url, room}`.
2. **Voice-agent worker** (`app.agent`) — LiveKit agent: **Sarvam STT -> OpenAI LLM -> Sarvam TTS**. Joins only when dispatched with `agent_name="voice-agent"`.

Both must run together. Every HTTP response uses one envelope: `{success, message, data}`.

Note: package name and README still read `vani-sbi-backend` (pre-pivot from an SBI banking bot). The live product is MakeMyTrip travel — `worker.py`/`instructions.py` are the source of truth over the README.

## Commands

Setup: `uv sync` then `cp .env.example .env` and fill keys. Always run Python via `uv run ...`.

Dev (two terminals):
- `uv run uvicorn app.main:app --reload`   # token API :8000
- `uv run python -m app.agent dev`          # agent worker

Prod (both): `./run_both.sh`  (= granian `server_run.py` + agent worker)

Test: `uv run python -m tests.test_instructions`   # prints "ok"; plain-assert, no pytest configured

No linter/formatter is configured.

Required env: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `OPENAI_API_KEY`, `SARVAM_API_KEY`.
Optional: `USER_API_URL` (caller-context lookup; `id` lookups skipped if unset), `OPENUI_RENDER_MODEL`, `PORT`, `WORKERS`.

## Architecture

### Request flow
Web client -> `POST /token` (`app/api/routes/token.py`) -> `app/services/livekit.py` mints token + dispatches agent with JSON job metadata `{agent_name, user}` -> worker `entrypoint` (`app/agent/worker.py`) reads metadata, builds persona via `build_instructions()`, starts `AgentSession`. `AGENT_DISPATCH_NAME="voice-agent"` (config.py) must match the `@server.rtc_session(agent_name=...)` decorator — that's the dispatch contract. There is no database or message queue; state lives in the LiveKit room, "data" is curated Python dicts.

### Voice ⇄ generative UI (the core pattern)
The agent barely speaks results — it **shows** them. `instructions.py` enforces "SHOW, DON'T TELL": tools push visual payloads to the frontend over LiveKit text-streams on custom **topics**, and the agent says one short line. Two rendering paths:

1. **Typed-JSON topics** — native frontend components. `publish_json(room, topic, payload)` sends one JSON snapshot (replaces prior). Topics: `trip.hero`, `hotels.list`, `flights.list`, `experiences.list`, `food.list`, `detail.view`, `booking.confirmation`, `trip.summary`. Payload shapes are the frontend contract in `makemytrip_frontend/src/lib/streamTypes.ts` (separate repo) — data comes from `app/agent/travel_data.py`.

2. **OpenUI-Lang** on the `ui.render` topic — streamed to the frontend's OpenUI `<Renderer>`, which builds UI live as statements arrive. Stream attributes `{tab, title}` file each render under a dashboard tab. Two sub-paths:
   - `render_ui` tool -> `stream_openui()` (`openui_render.py`): a **separate dedicated LLM call** (its own `AsyncOpenAI` client, model `OPENUI_RENDER_MODEL`) authors OpenUI-Lang from a natural-language description. Kept off the voice LLM so voice stays low-latency.
   - `show_itinerary/budget/visa` -> deterministic builders in `openui_build.py` (no LLM), streamed via `publish_lang()`.

Routing rule of thumb: hotels/flights/hero/experiences/food/details/booking/summary = typed-JSON; itinerary/budget/visa = prebuilt OpenUI-Lang; anything else = `render_ui` LLM fallback.

### Key files
- `app/agent/worker.py` — `TravelAgent` (6 `@function_tool` UI tools), `entrypoint`, STT/LLM/TTS/turn-detection config, topic constants. Tools: `show(kind, destination)` (dispatches via the `_SHOW` registry to overview/hotels/experiences/food/itinerary/budget/visa — add a kind = add one registry row), `show_flights`, `show_details`, `confirm_booking`, `set_trip_summary`, `render_ui` (LLM fallback).
- `app/agent/instructions.py` — persona + tool-routing rules; `build_instructions(agent_name, user)`.
- `app/agent/travel_data.py` — curated demo travel data (`hotels_for`, `flights_for`, `hero_for`, etc.).
- `app/agent/openui_render.py` / `openui_prompt.py` / `openui_build.py` / `makemytrip_ui.py` — OpenUI-Lang generation, generic spec, deterministic builders, product render recipes.
- `app/core/config.py` — env config + `AGENT_DISPATCH_NAME`.
- `app/core/responses.py` / `exceptions.py` — success/error envelope.
- `app/services/livekit.py` — all LiveKit SDK calls (`dispatch_agent`, `mint_token`); `app/services/context.py` — stubbed `fetch_user`.

## Conventions
- OpenUI-Lang: one statement per line, `root =` first, positional args only (no `key=value`), `null` for skipped middle args, every var except `root` must be referenced or it's silently dropped, props map by Zod key order. Read the `openui` skill (`.agents/skills/openui/SKILL.md`) before touching OpenUI-Lang generation.
- Topic name constants in `worker.py` + payload shapes in `travel_data.py`/`openui_build.py` are a frozen contract with the frontend's `streamTypes.ts` — don't change one side alone.
- Every UI tool returns a short string telling the agent "Say one short line only — do not read it aloud."
- `parallel_tool_calls=False` on the voice LLM — serialized so UI packets don't race.
- Determinism for demo stability: PNRs (md5 seed), photo assignment, locked image URLs — renders don't flicker between runs.
- `ponytail:` comments mark deliberate demo shortcuts / deferred work.
- LiveKit docs available via MCP server `livekit-docs` (see `opencode.jsonc`).
