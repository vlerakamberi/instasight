import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.analytics.monitoring import run_daily_monitoring, save_daily_snapshot
from app.analytics.trend_analysis import get_performance_trend, get_trend_summary

ACCOUNT_ID = "17841409576371357"

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "instasight.db"

pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(),
    reason="data/instasight.db not found; sync data before running these tests.",
)


# ---------------------------------------------------------------------------
# monitoring.py
# ---------------------------------------------------------------------------
def test_save_daily_snapshot_returns_dict():
    snapshot = save_daily_snapshot(ACCOUNT_ID)
    assert isinstance(snapshot, dict)
    for key in (
        "account_id",
        "snapshot_date",
        "followers_count",
        "avg_engagement_rate",
        "posts_this_week",
        "top_media_type",
    ):
        assert key in snapshot


def test_run_daily_monitoring_structure():
    result = run_daily_monitoring(ACCOUNT_ID)
    assert isinstance(result, dict)
    for key in ("account_id", "snapshot", "alerts", "alerts_count", "ran_at"):
        assert key in result


def test_alerts_is_list():
    result = run_daily_monitoring(ACCOUNT_ID)
    assert isinstance(result["alerts"], list)


# ---------------------------------------------------------------------------
# trend_analysis.py
# ---------------------------------------------------------------------------
def test_get_performance_trend_returns_list():
    trend = get_performance_trend(ACCOUNT_ID, days=30)
    assert isinstance(trend, list)


def test_get_trend_summary_has_data_key():
    summary = get_trend_summary(ACCOUNT_ID, days=30)
    assert isinstance(summary, dict)
    assert "has_data" in summary


def test_get_trend_summary_structure_when_data():
    summary = get_trend_summary(ACCOUNT_ID, days=30)
    if summary.get("has_data"):
        for key in (
            "engagement_start",
            "engagement_end",
            "followers_change",
            "trend_direction",
        ):
            assert key in summary
