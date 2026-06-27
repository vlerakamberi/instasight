from datetime import datetime
from typing import Any, Dict, List

from app.analytics.analysis import analyze_account
from app.database.connection import get_connection
from app.utils_logger import setup_logger


logger = setup_logger("monitoring")

ENGAGEMENT_DROP_THRESHOLD = 20.0
ENGAGEMENT_SPIKE_THRESHOLD = 30.0


def _best_content_type(analysis: Dict[str, Any]) -> str | None:
    """Pick the media type with the highest average engagement."""
    patterns = analysis.get("patterns")
    if patterns and patterns.get("best_content_type"):
        return patterns["best_content_type"]

    content_types = analysis.get("content_type_performance", [])
    if not content_types:
        return None
    ranked = sorted(
        content_types,
        key=lambda item: item.get("avg_engagement_rate", 0.0),
        reverse=True,
    )
    return ranked[0].get("media_type")


def save_daily_snapshot(account_id: str) -> Dict[str, Any]:
    """
    Capture today's performance metrics into performance_snapshots.
    """
    analysis = analyze_account(account_id)
    account = analysis["account"]

    followers_count = int(account["followers_count"] or 0)
    avg_engagement_rate = float(
        analysis["avg_engagement_rate"]["avg_engagement_rate"] or 0.0
    )
    posts_count = int(account["media_count"] or 0)
    top_media_type = _best_content_type(analysis)

    with get_connection() as conn:
        posts_this_week = int(
            conn.execute(
                """
                SELECT COUNT(*) AS c
                FROM posts
                WHERE account_id = ?
                  AND timestamp >= datetime('now', '-7 days')
                """,
                (account_id,),
            ).fetchone()["c"]
            or 0
        )

        snapshot_date = conn.execute("SELECT date('now') AS d").fetchone()["d"]

        conn.execute(
            """
            INSERT OR REPLACE INTO performance_snapshots (
                account_id,
                snapshot_date,
                followers_count,
                avg_engagement_rate,
                posts_count,
                posts_this_week,
                top_media_type
            )
            VALUES (?, date('now'), ?, ?, ?, ?, ?)
            """,
            (
                account_id,
                followers_count,
                avg_engagement_rate,
                posts_count,
                posts_this_week,
                top_media_type,
            ),
        )
        conn.commit()

    snapshot = {
        "account_id": account_id,
        "snapshot_date": snapshot_date,
        "followers_count": followers_count,
        "avg_engagement_rate": avg_engagement_rate,
        "posts_count": posts_count,
        "posts_this_week": posts_this_week,
        "top_media_type": top_media_type,
    }

    logger.info(
        "Snapshot saved for %s on %s (engagement=%.2f%%, posts_this_week=%s)",
        account_id,
        snapshot_date,
        avg_engagement_rate,
        posts_this_week,
    )
    return snapshot


def check_and_generate_alerts(account_id: str) -> List[Dict[str, Any]]:
    """
    Compare the two latest snapshots and emit alerts on significant changes.
    """
    alerts: List[Dict[str, Any]] = []

    with get_connection() as conn:
        snapshots = conn.execute(
            """
            SELECT snapshot_date, avg_engagement_rate
            FROM performance_snapshots
            WHERE account_id = ?
            ORDER BY snapshot_date DESC
            LIMIT 2
            """,
            (account_id,),
        ).fetchall()

        if len(snapshots) < 2:
            logger.info(
                "Not enough snapshots for %s (%s found); skipping alerts.",
                account_id,
                len(snapshots),
            )
            return []

        current = float(snapshots[0]["avg_engagement_rate"] or 0.0)
        previous = float(snapshots[1]["avg_engagement_rate"] or 0.0)

        pending: List[tuple[str, str]] = []

        # ALERT TYPE 1 — engagement_drop
        if previous > 0 and (previous - current) / previous * 100 > ENGAGEMENT_DROP_THRESHOLD:
            change = (previous - current) / previous * 100
            pending.append(
                (
                    "engagement_drop",
                    f"Engagement rate dropped from {previous}% to {current}% "
                    f"({change:.1f}% decrease) compared to yesterday.",
                )
            )

        # ALERT TYPE 2 — posting_inactivity
        posts_last_week = int(
            conn.execute(
                """
                SELECT COUNT(*) AS c
                FROM posts
                WHERE account_id = ?
                  AND timestamp >= datetime('now', '-7 days')
                """,
                (account_id,),
            ).fetchone()["c"]
            or 0
        )
        if posts_last_week == 0:
            pending.append(
                (
                    "posting_inactivity",
                    "No posts in the last 7 days. "
                    "Instagram algorithm penalizes inactive accounts.",
                )
            )

        # ALERT TYPE 3 — engagement_spike
        if previous > 0 and (current - previous) / previous * 100 > ENGAGEMENT_SPIKE_THRESHOLD:
            change = (current - previous) / previous * 100
            pending.append(
                (
                    "engagement_spike",
                    f"Engagement rate jumped from {previous}% to {current}% "
                    f"({change:.1f}% increase). Analyze what worked.",
                )
            )

        for alert_type, message in pending:
            conn.execute(
                """
                INSERT INTO alerts (
                    account_id, alert_type, message,
                    metric_value, metric_previous, email_sent
                )
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (account_id, alert_type, message, current, previous),
            )
            logger.warning("Alert [%s] for %s: %s", alert_type, account_id, message)
            alerts.append(
                {
                    "account_id": account_id,
                    "alert_type": alert_type,
                    "message": message,
                    "metric_value": current,
                    "metric_previous": previous,
                }
            )

        conn.commit()

    return alerts


def run_daily_monitoring(account_id: str) -> Dict[str, Any]:
    """
    Scheduler entry point: snapshot today's metrics and raise any alerts.
    """
    logger.info("Starting daily monitoring for account_id=%s", account_id)

    snapshot = save_daily_snapshot(account_id)
    alerts = check_and_generate_alerts(account_id)

    logger.info("Monitoring complete: %s alerts generated", len(alerts))

    return {
        "account_id": account_id,
        "snapshot": snapshot,
        "alerts": alerts,
        "alerts_count": len(alerts),
        "ran_at": datetime.now().isoformat(),
    }
