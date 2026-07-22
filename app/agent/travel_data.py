"""Curated demo travel data for the trip dashboard.

Two render paths consume this:
- Native typed-JSON topics (hero / hotels / flights) — dicts here match the
  frontend contract in makemytrip_frontend/src/lib/streamTypes.ts.
- Deterministic openui-lang (experiences / food / itinerary / budget / visa /
  booking) — app/agent/openui_build.py turns the dicts here into openui-lang.

Coverage: Kolkata (deep) + Goa + Jaipur backups; anything else falls back to
generated-but-resolving data so an off-script city still looks fine.

# ponytail: curated demo data (no travel API in the repo). Swap the *_for()
# bodies for a real search API when one exists; the return shapes are the
# frontend / openui_build contract and must not change.

Images: all cards/hotels/heroes pull from the shared `_POOL` of real HTTPS URLs,
rotating deterministically by index so they don't flicker between renders. Add
URLs to `_POOL` to widen the rotation.
"""

import re

_CODES = {
    "delhi": "DEL", "kolkata": "CCU", "mumbai": "BOM", "goa": "GOI",
    "jaipur": "JAI", "bengaluru": "BLR", "chennai": "MAA", "hyderabad": "HYD",
}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.strip().lower()).strip("-") or "city"


def _code(city: str) -> str:
    return _CODES.get(city.strip().lower(), city.strip()[:3].upper())


def _flickr(keywords: str, lock: int, w: int = 640, h: int = 480) -> str:
    """Deterministic photo from the shared pool, stable per lock number.

    # ponytail: keywords/size ignored — loremflickr didn't render reliably, so
    # every call now maps to a real pool URL (rotates by lock). Kept the name +
    # signature so existing call sites don't change.
    """
    return _pool(lock)


# Shared pool of real photos (user-supplied), used interchangeably across cards,
# detail galleries and hero banners. Deterministic assignment by index so the
# same item always gets the same photo.
_POOL = [
    "https://www.cvent.com/sites/default/files/image/2021-01/iStock-537361842-2.jpg",
    "https://cf.bstatic.com/xdata/images/hotel/max1024x768/528067594.jpg?k=aaacb3bf5a62eadded59f90083a40ef39103e3f9cc7fb72acc425d0de07ae1f7&o=",
    "https://assets.architecturaldigest.in/photos/69ba8a4abedec0d050a54777/16:9/w_1616,h_909,c_limit/Untitled%20design%20-%202026-03-18T163237.899.jpg",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSmnZfK4KI09VeTieeItIKRVko46gOsgO-S5gvzsa6fcSkVP_fWRdIa0PcU&s=10",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ3yse4VQSJUw6pZkiABjbLGba0LMpxXjb4ZZxkH47F0wXDERTJbZoQeTA&s=10",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSu9LVQLESflmRTl9YLRHt9R9cV4h3wjHKQhEvqyu5iBrmopG0VpXzcKOWc&s=10",
    "https://cf-images.assettype.com/TNIE%2Fimport%2Fuploads%2Fuser%2Fckeditor_images%2Farticle%2F2020%2F2%2F20%2Fdfdjjj1.jpg?w=640&auto=format%2Ccompress",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSWf65AYMvbslSvkltg83jTzkKAux65lDS5vZd0GqR3-68oBG7GI4s_N9sZ&s=10",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSowal-UKOZ8lZW_qZApp6kyUeeAPuJeOCU8CbpM2nir9c_m2g57_gV77r5&s=10",
    "https://q-xx.bstatic.com/xdata/images/hotel/max500/777471072.jpg?k=139efcb0249b5bd3a81e414d8b6ee5b23b26eccb3531ed48a0b6f7df82fa631d&o=",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQa9Vm0VxqcIA9Fys2eJCEIxViWkT4V0SUSWiPcNpDKuQ&s=10",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQzYO7HtdwPegcSdrfAuEkPWunTenB7dgyb-ft68QNdCZvfBVrqfGD0Rxk&s=10",
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSOSSNDfBvRvW3CgVQcV4xzjNnrjpL2Ey-GKxlu33g5sW4Jzg4xCoDpeho&s=10",
    "https://www.subahotels.com/Images/slider/13_50_2024_06_50_19suba_palace_banner_5.jpg",
]


def _pool(i: int) -> str:
    return _POOL[i % len(_POOL)]


def _gallery(start: int, n: int = 4) -> list[str]:
    """n distinct pool photos starting at `start` (wraps)."""
    return [_pool(start + k) for k in range(n)]


# ── Curated cities ──────────────────────────────────────────────────────────
# Each city: hero, hotels, experiences, food, itinerary, budget, visa.
# Flights are generated generically (good enough, realistic) from the route.

_CITIES: dict[str, dict] = {
    "kolkata": {
        "hero": {
            "destination": "Kolkata",
            "region": "West Bengal, India",
            "image": {
                "src": "https://assets.architecturaldigest.in/photos/69ba8a4abedec0d050a54777/16:9/w_1616,h_909,c_limit/Untitled%20design%20-%202026-03-18T163237.899.jpg",
                "alt": "Kolkata skyline",
            },
            "stats": [
                {"icon": "sun", "label": "Good Weather", "value": "28°C"},
                {"icon": "calendar", "label": "Best Season", "value": "Oct – Mar"},
                {"icon": "tag", "label": "Avg. Hotel Price", "value": "₹3,000 / night"},
            ],
            "related": ["Best time to visit Kolkata", "3-day Kolkata itinerary"],
        },
        "hotels": [
            {"id": "taj-bengal", "name": "Taj Bengal", "badge": "Popular",
             "image": {"src": "https://cf.bstatic.com/xdata/images/hotel/max1024x768/528067594.jpg?k=aaacb3bf5a62eadded59f90083a40ef39103e3f9cc7fb72acc425d0de07ae1f7&o=", "alt": "Taj Bengal"},
             "rating": 4.7, "reviews": 2312, "location": "Alipore, Kolkata",
             "amenities": ["Breakfast incl.", "Free cancellation", "Pool"],
             "price": "₹8,900", "priceUnit": "/ night"},
            {"id": "itc-royal-bengal", "name": "ITC Royal Bengal",
             "image": {"src": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSmnZfK4KI09VeTieeItIKRVko46gOsgO-S5gvzsa6fcSkVP_fWRdIa0PcU&s=10", "alt": "ITC Royal Bengal"},
             "rating": 4.6, "reviews": 1985, "location": "New Town, Kolkata",
             "amenities": ["Breakfast incl.", "Free cancellation", "Spa"],
             "price": "₹6,200", "priceUnit": "/ night"},
            {"id": "abhiray-grand", "name": "Abhiray Grand Hotel",
             "image": {"src": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ3yse4VQSJUw6pZkiABjbLGba0LMpxXjb4ZZxkH47F0wXDERTJbZoQeTA&s=10", "alt": "Abhiray Grand Hotel"},
             "rating": 4.6, "reviews": 1248, "location": "New Market, Kolkata",
             "amenities": ["Breakfast incl.", "Free cancellation"],
             "price": "₹4,200", "priceUnit": "/ night"},
        ],
        "experiences": [
            {"name": "Victoria Memorial Tour", "area": "Maidan", "rating": 4.7, "price": "₹500", "kw": "kolkata,victoriamemorial", "lock": 11},
            {"name": "Howrah Bridge & Flower Market Walk", "area": "Mullick Ghat", "rating": 4.6, "price": "₹800", "kw": "kolkata,howrahbridge", "lock": 12},
            {"name": "Kalighat Temple Visit", "area": "Kalighat", "rating": 4.5, "price": "₹300", "kw": "kolkata,temple", "lock": 13},
            {"name": "Hooghly River Sunset Cruise", "area": "Millennium Park", "rating": 4.8, "price": "₹1,200", "kw": "kolkata,rivercruise", "lock": 14},
            {"name": "Kumartuli Potters' Quarter", "area": "Kumartuli", "rating": 4.6, "price": "₹600", "kw": "kolkata,pottery", "lock": 15},
        ],
        "food": [
            {"name": "Peter Cat", "cuisine": "Continental · Chelo Kebab", "area": "Park Street", "rating": 4.5, "priceBand": "₹₹ · ₹1,200 for two", "kw": "kebab,restaurant", "lock": 21},
            {"name": "6 Ballygunge Place", "cuisine": "Bengali Thali", "area": "Ballygunge", "rating": 4.6, "priceBand": "₹₹ · ₹1,500 for two", "kw": "bengali,thali", "lock": 22},
            {"name": "Flurys", "cuisine": "Café · Bakery", "area": "Park Street", "rating": 4.4, "priceBand": "₹₹ · ₹900 for two", "kw": "cafe,bakery", "lock": 23},
            {"name": "Oh! Calcutta", "cuisine": "Bengali Fine-dining", "area": "Elgin", "rating": 4.5, "priceBand": "₹₹₹ · ₹2,000 for two", "kw": "finedining,curry", "lock": 24},
        ],
        "itinerary": {
            "title": "3 Days in Kolkata", "subtitle": "24 – 26 May 2025",
            "days": [
                {"title": "Day 1 — Arrival & New Market", "detail": "Check in, Victoria Memorial at sunset, dinner on Park Street"},
                {"title": "Day 2 — Culture", "detail": "Howrah Bridge, Kumartuli, Hooghly river cruise, College Street"},
                {"title": "Day 3 — Food & Flea", "detail": "Kalighat, South City brunch, last-minute shopping, fly out"},
            ],
        },
        "budget": {
            "rows": [
                {"item": "Flights (2 pax)", "estimate": "₹11,200"},
                {"item": "Hotel (2 nights)", "estimate": "₹12,400"},
                {"item": "Food", "estimate": "₹4,500"},
                {"item": "Local travel", "estimate": "₹2,000"},
                {"item": "Experiences", "estimate": "₹3,400"},
            ],
            "total": "₹33,500",
            "fareTrend": {"labels": ["8w", "6w", "4w", "2w", "Now"], "values": [4900, 5100, 5400, 5600, 6100]},
        },
        "visa": {"status": "none", "note": "Domestic trip — no visa required.",
                 "requirements": ["Valid government photo ID (Aadhaar / Passport / Driving licence)", "Ticket & hotel confirmation", "Carry ID for hotel check-in"]},
    },
    "goa": {
        "hero": {
            "destination": "Goa", "region": "India",
            "image": {"src": _flickr("goa,beach", 31, 1600, 600), "alt": "Goa beach"},
            "stats": [
                {"icon": "sun", "label": "Beach Weather", "value": "31°C"},
                {"icon": "calendar", "label": "Best Season", "value": "Nov – Feb"},
                {"icon": "tag", "label": "Avg. Hotel Price", "value": "₹5,500 / night"},
            ],
            "related": ["North vs South Goa", "3-day Goa itinerary"],
        },
        "hotels": [
            {"id": "taj-fort-aguada", "name": "Taj Fort Aguada Resort", "badge": "Popular",
             "image": {"src": _flickr("goa,resort", 41), "alt": "Taj Fort Aguada"},
             "rating": 4.7, "reviews": 3120, "location": "Sinquerim, North Goa",
             "amenities": ["Beachfront", "Breakfast incl.", "Pool"], "price": "₹14,500", "priceUnit": "/ night"},
            {"id": "w-goa", "name": "W Goa",
             "image": {"src": _flickr("goa,luxuryhotel", 42), "alt": "W Goa"},
             "rating": 4.6, "reviews": 2010, "location": "Vagator, North Goa",
             "amenities": ["Beachfront", "Free cancellation", "Spa"], "price": "₹18,900", "priceUnit": "/ night"},
            {"id": "the-leela-goa", "name": "The Leela Goa",
             "image": {"src": _flickr("goa,beachresort", 43), "alt": "The Leela Goa"},
             "rating": 4.7, "reviews": 2540, "location": "Mobor, South Goa",
             "amenities": ["Breakfast incl.", "Golf", "Pool"], "price": "₹16,200", "priceUnit": "/ night"},
        ],
        "experiences": [
            {"name": "Dudhsagar Falls Trip", "area": "Mollem", "rating": 4.7, "price": "₹2,500", "kw": "waterfall,jungle", "lock": 51},
            {"name": "Old Goa Churches Tour", "area": "Old Goa", "rating": 4.6, "price": "₹700", "kw": "goa,church", "lock": 52},
            {"name": "Spice Plantation Visit", "area": "Ponda", "rating": 4.5, "price": "₹900", "kw": "spice,plantation", "lock": 53},
            {"name": "Sunset Cruise on the Mandovi", "area": "Panaji", "rating": 4.8, "price": "₹1,500", "kw": "goa,cruise", "lock": 54},
            {"name": "Scuba at Grande Island", "area": "Grande Island", "rating": 4.7, "price": "₹3,500", "kw": "scuba,diving", "lock": 55},
        ],
        "food": [
            {"name": "Fisherman's Wharf", "cuisine": "Goan Seafood", "area": "Cavelossim", "rating": 4.5, "priceBand": "₹₹ · ₹1,600 for two", "kw": "seafood,restaurant", "lock": 61},
            {"name": "Gunpowder", "cuisine": "South Indian", "area": "Assagao", "rating": 4.6, "priceBand": "₹₹ · ₹1,400 for two", "kw": "southindian,food", "lock": 62},
            {"name": "Thalassa", "cuisine": "Greek", "area": "Vagator", "rating": 4.5, "priceBand": "₹₹₹ · ₹2,200 for two", "kw": "greek,restaurant", "lock": 63},
            {"name": "Britto's", "cuisine": "Goan · Beach shack", "area": "Baga", "rating": 4.3, "priceBand": "₹₹ · ₹1,300 for two", "kw": "beach,shack", "lock": 64},
        ],
        "itinerary": {
            "title": "3 Days in Goa", "subtitle": "Beaches + heritage",
            "days": [
                {"title": "Day 1 — North Goa", "detail": "Baga & Calangute, Fort Aguada, beach-shack dinner"},
                {"title": "Day 2 — Heritage", "detail": "Old Goa churches, spice plantation, Mandovi sunset cruise"},
                {"title": "Day 3 — South Goa", "detail": "Palolem beach, Dudhsagar detour, fly out"},
            ],
        },
        "budget": {
            "rows": [
                {"item": "Flights (2 pax)", "estimate": "₹13,800"},
                {"item": "Hotel (2 nights)", "estimate": "₹29,000"},
                {"item": "Food", "estimate": "₹6,000"},
                {"item": "Local travel", "estimate": "₹3,500"},
                {"item": "Experiences", "estimate": "₹7,000"},
            ],
            "total": "₹59,300",
            "fareTrend": {"labels": ["8w", "6w", "4w", "2w", "Now"], "values": [6200, 6400, 6600, 6800, 6900]},
        },
        "visa": {"status": "none", "note": "Domestic trip — no visa required.",
                 "requirements": ["Valid government photo ID", "Ticket & hotel confirmation"]},
    },
    "jaipur": {
        "hero": {
            "destination": "Jaipur", "region": "Rajasthan, India",
            "image": {"src": _flickr("jaipur,palace", 32, 1600, 600), "alt": "Jaipur palace"},
            "stats": [
                {"icon": "sun", "label": "Weather", "value": "33°C"},
                {"icon": "calendar", "label": "Best Season", "value": "Oct – Mar"},
                {"icon": "tag", "label": "Avg. Hotel Price", "value": "₹4,500 / night"},
            ],
            "related": ["Jaipur forts guide", "3-day Jaipur itinerary"],
        },
        "hotels": [
            {"id": "rambagh-palace", "name": "Rambagh Palace", "badge": "Popular",
             "image": {"src": _flickr("jaipur,palacehotel", 44), "alt": "Rambagh Palace"},
             "rating": 4.8, "reviews": 4100, "location": "Bhawani Singh Rd, Jaipur",
             "amenities": ["Heritage", "Breakfast incl.", "Spa"], "price": "₹35,000", "priceUnit": "/ night"},
            {"id": "itc-rajputana", "name": "ITC Rajputana",
             "image": {"src": _flickr("jaipur,hotel", 45), "alt": "ITC Rajputana"},
             "rating": 4.5, "reviews": 2260, "location": "Palace Road, Jaipur",
             "amenities": ["Breakfast incl.", "Pool", "Free cancellation"], "price": "₹7,800", "priceUnit": "/ night"},
            {"id": "fairmont-jaipur", "name": "Fairmont Jaipur",
             "image": {"src": _flickr("jaipur,luxuryhotel", 46), "alt": "Fairmont Jaipur"},
             "rating": 4.6, "reviews": 3050, "location": "Kukas, Jaipur",
             "amenities": ["Spa", "Pool", "Breakfast incl."], "price": "₹9,500", "priceUnit": "/ night"},
        ],
        "experiences": [
            {"name": "Amber Fort & Elephant Ride", "area": "Amer", "rating": 4.7, "price": "₹1,200", "kw": "jaipur,amberfort", "lock": 71},
            {"name": "City Palace Tour", "area": "Old City", "rating": 4.6, "price": "₹700", "kw": "jaipur,citypalace", "lock": 72},
            {"name": "Hawa Mahal Photo Walk", "area": "Badi Chaupar", "rating": 4.5, "price": "₹500", "kw": "jaipur,hawamahal", "lock": 73},
            {"name": "Nahargarh Sunset Point", "area": "Nahargarh", "rating": 4.8, "price": "₹600", "kw": "jaipur,fort", "lock": 74},
            {"name": "Chokhi Dhani Cultural Village", "area": "Tonk Road", "rating": 4.4, "price": "₹1,100", "kw": "rajasthan,culture", "lock": 75},
        ],
        "food": [
            {"name": "LMB (Laxmi Misthan Bhandar)", "cuisine": "Rajasthani · Sweets", "area": "Johari Bazaar", "rating": 4.4, "priceBand": "₹₹ · ₹800 for two", "kw": "indiansweets,thali", "lock": 81},
            {"name": "Spice Court", "cuisine": "Rajasthani", "area": "Civil Lines", "rating": 4.5, "priceBand": "₹₹ · ₹1,300 for two", "kw": "rajasthani,food", "lock": 82},
            {"name": "Handi", "cuisine": "North Indian", "area": "MI Road", "rating": 4.5, "priceBand": "₹₹ · ₹1,200 for two", "kw": "northindian,curry", "lock": 83},
            {"name": "Chokhi Dhani", "cuisine": "Rajasthani Thali", "area": "Tonk Road", "rating": 4.4, "priceBand": "₹₹₹ · ₹2,000 for two", "kw": "rajasthani,thali", "lock": 84},
        ],
        "itinerary": {
            "title": "3 Days in Jaipur", "subtitle": "The Pink City",
            "days": [
                {"title": "Day 1 — Old City", "detail": "City Palace, Hawa Mahal, Johari Bazaar, LMB dinner"},
                {"title": "Day 2 — Forts", "detail": "Amber Fort, Jaigarh, Nahargarh sunset"},
                {"title": "Day 3 — Culture", "detail": "Albert Hall, Chokhi Dhani, fly out"},
            ],
        },
        "budget": {
            "rows": [
                {"item": "Flights (2 pax)", "estimate": "₹9,600"},
                {"item": "Hotel (2 nights)", "estimate": "₹15,600"},
                {"item": "Food", "estimate": "₹4,000"},
                {"item": "Local travel", "estimate": "₹2,500"},
                {"item": "Experiences", "estimate": "₹4,600"},
            ],
            "total": "₹36,300",
            "fareTrend": {"labels": ["8w", "6w", "4w", "2w", "Now"], "values": [4200, 4400, 4600, 4700, 4800]},
        },
        "visa": {"status": "none", "note": "Domestic trip — no visa required.",
                 "requirements": ["Valid government photo ID", "Ticket & hotel confirmation"]},
    },
}


def _city(destination: str) -> dict | None:
    return _CITIES.get(destination.strip().lower())


# ── Native typed-JSON (hero / hotels / flights) ─────────────────────────────

def hero_for(destination: str) -> dict:
    """TripHero JSON: overview hero + stat chips + related + weather driver."""
    c = _city(destination)
    if c:
        return dict(c["hero"])
    return {
        "destination": destination,
        "image": {"src": _flickr(f"{destination},travel", 1, 1600, 600), "alt": destination},
        "stats": [
            {"icon": "sun", "label": "Weather", "value": "Pleasant"},
            {"icon": "calendar", "label": "Best Season", "value": "Oct – Mar"},
            {"icon": "tag", "label": "Avg. Hotel Price", "value": "₹3,500 / night"},
        ],
        "related": [f"Best time to visit {destination}", f"3-day {destination} itinerary"],
    }


def hotels_for(destination: str) -> dict:
    """HotelsList JSON for the native hotels carousel."""
    view_all = f"Show me all hotel options in {destination}"
    c = _city(destination)
    if c:
        hotels = [
            {**h, "image": {"src": _pool(i), "alt": h["name"]},
             "action": f"Book {h['name']}, {h['location']}"}
            for i, h in enumerate(c["hotels"])
        ]
        return {"title": "Top Hotels for You", "destination": c["hero"]["destination"],
                "viewAllAction": view_all, "hotels": hotels}
    tiers = [("Grand", 4.6, 1820, "₹6,500", "Popular"), ("Regency", 4.5, 1340, "₹4,800", None),
             ("Comfort Inn", 4.3, 960, "₹3,200", None)]
    hotels = []
    for i, (suffix, rating, reviews, price, badge) in enumerate(tiers):
        name = f"{destination} {suffix}"
        h = {"id": _slug(name), "name": name,
             "image": {"src": _pool(i), "alt": name},
             "rating": rating, "reviews": reviews, "location": f"Central {destination}",
             "amenities": ["Breakfast incl.", "Free cancellation"], "price": price,
             "priceUnit": "/ night", "action": f"Book {name}, {destination}"}
        if badge:
            h["badge"] = badge
        hotels.append(h)
    return {"title": "Top Hotels for You", "destination": destination, "viewAllAction": view_all, "hotels": hotels}


def flights_for(origin: str, destination: str, date: str | None = None) -> dict:
    """FlightsList JSON for the native flights list."""
    o, d = _code(origin), _code(destination)
    when = f" on {date}" if date else ""
    rows = [
        ("IndiGo", "6E 2041", "06:20", "08:45", "2h 25m", "₹5,600", "Lowest fare"),
        ("Air India", "AI 763", "10:15", "12:50", "2h 35m", "₹6,150", None),
        ("Vistara", "UK 729", "18:40", "21:10", "2h 30m", "₹7,300", None),
    ]
    flights = []
    for airline, no, dep, arr, dur, price, tag in rows:
        f = {"id": _slug(no), "airline": airline, "flightNo": no,
             "depart": {"time": dep, "code": o}, "arrive": {"time": arr, "code": d},
             "duration": dur, "stops": "Non-stop", "price": price,
             "action": f"Book {airline} {no}, {origin} to {destination}, departing {dep}{when}, {price}"}
        if tag:
            f["tag"] = tag
        flights.append(f)
    return {"title": "Recommended Flights",
            "viewAllAction": f"Show me all flights from {origin} to {destination}{when}",
            "flights": flights}


# ── Common card lists (same HotelsList shape → native HotelCard) ─────────────
# Experiences and restaurants reuse the hotel card component on the frontend, so
# they emit the same {title, items:[Hotel-shaped]} payload. `cta` sets the button
# label; `action` opens the detail view via show_details.

def experiences_for(destination: str) -> dict:
    """HotelsList-shaped: activities rendered by the common card carousel."""
    c = _city(destination)
    raw = c["experiences"] if c else [
        {"name": f"{destination} City Highlights", "area": destination, "rating": 4.6, "price": "₹900"},
        {"name": f"{destination} Food Walk", "area": destination, "rating": 4.5, "price": "₹1,100"},
        {"name": f"{destination} Heritage Tour", "area": destination, "rating": 4.7, "price": "₹1,300"},
    ]
    items = []
    for i, x in enumerate(raw):
        items.append({
            "id": _slug(x["name"]), "name": x["name"], "location": x["area"],
            "rating": x["rating"], "reviews": 400 + i * 130,
            "image": {"src": _pool(i), "alt": x["name"]},
            "amenities": ["Guided", "Instant confirm"],
            "price": x["price"], "priceUnit": "/ person",
            "cta": "View details", "action": f"Show details of {x['name']}",
        })
    return {"title": f"Things to do in {destination}", "destination": destination, "hotels": items}


def food_for(destination: str) -> dict:
    """HotelsList-shaped: restaurants rendered by the common card carousel."""
    c = _city(destination)
    raw = c["food"] if c else [
        {"name": f"{destination} Kitchen", "cuisine": "Local", "area": destination, "rating": 4.5, "priceBand": "₹₹ · ₹1,200 for two"},
        {"name": f"The {destination} Café", "cuisine": "Café", "area": destination, "rating": 4.4, "priceBand": "₹₹ · ₹900 for two"},
    ]
    items = []
    for i, x in enumerate(raw):
        items.append({
            "id": _slug(x["name"]), "name": x["name"], "location": x["area"],
            "rating": x["rating"], "reviews": 300 + i * 90,
            "image": {"src": _pool(i + 4), "alt": x["name"]},
            "amenities": [x["cuisine"]],
            "price": x["priceBand"], "priceUnit": "",
            "cta": "View details", "action": f"Show details of {x['name']}",
        })
    return {"title": f"Where to eat in {destination}", "destination": destination, "hotels": items}


def _find_item(name: str) -> tuple[dict, str] | None:
    """Locate a curated hotel/experience/restaurant by name → (item, category)."""
    key = name.strip().lower()
    for c in _CITIES.values():
        for cat in ("hotels", "experiences", "food"):
            for x in c.get(cat, []):
                if x["name"].strip().lower() in key or key in x["name"].strip().lower():
                    return x, cat
    return None


def details_for(name: str) -> dict:
    """DetailView payload: title, subtitle, images gallery, description, facts, actions."""
    found = _find_item(name)
    seed = abs(hash(name)) % len(_POOL)
    if found:
        x, cat = found
        area = x.get("area") or x.get("location", "")
        rating = x.get("rating")
        price = x.get("price") or x.get("priceBand", "")
        facts = [{"label": "Area", "value": area}]
        if rating:
            facts.append({"label": "Rating", "value": f"★ {rating}"})
        if cat == "food":
            facts.append({"label": "Cuisine", "value": x.get("cuisine", "")})
        facts.append({"label": "Price", "value": price})
        book = {"hotels": "Book", "experiences": "Book now", "food": "Reserve a table"}[cat]
        desc = {
            "hotels": f"{x['name']} in {area}. Comfortable stay with {', '.join(x.get('amenities', [])) or 'great amenities'}.",
            "experiences": f"{x['name']} — a popular thing to do in {area}. Guided, with instant confirmation.",
            "food": f"{x['name']} in {area}. {x.get('cuisine', 'Great food')} — a local favourite.",
        }[cat]
        return {
            "title": x["name"], "subtitle": area,
            "images": _gallery(seed, 5),
            "description": desc, "facts": facts,
            "actions": [
                {"label": book, "action": f"Book {x['name']}, {area}", "variant": "primary"},
                {"label": "Back to results", "action": f"Show me options in {area or name}", "variant": "secondary"},
            ],
        }
    # Unknown item → generic but still rich.
    return {
        "title": name, "subtitle": "",
        "images": _gallery(seed, 5),
        "description": f"Here are more details about {name}.",
        "facts": [{"label": "Availability", "value": "Available"}],
        "actions": [{"label": "Book", "action": f"Book {name}", "variant": "primary"}],
    }


def itinerary_for(destination: str) -> dict:
    """{title, subtitle, days:[{title, detail}]}."""
    c = _city(destination)
    if c:
        return dict(c["itinerary"])
    return {"title": f"3 Days in {destination}", "subtitle": "Suggested plan", "days": [
        {"title": "Day 1 — Arrival", "detail": f"Check in and explore central {destination}"},
        {"title": "Day 2 — Highlights", "detail": "Top sights, local food, evening at leisure"},
        {"title": "Day 3 — Wrap up", "detail": "Last-minute shopping, depart"},
    ]}


def budget_for(destination: str) -> dict:
    """{rows:[{item, estimate}], total, fareTrend:{labels, values}}."""
    c = _city(destination)
    if c:
        return dict(c["budget"])
    return {"rows": [
        {"item": "Flights (2 pax)", "estimate": "₹11,000"},
        {"item": "Hotel (2 nights)", "estimate": "₹13,000"},
        {"item": "Food", "estimate": "₹4,500"},
        {"item": "Local travel", "estimate": "₹2,500"},
        {"item": "Experiences", "estimate": "₹3,500"},
    ], "total": "₹34,500", "fareTrend": {"labels": ["8w", "6w", "4w", "2w", "Now"], "values": [5000, 5200, 5400, 5500, 5600]}}


def visa_for(destination: str) -> dict:
    """{status, note, requirements[]}."""
    c = _city(destination)
    if c:
        return dict(c["visa"])
    # Unknown → assume domestic India for this demo.
    return {"status": "none", "note": "Domestic trip — no visa required.",
            "requirements": ["Valid government photo ID", "Ticket & hotel confirmation"]}
