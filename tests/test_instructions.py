"""Run: uv run python -m tests.test_instructions"""

from app.agent.instructions import build_instructions


def test_build_instructions():
    with_user = build_instructions("Support", {"name": "Asha", "acct": "x123"})
    without = build_instructions("Support", None)
    assert "Asha" in with_user and "known customer" in with_user
    assert "not identified" in without and "Asha" not in without


if __name__ == "__main__":
    test_build_instructions()
    print("ok")
