from typing import Any, Dict, List

from app.database.connection import get_connection
from app.utils_logger import setup_logger


logger = setup_logger("trend_analysis")


def get_performance_trend(account_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """
    Return performance snapshots for the last `days`, oldest first.
    """
    days = int(days)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT snapshot_date, followers_count, avg_engagement_rate,
                   posts_this_week, top_media_type
            FROM performance_snapshots
            WHERE account_id = ?
              AND snapshot_date >= date('now', '-{days} days')
            ORDER BY snapshot_date ASC
            """,
            (account_id,),
        ).fetchall()

    snapshots = [
        {
            "snapshot_date": row["snapshot_date"],
            "followers_count": row["followers_count"],
            "avg_engagement_rate": row["avg_engagement_rate"],
            "posts_this_week": row["posts_this_week"],
            "top_media_type": row["top_media_type"],
        }
        for row in rows
    ]

    logger.info(
        "get_performance_trend(%s, days=%s) returned %s snapshots",
        account_id,
        days,
        len(snapshots),
    )
    return snapshots


def get_trend_summary(account_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Summarize the change in performance metrics over the last `days`.
    """
    snapshots = get_performance_trend(account_id, days)

    if len(snapshots) < 2:
        return {
            "has_data": False,
            "message": "Not enough data yet. "
            "Run monitoring daily to build trend history.",
        }

    first = snapshots[0]
    last = snapshots[-1]

    engagement_start = first["avg_engagement_rate"] or 0.0
    engagement_end = last["avg_engagement_rate"] or 0.0
    engagement_change = engagement_end - engagement_start
    engagement_change_pct = (
        engagement_change / engagement_start * 100 if engagement_start > 0 else 0
    )

    followers_change = last["followers_count"] - first["followers_count"]
    avg_posts_per_week = sum(s["posts_this_week"] or 0 for s in snapshots) / len(snapshots)

    if engagement_change > 0:
        trend_direction = "up"
    elif engagement_change < 0:
        trend_direction = "down"
    else:
        trend_direction = "stable"

    return {
        "has_data": True,
        "days_tracked": days,
        "snapshots_count": len(snapshots),
        "first_date": first["snapshot_date"],
        "last_date": last["snapshot_date"],
        "engagement_start": engagement_start,
        "engagement_end": engagement_end,
        "engagement_change": round(engagement_change, 2),
        "engagement_change_pct": round(engagement_change_pct, 1),
        "followers_start": first["followers_count"],
        "followers_end": last["followers_count"],
        "followers_change": followers_change,
        "avg_posts_per_week": round(avg_posts_per_week, 2),
        "trend_direction": trend_direction,
    }
