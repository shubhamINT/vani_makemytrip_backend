# Backend agent contract — MakeMyTrip AI Travel Concierge

Hand this to the backend/agent developer. It defines everything the LiveKit agent
must provide so the frontend (this repo) works: the token endpoint, the room topics,
and the **openui-lang** the agent streams to render flights, hotels, tickets and trips.

The frontend renders with OpenUI's `openuiChatLibrary`, so the agent must emit **only
components from that library** (listed at the end). Every example below is
parser-validated against that library.

---

## 1. Token endpoint

The frontend calls `POST {VITE_TOKEN_ENDPOINT}`:

Request:
```json
{ "agent_name": "Vani-makemytrip", "id": "optional-user-id" }
```
- `agent_name` — room naming + persona. Frontend sends `VITE_AGENT_NAME` (currently `Vani-makemytrip`).
- `id` — optional user id; if set, load the traveler's context (past trips, preferences).

Response (envelope; flat `{token,url}` also accepted):
```json
{ "success": true, "message": "token created",
  "data": { "token": "eyJ...", "url": "wss://your-livekit-host", "room": "..." } }
```
- Mint the token **and dispatch the agent into the room** before responding.
- Return `502` if dispatch fails — the frontend shows a retry state.
- CORS: allow the site origin.

---

## 2. Room protocol

| Direction | Topic | Payload | Meaning |
|---|---|---|---|
| agent → user | audio track | — | spoken replies (agent greets first) |
| both | `lk.transcription` | reserved | live captions (LiveKit-managed, do not write) |
| user → agent | `lk.chat` | text | typed messages **and booking actions** (see §4) |
| agent → user | `ui.render` | raw openui-lang text | a result panel to display |

Rules:
- Greet first with a short spoken line.
- When data is better **shown** than spoken (search results, a confirmation, an
  itinerary), call your `render_ui` tool and stream the openui-lang on `ui.render`.
  Say a short line too ("Here are your options") so voice users look at the screen.
- **No persistence** — `ui.render`/transcripts are realtime only. Persist server-side.

---

## 3. openui-lang the agent emits

Line-oriented, assignment-based. `root` must be a `Card`. Positional args, one
statement per line. Below are the core travel patterns — copy the shapes.

### Hotel results (carousel of cards with images, tags, price, Book)
```text
root = Card([head, note, hotels, follow])
head = CardHeader("Modern Hotels in Paris", "Showing 3 stays")
note = TextContent("Design-forward hotels near the Champs-Élysées.")
hotels = Carousel([c1, c2, c3])
c1 = Card([img1, name1, tags1, price1, b1])
img1 = Image("Hotel Plaza Athénée", "https://example.com/plaza.jpg")
name1 = TextContent("Hotel Plaza Athénée", "default-heavy")
tags1 = TagBlock([Tag("Free Wifi", null, null, "success"), Tag("Spa", null, null, "info")])
price1 = TextContent("₹42,000 / night")
b1 = Button("Book", Action([@ToAssistant("Book Hotel Plaza Athénée")]), "primary")
c2 = Card([img2, name2, price2, b2])
img2 = Image("Four Seasons George V", "https://example.com/george.jpg")
name2 = TextContent("Four Seasons George V", "default-heavy")
price2 = TextContent("₹58,000 / night")
b2 = Button("Book", Action([@ToAssistant("Book Four Seasons George V")]), "primary")
c3 = Card([img3, name3, price3, b3])
img3 = Image("Hotel Lutetia", "https://example.com/lutetia.jpg")
name3 = TextContent("Hotel Lutetia", "default-heavy")
price3 = TextContent("₹49,000 / night")
b3 = Button("Book", Action([@ToAssistant("Book Hotel Lutetia")]), "primary")
follow = FollowUpBlock([FollowUpItem("Cheaper options"), FollowUpItem("Near the Eiffel Tower")])
```

### Flight results (table + book buttons)
```text
root = Card([head, flights, book])
head = CardHeader("Delhi → Goa", "Fri, 18 Jul · 42 flights")
flights = Table([Col("Airline", ["IndiGo", "Vistara", "Air India"]), Col("Depart", ["06:10", "09:25", "13:40"]), Col("Duration", ["2h 25m", "2h 30m", "2h 20m"]), Col("Fare", ["₹4,199", "₹5,850", "₹6,100"], "number")])
book = Buttons([Button("Book IndiGo 06:10", Action([@ToAssistant("Book IndiGo flight Delhi to Goa at 06:10")]), "primary"), Button("More times", Action([@ToAssistant("Show more flight times")]), "secondary")])
```

### Booking confirmation / ticket (callout + details + e-ticket link)
```text
root = Card([head, alert, details, actions])
head = CardHeader("Booking confirmed", "PNR ABX7Q2")
alert = Callout("success", "You're going to Goa!", "IndiGo 6E-231 · Fri 18 Jul · 06:10")
details = ListBlock([ListItem("Seat 14A · Window"), ListItem("Terminal 1, Gate to be announced"), ListItem("Total paid: ₹4,199")])
actions = Buttons([Button("View e-ticket", Action([@OpenUrl("https://example.com/ticket/ABX7Q2")]), "primary"), Button("Add to calendar", Action([@ToAssistant("Add my Goa flight to calendar")]), "secondary")])
```

### Trip itinerary (steps)
```text
root = Card([head, plan])
head = CardHeader("3 days in Bali", "Budget-friendly")
plan = Steps([StepsItem("Day 1 — Seminyak", "Beach clubs, sunset at Tanah Lot"), StepsItem("Day 2 — Ubud", "Rice terraces, Monkey Forest, temples"), StepsItem("Day 3 — Nusa Penida", "Kelingking Beach day trip")])
```

---

## 4. Booking round-trip — how actions come back

Buttons carry an `Action(...)`. When the user clicks one, the frontend does:

- `@OpenUrl("...")` → opens the URL in a new tab (use for e-tickets, receipts, payment pages).
- `@ToAssistant("...")` → sends that text back to the agent **on `lk.chat`** as a normal
  user message.

So a "Book" button becomes an incoming chat message like `"Book Hotel Plaza Athénée"`.
The agent must handle these strings: confirm details, run the booking tool, then stream a
**confirmation `ui.render`** (the ticket pattern above). Write action strings to be
self-sufficient — include enough to identify the item (name, flight number, time), since
they arrive with no extra structured payload.

Payment/checkout that must happen in-browser → send the user to a URL with `@OpenUrl`.

---

## 5. Allowed components (openuiChatLibrary)

Emit only these. Argument order matters (positional). Verify new shapes with the parser
before shipping (`createParser(openuiChatLibrary.toJSONSchema(), "Card").parse(src)`,
check `result.meta.errors`).

```
Card, CardHeader, TextContent, MarkDownRenderer, Callout, TextCallout,
Image, ImageBlock, ImageGallery, Carousel, Separator,
Table, Col, ListBlock, ListItem, TagBlock, Tag, SectionBlock, SectionItem,
Steps, StepsItem, FollowUpBlock, FollowUpItem, Tabs, TabItem, Accordion, AccordionItem,
Buttons, Button, Form, FormControl, Input, TextArea, Select, SelectItem,
DatePicker, Slider, CheckBoxGroup, CheckBoxItem, RadioGroup, RadioItem, SwitchGroup, SwitchItem, Label,
BarChart, LineChart, AreaChart, PieChart, RadarChart, RadialChart, ScatterChart,
HorizontalBarChart, SingleStackedBarChart, Series, Point, ScatterSeries, Slice, CodeBlock
```

Key signatures to watch (source of the mistakes above):
- `Image(alt, src)` — **alt is first**.
- `Tag(text, icon, size, variant)` — variant is 4th; pass `null` for skipped middle args.
- `CardHeader(title, subtitle)`, `Button(label, action, variant, type, size)`.
- `Carousel(children, variant)` — children are components (nest `Card`s for hotel/flight cards).
- Actions: `@ToAssistant(message)`, `@OpenUrl(url)`, wrapped in `Action([...])`.
```
