# vani-sbi-backend

LiveKit web-call token API + voice agent (Sarvam STT · OpenAI LLM · Sarvam TTS).

## Setup
```bash
uv sync
cp .env.example .env   # fill in the keys
```

## Layout
```
app/
  config.py    # env-loaded settings (LiveKit creds, dispatch name, token TTL)
  api.py       # FastAPI app + POST /token
  agent.py     # voice worker (Sarvam STT / OpenAI LLM / Sarvam TTS)
  context.py   # id -> user-context lookup (stubbed)
tests/test_instructions.py
```

## Run (two processes)
```bash
uv run python -m app.agent dev          # voice agent worker
uv run uvicorn app.api:app --reload     # token API on :8000
```

## Use
```bash
curl -X POST localhost:8000/token -H 'content-type: application/json' \
  -d '{"agent_name":"support","id":"123"}'   # id optional
# -> { "token": "...", "url": "wss://...", "room": "support-123-xxxxxx" }
```
`agent_name` shapes the agent persona. When `id` is set and `USER_API_URL` is configured,
the backend fetches user context and injects it into the agent's instructions; otherwise the
agent runs generic. Give the returned `token` + `url` to a LiveKit web client (or the
[Agents Playground](https://agents-playground.livekit.io)) to start the call.
