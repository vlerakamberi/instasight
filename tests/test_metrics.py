import pytest

from app.analytics.metrics import (
    avg_engagement_rate,
    best_posting_day,
    content_type_performance,
    engagement_rate,
    posting_frequency,
    top_performing_posts,
)
from app.database.connection import DB_PATH, get_connection


pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(),
    reason="Real database not found; run python tests/test_real_api.py first",
)


def _get_account_id() -> str | None:
    with get_connection() as conn:
        row = conn.execute("SELECT id FROM accounts LIMIT 1").fetchone()
    return row["id"] if row else None


def _get_post_id(account_id: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM posts WHERE account_id = ? LIMIT 1",
            (account_id,),
        ).fetchone()
    return row["id"] if row else None


@pytest.fixture(scope="module")
def account_id() -> str:
    aid = _get_account_id()
    if not aid:
        pytest.skip("No account rows in database")
    return aid


@pytest.fixture(scope="module")
def post_id(account_id: str) -> str:
    pid = _get_post_id(account_id)
    if not pid:
        pytest.skip("No post rows in database")
    return pid


def test_engagement_rate(post_id: str, account_id: str) -> None:
    result = engagement_rate(post_id)

    assert result["post_id"] == post_id
    assert result["account_id"] == account_id
    assert result["followers_count"] > 0
    assert result["engagement_rate"] >= 0
    expected = (
        (result["likes_count"] + result["comments_count"])
        / result["followers_count"]
        * 100
    )
    assert result["engagement_rate"] == round(expected, 2)


def test_avg_engagement_rate(account_id: str) -> None:
    result = avg_engagement_rate(account_id)

    assert result["account_id"] == account_id
    assert result["followers_count"] > 0
    assert result["post_count"] > 0
    assert result["avg_engagement_rate"] >= 0


def test_top_performing_posts(account_id: str) -> None:
    result = top_performing_posts(account_id, limit=5)

    assert len(result) > 0
    assert len(result) <= 5
    rates = [item["engagement_rate"] for item in result]
    assert rates == sorted(rates, reverse=True)
    for item in result:
        assert item["followers_count"] > 0
        assert "post_id" in item


def test_posting_frequency(account_id: str) -> None:
    result = posting_frequency(account_id)

    assert result["account_id"] == account_id
    assert result["followers_count"] > 0
    assert result["post_count"] > 0
    assert result["posts_per_week"] > 0
    assert result["weeks_span"] > 0


def test_best_posting_day(account_id: str) -> None:
    result = best_posting_day(account_id)

    assert result["account_id"] == account_id
    assert result["followers_count"] > 0
    assert result["day"] is not None
    assert result["post_count"] > 0
    assert result["avg_engagement_rate"] >= 0


def test_content_type_performance(account_id: str) -> None:
    result = content_type_performance(account_id)

    assert len(result) > 0
    for item in result:
        assert item["media_type"]
        assert item["followers_count"] > 0
        assert item["post_count"] > 0
        assert item["avg_engagement_rate"] >= 0
