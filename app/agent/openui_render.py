"""Dedicated LLM call that authors OpenUI-Lang for the `render_ui` tool.

Kept separate from the voice LLM so the conversational model stays lean and
fast (no big UI spec in its context) while a focused call handles layout.
Streams line-by-line so the frontend `<Renderer>` builds the UI live.
"""

from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.agent.makemytrip_ui import MAKEMYTRIP_UI_GUIDE
from app.agent.openui_prompt import OPENUI_SYSTEM_PROMPT
from app.core.config import OPENUI_RENDER_MODEL

_client = AsyncOpenAI()  # reads OPENAI_API_KEY

# Standard OpenUI-Lang (syntax + components) + MakeMyTrip render recipes.
_SYSTEM = (
    OPENUI_SYSTEM_PROMPT
    + "\n\n"
    + MAKEMYTRIP_UI_GUIDE
    + "\n\nYou are the UI author. Turn the request below into OpenUI-Lang using "
    "the MakeMyTrip recipes above. Output ONLY raw OpenUI-Lang starting with "
    "`root = Card(`. No markdown fences, no prose, no explanation."
)


async def stream_openui(request: str) -> AsyncIterator[str]:
    """Stream OpenUI-Lang generated from a natural-language description.

    Line-buffered: emits on each newline and drops any ``` fence line, so a
    model that wraps its output in a code block despite the instruction still
    yields clean OpenUI-Lang. OpenUI-Lang is one-statement-per-line, so this
    costs negligible latency.
    """
    stream = await _client.chat.completions.create(
        model=OPENUI_RENDER_MODEL,
        stream=True,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": request},
        ],
    )
    buf = ""
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if not delta:
            continue
        buf += delta
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            if line.strip().startswith("```"):  # ponytail: drop stray fences
                continue
            yield line + "\n"
    # trailing partial line (no final newline)
    if buf and not buf.strip().startswith("```"):
        yield buf
