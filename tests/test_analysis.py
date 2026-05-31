import pytest

from app.analytics.analysis import analyze_account, generate_growth_insights
from app.database.connection import DB_PATH, get_connection


pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(),
    reason="Real database not found; run python tests/test_real_api.py first",
)


REQUIRED_TOP_LEVEL_KEYS = {
    "account_id",
    "account",
    "avg_engagement_rate",
    "top_performing_posts",
    "posting_frequency",
    "best_posting_day",
    "content_type_performance",
    "growth_insights",
}

REQUIRED_ACCOUNT_KEYS = {"username", "followers_count", "media_count"}


def _get_account_id() -> str | None:
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM accounts LIMIT 1").fetchone()
    return row["id"] if row else None


@pytest.fixture(scope="module")
def account_id() -> str:
    aid = _get_account_id()
    if not aid:
        pytest.skip("No account rows in database")
    return aid


@pytest.fixture(scope="module")
def analysis(account_id: str) -> dict:
    return analyze_account(account_id)


def test_analyze_account_structure(analysis: dict, account_id: str) -> None:
    assert REQUIRED_TOP_LEVEL_KEYS.issubset(analysis.keys())
    assert analysis["account_id"] == account_id

    account = analysis["account"]
    assert REQUIRED_ACCOUNT_KEYS.issubset(account.keys())
    assert account["username"]
    assert account["followers_count"] > 0
    assert account["media_count"] >= 0

    avg = analysis["avg_engagement_rate"]
    assert avg["account_id"] == account_id
    assert avg["post_count"] > 0
    assert "avg_engagement_rate" in avg

    assert 0 < len(analysis["top_performing_posts"]) <= 3
    top_rates = [p["engagement_rate"] for p in analysis["top_performing_posts"]]
    assert top_rates == sorted(top_rates, reverse=True)

    frequency = analysis["posting_frequency"]
    assert frequency["account_id"] == account_id
    assert frequency["posts_per_week"] > 0

    best_day = analysis["best_posting_day"]
    assert best_day["day"] is not None

    assert len(analysis["content_type_performance"]) > 0


def test_growth_insights_present(analysis: dict) -> None:
    insights = analysis["growth_insights"]
    assert isinstance(insights, list)
    assert len(insights) > 0
    assert all(isinstance(line, str) and line.strip() for line in insights)


def test_generate_growth_insights_matches_analyze(analysis: dict) -> None:
    regenerated = generate_growth_insights(analysis)
    assert regenerated == analysis["growth_insights"]


def test_generate_growth_insights_content(analysis: dict) -> None:
    insights = generate_growth_insights(analysis)
    combined = " ".join(insights).lower()

    assert "engagement" in combined
    assert "post" in combined
