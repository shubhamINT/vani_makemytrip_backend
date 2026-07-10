# vani-sbi-backend

LiveKit web-call token API + a Sarvam/OpenAI voice agent for SBI.

## Purpose

Two cooperating processes:

1. **Token API** (`app.main:app`) — a FastAPI service. A web caller asks for a
   room-join token; the API mints a short-lived LiveKit JWT, dispatches the voice
   agent into that room, and returns `{token, url, room}`.
2. **Voice agent worker** (`app.agent`) — a LiveKit agent that joins the dispatched
   room and runs the conversation: **Sarvam STT → OpenAI LLM → Sarvam TTS**.

Every HTTP response uses one envelope: `{ "success": bool, "message": str, "data": {...} | null }`.

## Prerequisites

- Python **3.12+**
- [`uv`](https://docs.astral.sh/uv/) (dependency + venv manager)
- LiveKit server + API key/secret, an OpenAI key, and a Sarvam key

## Setup

```bash
uv sync
cp .env.example .env   # then fill in the keys (create .env.example if absent)
```

`.env` variables:

| Var | Required | Purpose |
|-----|----------|---------|
| `LIVEKIT_URL` | yes | LiveKit server URL (e.g. `wss://your.livekit.cloud`) |
| `LIVEKIT_API_KEY` | yes | LiveKit API key |
| `LIVEKIT_API_SECRET` | yes | LiveKit API secret |
| `USER_API_URL` | no | Caller-context lookup endpoint; `id` lookups are skipped if unset |
| `PORT` | no | Prod HTTP port (default `8000`) |
| `WORKERS` | no | Prod worker count (default = CPU count) |

Sarvam/OpenAI keys are read by the LiveKit plugins from their standard env vars
(`OPENAI_API_KEY`, `SARVAM_API_KEY`) — put them in `.env` too.

## Run

Two processes must run together (API + agent worker).

**Development:**
```bash
uv run uvicorn app.main:app --reload      # token API on :8000
uv run python -m app.agent dev            # voice agent worker
```

**Production (both at once, granian):**
```bash
./run_both.sh
# = `uv run server_run.py` (granian → app.main:app) + `uv run python -m app.agent dev`
```

## File-by-file

| Path | Purpose |
|------|---------|
| `app/main.py` | App factory `create_app()`; wires routers + exception handlers. ASGI entry `app`. |
| `app/core/config.py` | Env-loaded settings (LiveKit creds, dispatch name, token TTL). |
| `app/core/responses.py` | `ok(data, message)` — builds the success envelope. |
| `app/core/exceptions.py` | `register_exception_handlers(app)` — renders errors in the envelope. |
| `app/api/schemas.py` | API schemas: `Envelope`, `TokenRequest`, `TokenData`. |
| `app/api/routes/token.py` | `POST /token` — thin handler calling the services. |
| `app/api/routes/health.py` | `GET /health` — liveness probe. |
| `app/services/livekit.py` | `dispatch_agent()` + `mint_token()` (all LiveKit calls). |
| `app/services/context.py` | `fetch_user(id)` — caller-context lookup (stubbed). |
| `app/agent/worker.py` | Voice agent worker: `AgentServer` + `rtc_session` entrypoint. |
| `app/agent/instructions.py` | `build_instructions()` — agent persona text. |
| `app/agent/__main__.py` | Makes `python -m app.agent` launch the worker CLI. |
| `server_run.py` | Prod launcher: granian serving `app.main:app`. |
| `run_both.sh` | Starts API + agent worker together. |
| `tests/test_instructions.py` | Unit test for persona instruction building. |

## API

### `POST /token`
```bash
curl -X POST localhost:8000/token -H 'content-type: application/json' \
  -d '{"agent_name":"support","id":"123"}'   # id optional
```
```json
{
  "success": true,
  "message": "token created",
  "data": { "token": "…", "url": "wss://…", "room": "support-123-ab12cd" }
}
```
`agent_name` shapes the agent persona. When `id` is set and `USER_API_URL` is
configured, the backend fetches user context and injects it into the agent's
instructions; otherwise the agent runs generic. Hand the returned `token` + `url`
to a LiveKit web client (or the
[Agents Playground](https://agents-playground.livekit.io)) to start the call.

### `GET /health`
```json
{ "success": true, "message": "ok", "data": { "ok": true } }
```

### Errors
Errors use the same envelope, e.g. missing `agent_name`:
```json
{ "success": false, "message": "validation error", "data": { "errors": [ … ] } }
```
Upstream LiveKit dispatch failure returns `502` with
`{ "success": false, "message": "agent dispatch failed", "data": null }`.

## Testing
```bash
uv run python -m tests.test_instructions   # -> ok
```
