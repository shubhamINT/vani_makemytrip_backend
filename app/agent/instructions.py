"""Voice agent persona instructions."""

import json


def build_instructions(agent_name: str, user: dict | None) -> str:
    """Persona instructions, enriched with fetched user context when present."""
    base = (
        f"You are {agent_name}, a helpful voice assistant for SBI. "
        "Speak naturally and concisely. Answer in the user's language. "
        "When data is best shown visually (account summaries, transactions, "
        "charges, comparisons), call the show_details tool to display a table "
        "on screen instead of reading every value aloud."
    )
    if user:
        base += f"\n\nYou are speaking with a known customer. Their details:\n{json.dumps(user, ensure_ascii=False)}"
    else:
        base += "\n\nThe caller is not identified. Do not assume any account details."
    return base
