"""Central config, loaded from the environment (.env)."""

import os

from dotenv import load_dotenv

load_dotenv()

LIVEKIT_URL = os.environ["LIVEKIT_URL"]
LIVEKIT_API_KEY = os.environ["LIVEKIT_API_KEY"]
LIVEKIT_API_SECRET = os.environ["LIVEKIT_API_SECRET"]

USER_API_URL = os.getenv("USER_API_URL")  # optional; id lookups skipped if unset

AGENT_DISPATCH_NAME = "voice-agent"  # must match app/agent/worker.py rtc_session(agent_name=...)
TOKEN_TTL_SECONDS = 60 * 30

# Model for the dedicated OpenUI-Lang render call (separate from the voice LLM).
OPENUI_RENDER_MODEL = os.getenv("OPENUI_RENDER_MODEL", "gpt-5.4-mini")
