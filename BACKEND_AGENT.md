# Backend agent contract — MakeMyTrip AI Travel Concierge

What the LiveKit agent must provide so this frontend works: token endpoint, room
topics, and the payload schema for each topic.

Rendering is hybrid:
- **Typed JSON topics** for structured data: `trip.hero`, `hotels.list`, `flights.list`, `trip.summary`, `booking.confirmation`.
- **openui-lang** (`ui.render`) for long-tail only: experiences, food, itinerary, budget, visa, charts, open-ended answers.

---

## 0. What feeds each UI area

These render automatically once the topic is sent. If not sent, the area stays absent.

| UI area | Fed by |
|---|---|
| Destination hero banner (Overview) | `trip.hero` |
| Trip Summary card (right rail) | `trip.summary` |
| Weather card (right rail) | client-side from `trip.summary.destination` (Open-Meteo) |
| Hotel results | `hotels.list` |
| Flight results | `flights.list` |
| Booking / e-ticket card | `booking.confirmation` |

---

## 1. Token endpoint

Frontend calls `POST {VITE_TOKEN_ENDPOINT}`.

Request:
```json
{ "agent_name": "Vani-makemytrip", "id": "optional-user-id" }
```
- `agent_name` — room naming + persona (frontend sends `VITE_AGENT_NAME`).
- `id` — optional user id; if set, load traveler context.

Response (envelope; flat `{token,url}` also accepted):
```json
{ "success": true, "message": "token created",
  "data": { "token": "eyJ...", "url": "wss://your-livekit-host", "room": "..." } }
```
- Mint token **and dispatch the agent into the room** before responding.
- Return `502` if dispatch fails.
- CORS: allow the site origin.

---

## 2. Room protocol

| Direction | Topic | Payload | Meaning |
|---|---|---|---|
| agent → user | audio track | — | spoken replies (greet first) |
| both | `lk.transcription` | reserved | live captions (LiveKit-managed, do not write) |
| user → agent | `lk.chat` | text | typed messages + button/action strings (§9) |
| agent → user | `trip.hero` | JSON | destination hero banner |
| agent → user | `hotels.list` | JSON | hotel results carousel |
| agent → user | `flights.list` | JSON | flight results list |
| agent → user | `trip.summary` | JSON | trip summary card (right rail) |
| agent → user | `booking.confirmation` | JSON | confirmed booking / e-ticket card |
| agent → user | `ui.render` | openui-lang text | long-tail content (see §10) |

- Each typed JSON topic is **one snapshot per stream** — frontend `readAll()` + parse. Re-send replaces the previous value.
- `ui.render` streams carry two attributes: `tab` (`overview / hotels / flights / experiences / food / itinerary / budget / visa`; untagged → overview) and `title` (heading shown above the render).
- Greet with a short spoken line. When data is better shown than spoken, send the topic **and** say a short line ("Here are your options").
- No persistence — topics/transcripts are realtime only. Persist server-side.

---

## 3. `trip.hero`

Sent once the destination is known.

```json
{
  "destination": "Kolkata",
  "region": "West Bengal, India",
  "image": { "src": "https://cdn…/kolkata-hero-1600x600.webp", "alt": "Victoria Memorial" },
  "stats": [
    { "icon": "sun",      "label": "Good Weather",     "value": "28°C" },
    { "icon": "calendar", "label": "Best Season",      "value": "Oct – Mar" },
    { "icon": "tag",      "label": "Avg. Hotel Price", "value": "₹3,000 / night" }
  ],
  "related": ["Best time to visit Kolkata", "3-day Kolkata itinerary"]
}
```
- `icon` enum: `sun | cloud | calendar | tag | wallet | thermometer | umbrella` (unknown → generic dot).
- `stats` ≤ 4; `related` ≤ 5 (clicking one sends it as a chat message).
- Image: 1600×600 WebP q75–80, ≤ 200 KB.

---

## 4. `hotels.list`

```json
{
  "title": "Top Hotels for You",
  "destination": "Kolkata",
  "viewAllAction": "Show me all hotel options in Kolkata for 24–26 May, 2 adults",
  "hotels": [{
    "id": "abhiray-grand",
    "name": "Abhiray Grand Hotel",
    "image": { "src": "https://cdn…/abhiray-640x480.webp", "alt": "Abhiray Grand exterior" },
    "badge": "Popular",
    "rating": 4.6,
    "reviews": 1248,
    "location": "New Market, Kolkata",
    "amenities": ["Breakfast incl.", "Free cancellation"],
    "price": "₹4,200",
    "priceUnit": "/ night",
    "action": "Show me rooms at Abhiray Grand Hotel, New Market, Kolkata for 24–26 May, 2 adults"
  }]
}
```
- `badge`, `rating`, `reviews`, `location`, `amenities` optional. `amenities` ≤ 3 shown.
- 3–8 hotels (Overview shows first 4, Hotels tab all).
- `action` → "View Rooms" button; `viewAllAction` → "View all" link. Both sent verbatim on `lk.chat`.
- Image: 640×480 WebP q75, ≤ 60 KB.

---

## 5. `flights.list`

```json
{
  "title": "Recommended Flights",
  "viewAllAction": "Show me all flights from Delhi to Kolkata on 24 May",
  "flights": [{
    "id": "6e-2041",
    "airline": "IndiGo",
    "logo": "https://cdn…/airlines/indigo-96.webp",
    "flightNo": "6E 2041",
    "depart": { "time": "06:20", "code": "DEL" },
    "arrive": { "time": "08:45", "code": "CCU" },
    "duration": "2h 25m",
    "stops": "Non-stop",
    "price": "₹5,600",
    "tag": "Lowest fare",
    "action": "Book IndiGo 6E 2041, Delhi to Kolkata, departing 06:20 on 24 May, 2 adults"
  }]
}
```
- `tag` optional → green badge. `logo` optional → airline-initials fallback.
- 2–6 rows (Overview shows first 3, Flights tab all).
- `action` → "Book" button, sent verbatim on `lk.chat`.
- Logo: 96×96 WebP/PNG/SVG, ≤ 10 KB.

---

## 6. `trip.summary`

```json
{
  "destination": "Kolkata",
  "dates": "24–26 May 2025",
  "duration": "2 nights / 3 days",
  "travelers": "2 adults",
  "budget": "₹28,000 – ₹32,000",
  "fullPlanAction": "Show me the full trip plan for Kolkata"
}
```
- All fields optional; present fields show their row.
- `destination` also seeds the Weather card — send as soon as known.
- `fullPlanAction` → "View Full Plan →" button (default `"Show me the full trip plan"`), sent verbatim on `lk.chat`.

---

## 7. `booking.confirmation`

Send after a booking succeeds.

```json
{
  "kind": "flight",
  "title": "Flight Booking Confirmation",
  "status": "Booking confirmed",
  "reference": "PNR ABC1234",
  "headline": "You're going to Delhi!",
  "subhead": "IndiGo 6E-620 · Kolkata to Delhi · 08:20 CCU → 09:45 DEL",
  "details": [
    { "label": "Seat", "value": "23A" },
    { "label": "Departure", "value": "08:20 from CCU" },
    { "label": "Arrival", "value": "09:45 at DEL" },
    { "label": "Passengers", "value": "2 Adults" }
  ],
  "actions": [
    { "label": "View e-ticket", "url": "https://.../eticket/ABC1234", "variant": "primary" },
    { "label": "Add to calendar", "action": "Add my Delhi flight to my calendar", "variant": "secondary" }
  ]
}
```
- `kind` — `flight | hotel | experience` (header icon; default flight).
- `title`, `status`, `reference`, `headline`, `subhead` optional but recommended. `status` shows a green check; `reference` shows as a mono chip (use `"PNR pending"` before issuance); `headline` + `subhead` show in a green highlight block.
- `details` — ordered label/value rows (numbered chips). ~3–6.
- `actions` (≤ 3) — each has either `url` (opens new tab) or `action` (sent verbatim on `lk.chat`); `variant` `primary` | `secondary`.
- Re-send to update in place (e.g. `"PNR pending"` then the real PNR).

---

## 8. Image requirements

HTTPS only, resolvable, meaningful `alt`. Prefer CDN resize params (`?w=640&q=75&fm=webp`).

| Asset | Aspect | Send (2x) | Format | Budget |
|---|---|---|---|---|
| Hero banner | ~8:3 | 1600×600 | WebP q75–80 | ≤ 200 KB |
| Hotel thumb | 4:3 | 640×480 | WebP q75 | ≤ 60 KB |
| Airline logo | 1:1 | 96×96 | WebP/PNG alpha (SVG ideal) | ≤ 10 KB |

`Cache-Control: public, max-age=31536000, immutable` recommended.

---

## 9. Button actions round-trip

Every card button's string comes back as a normal `lk.chat` message.
- Action with `url` → frontend opens URL in a new tab (e-tickets, receipts, payment).
- Action with `action` → sent to the agent on `lk.chat`.

A "Book" button arrives as e.g. `"Book IndiGo 6E 2041, …"`. Agent confirms, runs the
booking tool, then sends a `booking.confirmation` snapshot (§7). Write action strings
self-sufficient — include name + flight number + dates + pax, since no extra structured
payload accompanies them. In-browser checkout → use a `url` action.

---

## 10. openui-lang components (`ui.render` only)

For experiences, food, itinerary, budget, visa, charts, open-ended answers. Emit only
these; argument order is positional. Verify shapes with the parser before shipping
(`createParser(openuiChatLibrary.toJSONSchema(), "Card").parse(src)`, check `result.meta.errors`).

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

Signatures to watch:
- `Image(alt, src)` — alt first.
- `Tag(text, icon, size, variant)` — variant 4th; pass `null` for skipped middle args.
- `CardHeader(title, subtitle)`, `Button(label, action, variant, type, size)`.
- `Carousel(children, variant)` — children are components.
- Actions: `@ToAssistant(message)`, `@OpenUrl(url)`, wrapped in `Action([...])`.
