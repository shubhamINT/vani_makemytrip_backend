# MakeMyTrip Travel Concierge — Voice Agent Backend

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](.python-version)
[![LiveKit Agents](https://img.shields.io/badge/LiveKit%20Agents-1.5-green.svg)](https://docs.livekit.io/agents/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-teal.svg)](https://fastapi.tiangolo.com/)

Voice-powered AI travel concierge for **MakeMyTrip**. Users speak naturally to search flights, browse hotels, plan itineraries, and book travel — and results appear visually on screen rather than being read aloud.

## Architecture

Two cooperating processes run together:

```
┌──────────────────────────────────────────────────────────┐
│                   Token API (FastAPI :8000)               │
│  POST /token → mints LiveKit JWT + dispatches agent      │
└──────────────┬───────────────────────────────────────────┘
               │  {token, url, room}
               ▼
┌──────────────────────────────────────────────────────────┐
│               Voice-Agent Worker (LiveKit)                │
│  Sarvam STT → OpenAI LLM → Sarvam TTS                     │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  "SHOW, DON'T TELL" — Two rendering paths:          │  │
│  │                                                     │  │
│  │  Typed-JSON topics  │  OpenUI-Lang  (ui.render)     │  │
│  │  ─────────────────  │  ─────────────────────         │  │
│  │  trip.hero          │  Itinerary (deterministic)    │  │
│  │  hotels.list        │  Budget (deterministic)       │  │
│  │  flights.list       │  Visa (deterministic)         │  │
│  │  experiences.list   │  render_ui (LLM fallback)     │  │
│  │  food.list          │                               │  │
│  │  detail.view        │                               │  │
│  │  booking.confirm    │                               │  │
│  │  trip.summary       │                               │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Request Flow

```
Web Client → POST /token → Mint LiveKit JWT + Dispatch Agent
          → Agent joins room → AgentSession started
          → User speaks → Sarvam STT → OpenAI LLM → Sarvam TTS
          → Results pushed to frontend via LiveKit text-streams
```

Every HTTP response uses one uniform envelope: `{success: bool, message: str, data: dict | null}`.

### Voice ⇄ Generative UI (Core Pattern)

The agent barely speaks results — it **shows** them. Tools push visual payloads to the frontend over LiveKit text-streams on custom topics, and the agent says one short line:

- **Typed-JSON topics** — Native frontend React components (HeroCard, HotelsSection, FlightsSection). Payloads match `streamTypes.ts` on the frontend.
- **OpenUI-Lang** — Streamed to the frontend's OpenUI `<Renderer>`, which builds UI live as statements arrive. Two sub-paths:
  - `render_ui` tool → dedicated LLM call authors OpenUI-Lang from a description
  - `show_itinerary/budget/visa` → deterministic Python builders (no LLM)

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Runtime** | Python | 3.12+ |
| **Package Manager** | [uv](https://docs.astral.sh/uv/) | — |
| **API Framework** | FastAPI | 0.115+ |
| **ASGI Server (dev)** | Uvicorn | 0.30+ |
| **ASGI Server (prod)** | Granian | 2.7.9+ |
| **Voice Pipeline** | LiveKit Agents | ~1.5 |
| **Speech-to-Text** | Sarvam AI (saaras:v3) | via LiveKit plugin |
| **LLM** | OpenAI GPT (gpt-5.4-mini) | via LiveKit plugin |
| **Text-to-Speech** | Sarvam AI (bulbul:v3) | via LiveKit plugin |
| **Turn Detection** | LiveKit Inference (v1-mini) | local model |
| **HTTP Client** | HTTPX | 0.27+ |
| **UI Rendering** | [OpenUI-Lang](https://openui.dev) | streaming generative UI |
| **Containerization** | Docker / Docker Compose | — |
| **Deployment** | Bash / Docker | — |

## Features

- **Voice-first travel search** — Natural language: *"Show me flights from Delhi to Kolkata on Friday"*
- **Multi-lingual STT** — Sarvam saaras:v3 in "codemix" mode handles English, Hindi, Bengali, Hinglish, Banglish
- **Generative UI** — Results appear visually on a dashboard with tabbed panels
- **Native dashboard tabs** — Overview, Hotels, Flights, Experiences, Food, Itinerary, Budget, Visa
- **Deterministic demos** — Curated travel data for Kolkata, Goa, Jaipur with real photo URLs
- **Stable PNR generation** — MD5-seeded booking codes (deterministic per session)
- **Live weather integration** — Trip summary card drives live weather widget
- **Booking confirmations** — E-ticket cards with "Add to calendar" and "View e-ticket" actions
- **Barge-in support** — Interrupt the agent mid-speech
- **Dockerized deployment** — Single `docker compose up` runs both services

## Project Structure

```
makemytrip_backed/
├── app/
│   ├── main.py                  # FastAPI app factory + CORS + exception handlers
│   ├── api/
│   │   ├── schemas.py           # Envelope, TokenRequest, TokenData
│   │   └── routes/
│   │       ├── token.py         # POST /token — mint + dispatch
│   │       └── health.py        # GET /health — liveness probe
│   ├── agent/
│   │   ├── __main__.py          # Entry: python -m app.agent
│   │   ├── worker.py            # TravelAgent class, tools, entrypoint
│   │   ├── instructions.py      # build_instructions() — persona text
│   │   ├── travel_data.py       # Curated demo data (Kolkata, Goa, Jaipur)
│   │   ├── openui_render.py     # Dedicated LLM call for OpenUI-Lang
│   │   ├── openui_prompt.py     # Standard OpenUI-Lang syntax spec
│   │   ├── openui_build.py      # Deterministic Itinerary/Budget/Visa builders
│   │   └── makemytrip_ui.py     # MakeMyTrip-specific rendering recipes
│   ├── core/
│   │   ├── config.py            # Env config (LiveKit creds, dispatch name)
│   │   ├── responses.py         # ok() — success envelope helper
│   │   └── exceptions.py        # Exception handlers in envelope format
│   └── services/
│       ├── livekit.py           # mint_token(), dispatch_agent()
│       └── context.py           # fetch_user() — caller context lookup
├── tests/
│   ├── test_instructions.py     # Persona instruction test
│   └── test_show_dispatch.py    # Show dispatch registry + data tests
├── server_run.py                # Prod launcher (granian)
├── run_both.sh                  # Dev launcher (API + agent)
├── Dockerfile                   # Multi-stage Docker build
├── docker-compose.yml           # API service + Agent service
├── deploy.sh                    # Git-pull + docker-compose deploy
├── pyproject.toml               # Dependencies
├── .env.example                 # Environment variable template
└── CLAUDE.md                    # Developer guidance for AI coding
```

## Getting Started

### Prerequisites

- Python **3.12+**
- [`uv`](https://docs.astral.sh/uv/) — Python package and venv manager
- A LiveKit server (or [LiveKit Cloud](https://cloud.livekit.io) account)
- OpenAI API key
- Sarvam AI API key

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd makemytrip_backed

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
```

### Configuration (`.env`)

| Variable | Required | Purpose |
|----------|----------|---------|
| `LIVEKIT_URL` | Yes | LiveKit server URL (e.g. `wss://your.livekit.cloud`) |
| `LIVEKIT_API_KEY` | Yes | LiveKit API key |
| `LIVEKIT_API_SECRET` | Yes | LiveKit API secret |
| `OPENAI_API_KEY` | Yes | OpenAI API key (for LLM + OpenUI render) |
| `SARVAM_API_KEY` | Yes | Sarvam AI API key (STT + TTS) |
| `USER_API_URL` | No | Optional user-context lookup endpoint |
| `OPENUI_RENDER_MODEL` | No | Model for OpenUI-Lang generation (default: `gpt-5.4-mini`) |
| `PORT` | No | HTTP port (default: `8000`) |
| `WORKERS` | No | Worker count (default: CPU count) |

### Run (Development)

Two processes must run together. Open two terminals:

```bash
# Terminal 1 — Token API
uv run uvicorn app.main:app --reload

# Terminal 2 — Voice Agent Worker
uv run python -m app.agent dev
```

### Run (Production)

```bash
# Option A: Run both together
./run_both.sh

# Option B: Docker Compose
docker compose up -d --build
```

### Deploy

```bash
# Pull latest code, rebuild, and restart
./deploy.sh
```

## API

### `POST /token`

Mints a LiveKit room-join token and dispatches the voice agent.

```bash
curl -X POST localhost:8000/token \
  -H 'content-type: application/json' \
  -d '{"agent_name":"voice-agent","id":"123"}'
```

Success response:
```json
{
  "success": true,
  "message": "token created",
  "data": {
    "token": "...",
    "url": "wss://...",
    "room": "voice-agent-123-ab12cd"
  }
}
```

Hand the returned `token` + `url` to a LiveKit web client (e.g. [Agents Playground](https://agents-playground.livekit.io)) to start the call.

### `GET /health`

```json
{
  "success": true,
  "message": "ok",
  "data": { "ok": true }
}
```

### Error Format

All errors use the same envelope. Example validation error:

```json
{
  "success": false,
  "message": "validation error",
  "data": { "errors": [...] }
}
```

Upstream LiveKit dispatch failures return HTTP 502.

## Agent Tools

The voice agent exposes these tools (all called by the LLM automatically):

| Tool | Purpose |
|------|---------|
| `show(kind, destination)` | Destination screens: overview, hotels, experiences, food, itinerary, budget, visa |
| `show_flights(origin, destination, date)` | Flight search results |
| `show_details(name)` | Detail view (gallery + description + facts) |
| `confirm_booking(item, kind, when, price, seat)` | Booking confirmation with PNR |
| `set_trip_summary(destination, dates, ...)` | Trip summary sidebar card + weather driver |
| `render_ui(request, tab, title)` | Fallback: LLM-generated OpenUI-Lang for anything not covered above |

### Dispatch Registry (`_SHOW`)

The generic `show` tool dispatches to seven "kinds" via a registry in `worker.py:108`:

- `overview` → typed JSON (hero/at-a-glance)
- `hotels` → typed JSON (hotel carousel)
- `experiences` → typed JSON (activity cards)
- `food` → typed JSON (restaurant cards)
- `itinerary` → OpenUI-Lang (day-by-day steps)
- `budget` → OpenUI-Lang (cost breakdown + fare chart)
- `visa` → OpenUI-Lang (entry requirements)

Adding a new kind = one row in the registry.

## Testing

```bash
# Run all tests
uv run python -m tests.test_instructions
uv run python -m tests.test_show_dispatch
```

Tests are plain-assert (no pytest). They verify:
- Persona instruction generation with/without user context (`test_instructions.py`)
- Show dispatch registry matches tool signature (`test_show_dispatch.py`)
- All data functions produce valid outputs for curated cities
- Hotel images come from real photo pool (no placeholder URLs)

## Demo Travel Data

The project ships with curated travel data for three destinations:

| Destination | Hotels | Experiences | Restaurants | Photo Pool |
|------------|--------|------------|-------------|------------|
| **Kolkata** | 3 (Taj Bengal, ITC Royal Bengal, Abhiray Grand) | 5 (Victoria Memorial, Howrah Bridge, Kalighat, River Cruise, Kumartuli) | 4 (Peter Cat, 6 Ballygunge Place, Flurys, Oh! Calcutta) | 14 real HTTPS images |
| **Goa** | 3 (Taj Fort Aguada, W Goa, The Leela) | 5 (Dudhsagar Falls, Old Goa Churches, Spice Plantation, Sunset Cruise, Scuba) | 4 (Fisherman's Wharf, Gunpowder, Thalassa, Britto's) | Same shared pool |
| **Jaipur** | 3 (Rambagh Palace, ITC Rajputana, Fairmont) | 5 (Amber Fort, City Palace, Hawa Mahal, Nahargarh, Chokhi Dhani) | 4 (LMB, Spice Court, Handi, Chokhi Dhani) | Same shared pool |

Any city not curated falls back to generated-but-resolving data so an off-script city still looks fine.

## Rendering Architecture

### When to use which path

| Content | Rendering Path | Topic |
|---------|---------------|-------|
| Destination hero / at-a-glance | Typed JSON | `trip.hero` |
| Hotels list | Typed JSON | `hotels.list` |
| Flights list | Typed JSON | `flights.list` |
| Experiences / Activities | Typed JSON | `experiences.list` |
| Restaurants / Food | Typed JSON | `food.list` |
| Item detail view | Typed JSON | `detail.view` |
| Booking confirmation | Typed JSON | `booking.confirmation` |
| Trip summary | Typed JSON | `trip.summary` |
| Itinerary (day-by-day) | OpenUI-Lang (deterministic) | `ui.render` |
| Budget breakdown | OpenUI-Lang (deterministic) | `ui.render` |
| Visa / entry info | OpenUI-Lang (deterministic) | `ui.render` |
| Everything else | OpenUI-Lang (LLM fallback) | `ui.render` |

### Key Design Decisions

- **Separate UI LLM** — The `render_ui` tool uses its own `AsyncOpenAI` client (configurable model, default `gpt-5.4-mini`) so the voice LLM stays low-latency
- **`parallel_tool_calls=True`** — Multiple tools fire together in one turn (e.g. `show` + `set_trip_summary`); each writes its own topic so writes don't race
- **Deterministic PNRs** — `_pnr(seed)` uses MD5 hashing so the same booking always gets the same PNR
- **Locked image URLs** — Photos from a shared pool, assigned deterministically by index so renders don't flicker between runs

## Development Workflow

- **Two-process architecture** — Always run the token API AND the agent worker together
- **No database** — State lives in the LiveKit room; "data" is curated Python dicts
- **No message queue** — Agent dispatch is the only coordination mechanism
- **Deployment** — `deploy.sh` pulls latest code via git, rebuilds Docker images, and restarts services with zero-downtime health check
- **Health checks** — Docker Compose uses in-container HTTP health checks (no curl dependency)

### Deployment Script (`deploy.sh`)

```bash
./deploy.sh
```

Checks for `.env`, pulls latest code, runs `docker compose up -d --build --wait`, and cleans up dangling images.

## Coding Standards

- **"SHOW, DON'T TELL"** — The single most important rule. Results go on screen, not in speech.
- **Short speech turns** — Agent says 1-2 sentences maximum per turn. Never recite prices/times aloud.
- **One question at a time** — Ask a follow-up only after showing something, and only for genuinely required details.
- **Deterministic demos** — No random or placeholder data. PNRs, images, and payloads are stable across runs.
- **Topic names = frontend contract** — Topic constants in `worker.py` and payload shapes in `travel_data.py` must match `streamTypes.ts` on the frontend.
- **Every UI tool returns a short string** — The return value tells the agent "Say one short line only — do not read it aloud."
- **OpenUI-Lang conventions** — One statement per line, `root =` first, positional args only, `null` for skipped args, every var (except `root`) must be referenced.
- **`ponytail:` comments** — Mark deliberate demo shortcuts or deferred work for future implementation.

## Contributing

1. Follow the `CLAUDE.md` guidance file for AI-assisted development
2. Read the OpenUI skill at `.agents/skills/openui/SKILL.md` before touching OpenUI-Lang generation
3. Maintain the `{success, message, data}` envelope for all API responses
4. Keep topic names and payload shapes in sync with the frontend's `streamTypes.ts`
5. Add curated demo data to `travel_data.py` when adding new destinations
6. Register new screen kinds in the `_SHOW` dictionary in `worker.py`
7. Ensure tests pass: `uv run python -m tests.test_instructions && uv run python -m tests.test_show_dispatch`
8. No linter/formatter is configured — maintain consistent style manually

## License

This project is part of MakeMyTrip's AI Concierge platform. Internal use.
