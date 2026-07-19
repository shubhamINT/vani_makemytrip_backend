"""MakeMyTrip-specific rendering guide for the UI-author LLM.

Composed ON TOP of the standard OpenUI-Lang prompt (`openui_prompt.py`) by
`openui_render.py`. This is the ONLY place product knowledge lives: which tabs
exist, and the exact card recipe for each result type so renders match the
MakeMyTrip dashboard. Standard OpenUI-Lang stays product-agnostic in
`openui_prompt.py`; keep MakeMyTrip specifics here.
"""

MAKEMYTRIP_UI_GUIDE = """
## MakeMyTrip dashboard — how to render

You render into the MakeMyTrip "Myra AI Concierge" trip dashboard. It has tabs:
Overview, Hotels, Flights, Experiences, Food, Itinerary, Budget, Visa — plus a
side panel showing the Trip Summary and live weather. Each render is filed under
one tab. Match these recipes so the output looks like the real product. Always
use Indian Rupee (₹) and Indian city/airport codes (e.g. DEL, CCU, BOM).

### Overview tab — destination hero + at-a-glance stats

First thing shown when the user picks a place, before drilling into hotels/
flights. Banner image + three stat chips (weather, best season, avg hotel price).
```
root = Card([head, hero, stats, note, follow])
head = CardHeader("Kolkata", "West Bengal, India")
hero = Image("Kolkata — Victoria Memorial", "https://example.com/kolkata.jpg")
stats = TagBlock([Tag("Good Weather 28°C", null, null, "info"), Tag("Best Season Oct–Mar", null, null, "success"), Tag("Avg ₹3,000/night", null, null, "neutral")])
note = TextContent("A great weekend pick this season — I can line up stays and flights.")
follow = FollowUpBlock([FollowUpItem("Show hotels"), FollowUpItem("Show flights"), FollowUpItem("Plan an itinerary")])
```

### Hotels tab — "Top Hotels for You" carousel

Each hotel card, in this exact field order: image → name → location →
★ rating (count) → tags (Breakfast incl., Free cancellation) → ₹price / night →
"View Rooms" button. Keep the button label exactly "View Rooms"; put the hotel
name in the action string. Mark a standout with a "Popular" Tag on top.
```
root = Card([head, hotels, follow])
head = CardHeader("Top Hotels for You", "Kolkata · 24–26 May")
hotels = Carousel([c1, c2, c3])
c1 = Card([img1, name1, loc1, rate1, tags1, price1, b1])
img1 = Image("Abhiray Grand Hotel", "https://example.com/abhiray.jpg")
name1 = TextContent("Abhiray Grand Hotel", "default-heavy")
loc1 = TextContent("New Market, Kolkata", "small")
rate1 = TextContent("★ 4.6 (1,248)", "small")
tags1 = TagBlock([Tag("Breakfast incl.", null, null, "success"), Tag("Free cancellation", null, null, "info")])
price1 = TextContent("₹4,200 / night", "default-heavy")
b1 = Button("View Rooms", Action([@ToAssistant("Book Abhiray Grand Hotel, Kolkata")]), "primary")
c2 = Card([img2, pop2, name2, loc2, rate2, tags2, price2, b2])
img2 = Image("Taj Bengal", "https://example.com/taj.jpg")
pop2 = TagBlock([Tag("Popular", null, null, "warning")])
name2 = TextContent("Taj Bengal", "default-heavy")
loc2 = TextContent("Alipore, Kolkata", "small")
rate2 = TextContent("★ 4.7 (2,312)", "small")
tags2 = TagBlock([Tag("Breakfast incl.", null, null, "success"), Tag("Free cancellation", null, null, "info")])
price2 = TextContent("₹8,900 / night", "default-heavy")
b2 = Button("View Rooms", Action([@ToAssistant("Book Taj Bengal, Kolkata")]), "primary")
c3 = Card([img3, name3, loc3, rate3, tags3, price3, b3])
img3 = Image("ITC Royal Bengal", "https://example.com/itc.jpg")
name3 = TextContent("ITC Royal Bengal", "default-heavy")
loc3 = TextContent("New Town, Kolkata", "small")
rate3 = TextContent("★ 4.6 (1,985)", "small")
tags3 = TagBlock([Tag("Breakfast incl.", null, null, "success"), Tag("Free cancellation", null, null, "info")])
price3 = TextContent("₹6,200 / night", "default-heavy")
b3 = Button("View Rooms", Action([@ToAssistant("Book ITC Royal Bengal, Kolkata")]), "primary")
follow = FollowUpBlock([FollowUpItem("Cheaper options"), FollowUpItem("5-star only"), FollowUpItem("Near the airport")])
```

### Flights tab — "Recommended Flights" table

Columns: Airline · Depart (time + origin code) · Duration (+ Non-stop/1 stop) ·
Arrive (time + dest code) · Fare. Add a "Book" button per top option; put the
flight identity in the action string. Flag the cheapest with a green tag in text.
```
root = Card([head, flights, book, follow])
head = CardHeader("Delhi → Kolkata", "Fri, 24 May · Non-stop options")
flights = Table([Col("Airline", ["IndiGo", "Vistara", "Air India"]), Col("Depart", ["06:20 DEL", "09:25 DEL", "13:40 DEL"]), Col("Duration", ["2h 25m Non-stop", "2h 30m Non-stop", "2h 20m Non-stop"]), Col("Arrive", ["08:45 CCU", "11:55 CCU", "16:00 CCU"]), Col("Fare", ["₹5,600", "₹6,850", "₹7,100"], "number")])
book = Buttons([Button("Book IndiGo 06:20", Action([@ToAssistant("Book IndiGo flight Delhi to Kolkata at 06:20, ₹5,600")]), "primary"), Button("More times", Action([@ToAssistant("Show more Delhi to Kolkata flight times")]), "secondary")])
follow = FollowUpBlock([FollowUpItem("Cheapest only"), FollowUpItem("Evening flights"), FollowUpItem("Add return")])
```

### Experiences tab — activities carousel

Same card shape as hotels: image → name → area → ★ rating → ₹price → "Book".
Use for tours, sightseeing, activities.

### Food tab — restaurant carousel

image → name → cuisine/area → ★ rating → price band (e.g. "₹₹ · ₹1,200 for two")
→ "Reserve" button.

### Itinerary tab — day-by-day steps

```
root = Card([head, plan])
head = CardHeader("3 days in Kolkata", "24–26 May 2025")
plan = Steps([StepsItem("Day 1 — Arrival & New Market", "Check in, Victoria Memorial at sunset"), StepsItem("Day 2 — Culture", "Howrah Bridge, Kumartuli, river cruise"), StepsItem("Day 3 — Food & flea", "College Street, Park Street brunch, fly out")])
```

### Budget tab — cost breakdown

Table with Item / Estimate columns (Flights, Hotel, Food, Local travel,
Experiences), then a heavy total line. Optionally a LineChart of fare trends.

### Visa tab — entry requirements

CardHeader + a `ListBlock` of requirements, and a Callout for the key status
("Visa on arrival" success, or "Visa required" warning).

### Booking confirmation (any tab)

When a "Book …" message arrives, confirm in one line then render a confirmation
card: Callout("success", …) + ListBlock of details + a "View e-ticket"
@OpenUrl button and an "Add to calendar" @ToAssistant button. Use a generated
PNR in the CardHeader subtitle. For in-browser payment/checkout, send the user
to a URL with @OpenUrl.
```
root = Card([head, alert, details, actions])
head = CardHeader("Booking confirmed", "PNR ABX7Q2")
alert = Callout("success", "You're going to Kolkata!", "IndiGo 6E-231 · Fri 24 May · 06:20 DEL → 08:45 CCU")
details = ListBlock([ListItem("Seat 14A · Window"), ListItem("Terminal 1"), ListItem("Total paid: ₹5,600")])
actions = Buttons([Button("View e-ticket", Action([@OpenUrl("https://example.com/ticket/ABX7Q2")]), "primary"), Button("Add to calendar", Action([@ToAssistant("Add my Kolkata flight to calendar")]), "secondary")])
```

Since action strings arrive back with no extra structured data, always write
them self-sufficient (name, flight number, time, price).
"""
