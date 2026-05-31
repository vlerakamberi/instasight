import sys

import pytest

from app.ai.weekly_planner import generate_weekly_plan
from app.database.connection import DB_PATH


pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(),
    reason="Real database not found; run python tests/test_real_api.py first",
)

ACCOUNT_ID = "17841409576371357"

DAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday")


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass


def test_generate_weekly_plan_returns_english_plan() -> None:
    result = generate_weekly_plan(ACCOUNT_ID)

    assert result["account_id"] == ACCOUNT_ID
    assert result["username"]
    assert isinstance(result["plan"], str)
    assert len(result["plan"].strip()) > 0
    assert isinstance(result["generated_at"], str)
    assert "T" in result["generated_at"]
    assert result["week_start"]
    assert result["week_end"]

    # Plan must reference English day names from the prompt structure.
    found_days = [day for day in DAY_NAMES if day in result["plan"]]
    assert found_days, f"No English day names found in plan. Got: {result['plan'][:200]}"

    _configure_stdout()
    print("\n" + "=" * 60)
    print(f"Weekly plan for @{result['username']} (account_id={result['account_id']})")
    print(f"Week: {result['week_start']} -> {result['week_end']}")
    print(f"Generated at: {result['generated_at']}")
    print(f"Day names found: {', '.join(found_days)}")
    print("=" * 60)
    print(result["plan"])
    print("=" * 60 + "\n")
