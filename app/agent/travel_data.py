"""Curated demo travel data for the typed-JSON UI topics.

Produces dicts matching the frontend contract in
`makemytrip_frontend/src/lib/streamTypes.ts` (`TripHero`, `HotelsList`,
`FlightsList`). Hotels/flights/hero render via the frontend's native
components, so the agent must send this typed JSON — not OpenUI-Lang.

# ponytail: curated demo data (no travel API in the repo). Swap the bodies of
# hotels_for / flights_for / hero_for for a real search API when one exists;
# the return shapes are the frontend contract and must not change.
"""

import re

# Known-good hotel photos for the showcase city (Kolkata). Real, HTTPS,
# hotlinkable. Unknown cities fall back to Picsum (always resolves).
_KOLKATA = {
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
        {
            "id": "taj-bengal",
            "name": "Taj Bengal",
            "image": {
                "src": "https://cf.bstatic.com/xdata/images/hotel/max1024x768/528067594.jpg?k=aaacb3bf5a62eadded59f90083a40ef39103e3f9cc7fb72acc425d0de07ae1f7&o=",
                "alt": "Taj Bengal",
            },
            "badge": "Popular",
            "rating": 4.7,
            "reviews": 2312,
            "location": "Alipore, Kolkata",
            "amenities": ["Breakfast incl.", "Free cancellation"],
            "price": "₹8,900",
            "priceUnit": "/ night",
        },
        {
            "id": "itc-royal-bengal",
            "name": "ITC Royal Bengal",
            "image": {
                "src": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSmnZfK4KI09VeTieeItIKRVko46gOsgO-S5gvzsa6fcSkVP_fWRdIa0PcU&s=10",
                "alt": "ITC Royal Bengal",
            },
            "rating": 4.6,
            "reviews": 1985,
            "location": "New Town, Kolkata",
            "amenities": ["Breakfast incl.", "Free cancellation"],
            "price": "₹6,200",
            "priceUnit": "/ night",
        },
        {
            "id": "abhiray-grand",
            "name": "Abhiray Grand Hotel",
            "image": {
                "src": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ3yse4VQSJUw6pZkiABjbLGba0LMpxXjb4ZZxkH47F0wXDERTJbZoQeTA&s=10",
                "alt": "Abhiray Grand Hotel",
            },
            "rating": 4.6,
            "reviews": 1248,
            "location": "New Market, Kolkata",
            "amenities": ["Breakfast incl.", "Free cancellation"],
            "price": "₹4,200",
            "priceUnit": "/ night",
        },
    ],
}

# Airport code guesses for the flight fallback / Kolkata route.
_CODES = {"delhi": "DEL", "kolkata": "CCU", "mumbai": "BOM", "goa": "GOI", "bengaluru": "BLR", "chennai": "MAA"}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.strip().lower()).strip("-") or "city"


def _code(city: str) -> str:
    return _CODES.get(city.strip().lower(), city.strip()[:3].upper())


def _picsum(seed: str, w: int = 640, h: int = 480) -> str:
    return f"https://picsum.photos/seed/{_slug(seed)}/{w}/{h}"


def hero_for(destination: str) -> dict:
    """TripHero JSON for the overview hero + related chips + weather."""
    if destination.strip().lower() == "kolkata":
        return dict(_KOLKATA["hero"])
    return {
        "destination": destination,
        "image": {"src": _picsum(f"{destination}-hero", 1600, 600), "alt": destination},
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
    if destination.strip().lower() == "kolkata":
        hotels = [
            {**h, "action": f"Show me rooms at {h['name']}, {h['location']}"}
            for h in _KOLKATA["hotels"]
        ]
        return {"title": "Top Hotels for You", "destination": "Kolkata", "viewAllAction": view_all, "hotels": hotels}

    # Generic fallback: three plausible stays with resolving images.
    tiers = [
        ("Grand", 4.6, 1820, "₹6,500", "Popular"),
        ("Regency", 4.5, 1340, "₹4,800", None),
        ("Comfort Inn", 4.3, 960, "₹3,200", None),
    ]
    hotels = []
    for suffix, rating, reviews, price, badge in tiers:
        name = f"{destination} {suffix}"
        h = {
            "id": _slug(name),
            "name": name,
            "image": {"src": _picsum(name), "alt": name},
            "rating": rating,
            "reviews": reviews,
            "location": f"Central {destination}",
            "amenities": ["Breakfast incl.", "Free cancellation"],
            "price": price,
            "priceUnit": "/ night",
            "action": f"Show me rooms at {name}, {destination}",
        }
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
        f = {
            "id": _slug(no),
            "airline": airline,
            "flightNo": no,
            "depart": {"time": dep, "code": o},
            "arrive": {"time": arr, "code": d},
            "duration": dur,
            "stops": "Non-stop",
            "price": price,
            "action": f"Book {airline} {no}, {origin} to {destination}, departing {dep}{when}",
        }
        if tag:
            f["tag"] = tag
        flights.append(f)
    return {
        "title": "Recommended Flights",
        "viewAllAction": f"Show me all flights from {origin} to {destination}{when}",
        "flights": flights,
    }
