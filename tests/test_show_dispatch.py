"""Run: uv run python -m tests.test_show_dispatch

Guards the `show` dispatch registry: every registry key must be an allowed
`kind` literal on the tool, and every kind must produce a non-empty payload for
a curated city. Does not touch LiveKit — tests the registry + data fns only.
"""

import typing

from app.agent import travel_data as td
from app.agent.openui_build import budget_lang, itinerary_lang, visa_lang
from app.agent.worker import _SHOW, TravelAgent


def _kind_literals() -> set[str]:
    hints = typing.get_type_hints(TravelAgent.show.__wrapped__, include_extras=False)
    return set(typing.get_args(hints["kind"]))


def test_registry_matches_signature():
    assert set(_SHOW) == _kind_literals()


def test_data_fns_non_empty_for_curated_city():
    d = "Kolkata"
    assert td.hero_for(d)["destination"]
    assert td.hotels_for(d)["hotels"]
    assert td.experiences_for(d)["hotels"]
    assert td.food_for(d)["hotels"]
    assert itinerary_lang(td.itinerary_for(d)).startswith("root = Card(")
    assert budget_lang(d, td.budget_for(d)).startswith("root = Card(")
    assert visa_lang(d, td.visa_for(d)).startswith("root = Card(")


def test_hotel_images_come_from_pool():
    # Curated and off-script cities must both use real pool URLs (no loremflickr).
    for city in ("Kolkata", "Atlantis"):
        for h in td.hotels_for(city)["hotels"]:
            assert h["image"]["src"] in td._POOL, (city, h["image"]["src"])


if __name__ == "__main__":
    test_registry_matches_signature()
    test_data_fns_non_empty_for_curated_city()
    test_hotel_images_come_from_pool()
    print("ok")
