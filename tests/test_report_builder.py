import pytest

from app.analytics.report_builder import build_prompt_context, build_report
from app.database.connection import DB_PATH, get_connection


pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(),
    reason="Real database not found; run python tests/test_real_api.py first",
)


REQUIRED_REPORT_KEYS = {
    "account_id",
    "account_summary",
    "top_posts",
    "posting_timeline",
    "media_type_breakdown",
    "patterns",
    "growth_insights",
    "generated_at",
}

REQUIRED_SUMMARY_KEYS = {
    "username",
    "followers",
    "total_posts",
    "avg_engagement_rate",
}

REQUIRED_PATTERN_KEYS = {
    "best_day",
    "posts_per_week",
    "best_content_type",
}


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
def report(account_id: str) -> dict:
    return build_report(account_id)


def test_build_report_structure(report: dict) -> None:
    assert REQUIRED_REPORT_KEYS.issubset(report.keys())

    summary = report["account_summary"]
    assert REQUIRED_SUMMARY_KEYS.issubset(summary.keys())
    assert summary["username"]
    assert summary["followers"] > 0
    assert summary["total_posts"] >= 0
    assert summary["avg_engagement_rate"] >= 0

    assert isinstance(report["top_posts"], list)
    assert 0 < len(report["top_posts"]) <= 3
    for post in report["top_posts"]:
        assert "caption" in post
        assert "media_type" in post
        assert "engagement_rate" in post
        assert "likes_count" in post
        assert "comments_count" in post

    assert isinstance(report["posting_timeline"], list)
    assert len(report["posting_timeline"]) > 0
    assert isinstance(report["media_type_breakdown"], list)
    assert len(report["media_type_breakdown"]) > 0

    patterns = report["patterns"]
    assert REQUIRED_PATTERN_KEYS.issubset(patterns.keys())
    assert patterns["best_day"]
    assert patterns["posts_per_week"] > 0
    assert patterns["best_content_type"]

    assert isinstance(report["growth_insights"], list)
    assert len(report["growth_insights"]) > 0
    assert all(isinstance(item, str) for item in report["growth_insights"])

    assert isinstance(report["generated_at"], str)
    assert "T" in report["generated_at"]


def test_build_prompt_context_non_empty(report: dict) -> None:
    context = build_prompt_context(report)

    assert isinstance(context, str)
    assert len(context.strip()) > 0
    assert report["account_summary"]["username"] in context
    assert f"@{report['account_summary']['username']}" in context
    assert "Top 3 posts by engagement rate:" in context
    assert "Likes:" in context
    assert "Posting timeline" in context
    assert "Media type breakdown" in context
    assert "REAL INSTAGRAM DATA" in context
