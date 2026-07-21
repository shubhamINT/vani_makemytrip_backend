"""Deterministic openui-lang builders for the non-native dashboard tabs.

Covers experiences, food, itinerary, budget, visa. (Hotels/flights/hero/booking
are typed-JSON native components, not openui-lang — see travel_data.py and the
booking.confirmation payload in worker.py.)

Turns curated dicts from `travel_data.py` into valid `openuiChatLibrary`
openui-lang (root = Card), streamed on `ui.render`. Deterministic — no LLM — so
the demo renders identically every run with real images. Shapes mirror the
parser-validated recipes in `makemytrip_ui.py`.

Panel heading comes from the `CardHeader` here; the tool streams these with an
empty `title` stream-attribute so the frontend `OpenUIEmbed` shows no extra
`<h2>` (avoids the doubled-header bug).

Run self-check: `.venv/bin/python -m app.agent.openui_build`
"""


def _esc(s: str) -> str:
    """Escape a string for an openui-lang double-quoted literal."""
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def _q(s: str) -> str:
    return f'"{_esc(s)}"'


def _lines(stmts: list[str]) -> str:
    return "\n".join(stmts) + "\n"


def itinerary_lang(data: dict) -> str:
    """CardHeader + Steps."""
    steps = []
    for i, d in enumerate(data["days"]):
        s = f"s{i}"
        steps.append(s)
    step_defs = [f"s{i} = StepsItem({_q(d['title'])}, {_q(d['detail'])})" for i, d in enumerate(data["days"])]
    stmts = [
        "root = Card([head, plan])",
        f"head = CardHeader({_q(data['title'])}, {_q(data.get('subtitle', ''))})",
        f"plan = Steps([{', '.join(steps)}])",
        *step_defs,
    ]
    return _lines(stmts)


def budget_lang(destination: str, data: dict) -> str:
    """CardHeader + Table(Item/Estimate) + heavy total + LineChart fare trend."""
    items = [r["item"] for r in data["rows"]]
    ests = [r["estimate"] for r in data["rows"]]
    items_arr = "[" + ", ".join(_q(x) for x in items) + "]"
    ests_arr = "[" + ", ".join(_q(x) for x in ests) + "]"
    labels = "[" + ", ".join(_q(x) for x in data["fareTrend"]["labels"]) + "]"
    values = "[" + ", ".join(str(int(v)) for v in data["fareTrend"]["values"]) + "]"
    stmts = [
        "root = Card([head, table, total, trend])",
        f"head = CardHeader({_q('Budget for ' + destination)}, \"Estimated for 2 travelers\")",
        f"table = Table([Col(\"Item\", {items_arr}), Col(\"Estimate\", {ests_arr})])",
        f"total = TextContent({_q('Total: ' + data['total'])}, \"large-heavy\")",
        f"trend = LineChart({labels}, [fare], \"natural\", \"When booked\", \"Fare (₹)\")",
        f"fare = Series(\"Lowest fare\", {values})",
    ]
    return _lines(stmts)


def visa_lang(destination: str, data: dict) -> str:
    """CardHeader + Callout + ListBlock of requirements."""
    variant = {"none": "success", "on-arrival": "info", "required": "warning"}.get(data["status"], "neutral")
    title = {"none": "No visa required", "on-arrival": "Visa on arrival", "required": "Visa required"}.get(data["status"], "Entry info")
    reqs = ", ".join(f"ListItem({_q(r)})" for r in data["requirements"])
    stmts = [
        "root = Card([head, alert, reqs])",
        f"head = CardHeader({_q('Entry requirements — ' + destination)})",
        f"alert = Callout({_q(variant)}, {_q(title)}, {_q(data['note'])})",
        f"reqs = ListBlock([{reqs}])",
    ]
    return _lines(stmts)


if __name__ == "__main__":
    from app.agent import travel_data as td

    builders = [
        itinerary_lang(td.itinerary_for("Kolkata")),
        budget_lang("Kolkata", td.budget_for("Kolkata")),
        visa_lang("Kolkata", td.visa_for("Kolkata")),
    ]
    for i, lang in enumerate(builders):
        assert lang.startswith("root = Card("), f"builder {i} bad root"
        assert "example.com" not in lang, f"builder {i} has placeholder url"
        assert lang.count("\n") >= 3
    print("openui_build ok —", len(builders), "builders")
