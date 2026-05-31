import sys

import pytest

from app.ai.strategy_generator import generate_strategy
from app.database.connection import DB_PATH


pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(),
    reason="Real database not found; run python tests/test_real_api.py first",
)

ACCOUNT_ID = "17841409576371357"


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass


def test_generate_strategy_returns_non_empty_strategy() -> None:
    result = generate_strategy(ACCOUNT_ID)

    assert result["account_id"] == ACCOUNT_ID
    assert result["username"]
    assert isinstance(result["strategy"], str)
    assert len(result["strategy"].strip()) > 0
    assert isinstance(result["generated_at"], str)
    assert "T" in result["generated_at"]

    _configure_stdout()
    print("\n" + "=" * 60)
    print(f"Strategy for @{result['username']} (account_id={result['account_id']})")
    print(f"Generated at: {result['generated_at']}")
    print("=" * 60)
    print(result["strategy"])
    print("=" * 60 + "\n")
