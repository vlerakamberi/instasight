from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.database.connection import get_connection
from app.utils_logger import setup_logger


logger = setup_logger("metrics")


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.strip()
    if normalized.endswith("+0000"):
        normalized = normalized[:-5] + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        logger.warning("Could not parse timestamp: %s", value)
        return None


def _compute_engagement_rate(
    likes_count: int, comments_count: int, followers_count: int
) -> float:
    if followers_count <= 0:
        return 0.0
    return (likes_count + comments_count) / followers_count * 100


def _get_followers_count(conn, account_id: str) -> int:
    row = conn.execute(
        "SELECT followers_count FROM accounts WHERE id = ?",
        (account_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Account not found: {account_id}")
    return int(row["followers_count"] or 0)


def _get_post_account_id(conn, post_id: str) -> str:
    row = conn.execute(
        "SELECT account_id FROM posts WHERE id = ?",
        (post_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"Post not found: {post_id}")
    return row["account_id"]


def _get_latest_insight(conn, post_id: str) -> Dict[str, int]:
    row = conn.execute(
        """
        SELECT likes_count, comments_count
        FROM insights
        WHERE post_id = ?
        ORDER BY synced_at DESC
        LIMIT 1
        """,
        (post_id,),
    ).fetchone()
    if row is None:
        return {"likes_count": 0, "comments_count": 0}
    return {
        "likes_count": int(row["likes_count"] or 0),
        "comments_count": int(row["comments_count"] or 0),
    }


def _load_account_posts_with_insights(conn, account_id: str) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            p.id AS post_id,
            p.caption,
            p.media_type,
            p.timestamp,
            i.likes_count,
            i.comments_count
        FROM posts p
        INNER JOIN insights i ON i.id = (
            SELECT id
            FROM insights
            WHERE post_id = p.id
            ORDER BY synced_at DESC
            LIMIT 1
        )
        WHERE p.account_id = ?
        """,
        (account_id,),
    ).fetchall()

    followers_count = _get_followers_count(conn, account_id)
    posts: List[Dict[str, Any]] = []
    for row in rows:
        likes_count = int(row["likes_count"] or 0)
        comments_count = int(row["comments_count"] or 0)
        engagement = _compute_engagement_rate(
            likes_count, comments_count, followers_count
        )
        posts.append(
            {
                "post_id": row["post_id"],
                "caption": row["caption"],
                "media_type": row["media_type"],
                "timestamp": row["timestamp"],
                "likes_count": likes_count,
                "comments_count": comments_count,
                "followers_count": followers_count,
                "engagement_rate": round(engagement, 2),
            }
        )
    return posts


def engagement_rate(post_id: str) -> Dict[str, Any]:
    with get_connection() as conn:
        account_id = _get_post_account_id(conn, post_id)
        followers_count = _get_followers_count(conn, account_id)
        insight = _get_latest_insight(conn, post_id)
        rate = _compute_engagement_rate(
            insight["likes_count"],
            insight["comments_count"],
            followers_count,
        )
        result = {
            "post_id": post_id,
            "account_id": account_id,
            "likes_count": insight["likes_count"],
            "comments_count": insight["comments_count"],
            "followers_count": followers_count,
            "engagement_rate": round(rate, 2),
        }

    logger.info("engagement_rate(%s) = %s%%", post_id, result["engagement_rate"])
    return result


def avg_engagement_rate(account_id: str) -> Dict[str, Any]:
    with get_connection() as conn:
        posts = _load_account_posts_with_insights(conn, account_id)
        followers_count = _get_followers_count(conn, account_id)

    if not posts:
        result = {
            "account_id": account_id,
            "followers_count": followers_count,
            "post_count": 0,
            "avg_engagement_rate": 0.0,
        }
    else:
        avg_rate = sum(p["engagement_rate"] for p in posts) / len(posts)
        result = {
            "account_id": account_id,
            "followers_count": followers_count,
            "post_count": len(posts),
            "avg_engagement_rate": round(avg_rate, 2),
        }

    logger.info(
        "avg_engagement_rate(%s) = %s%% (%s posts)",
        account_id,
        result["avg_engagement_rate"],
        result["post_count"],
    )
    return result


def top_performing_posts(account_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        posts = _load_account_posts_with_insights(conn, account_id)

    ranked = sorted(posts, key=lambda p: p["engagement_rate"], reverse=True)[:limit]
    result = [
        {
            "post_id": post["post_id"],
            "caption": post["caption"],
            "media_type": post["media_type"],
            "likes_count": post["likes_count"],
            "comments_count": post["comments_count"],
            "followers_count": post["followers_count"],
            "engagement_rate": post["engagement_rate"],
        }
        for post in ranked
    ]

    logger.info(
        "top_performing_posts(%s, limit=%s) returned %s posts",
        account_id,
        limit,
        len(result),
    )
    return result


def posting_frequency(account_id: str) -> Dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT timestamp
            FROM posts
            WHERE account_id = ? AND timestamp IS NOT NULL
            """,
            (account_id,),
        ).fetchall()
        followers_count = _get_followers_count(conn, account_id)

    timestamps = [
        parsed
        for row in rows
        if (parsed := _parse_timestamp(row["timestamp"])) is not None
    ]
    post_count = len(timestamps)

    if post_count == 0:
        result = {
            "account_id": account_id,
            "followers_count": followers_count,
            "post_count": 0,
            "weeks_span": 0.0,
            "posts_per_week": 0.0,
        }
    elif post_count == 1:
        result = {
            "account_id": account_id,
            "followers_count": followers_count,
            "post_count": 1,
            "weeks_span": 1.0,
            "posts_per_week": 1.0,
        }
    else:
        earliest = min(timestamps)
        latest = max(timestamps)
        days_span = max((latest - earliest).days, 1)
        weeks_span = max(days_span / 7, 1.0)
        posts_per_week = post_count / weeks_span
        result = {
            "account_id": account_id,
            "followers_count": followers_count,
            "post_count": post_count,
            "weeks_span": round(weeks_span, 2),
            "posts_per_week": round(posts_per_week, 2),
        }

    logger.info(
        "posting_frequency(%s) = %s posts/week over %s weeks",
        account_id,
        result["posts_per_week"],
        result["weeks_span"],
    )
    return result


def best_posting_day(account_id: str) -> Dict[str, Any]:
    with get_connection() as conn:
        posts = _load_account_posts_with_insights(conn, account_id)
        followers_count = _get_followers_count(conn, account_id)

    by_day: Dict[str, List[float]] = defaultdict(list)
    for post in posts:
        parsed = _parse_timestamp(post["timestamp"])
        if parsed is None:
            continue
        day_name = parsed.strftime("%A")
        by_day[day_name].append(post["engagement_rate"])

    if not by_day:
        result = {
            "account_id": account_id,
            "followers_count": followers_count,
            "day": None,
            "avg_engagement_rate": 0.0,
            "post_count": 0,
        }
    else:
        day_avgs = {
            day: sum(rates) / len(rates)
            for day, rates in by_day.items()
        }
        best_day = max(day_avgs, key=day_avgs.get)
        result = {
            "account_id": account_id,
            "followers_count": followers_count,
            "day": best_day,
            "avg_engagement_rate": round(day_avgs[best_day], 2),
            "post_count": len(by_day[best_day]),
        }

    logger.info(
        "best_posting_day(%s) = %s (avg %s%%)",
        account_id,
        result["day"],
        result["avg_engagement_rate"],
    )
    return result


def content_type_performance(account_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        posts = _load_account_posts_with_insights(conn, account_id)
        followers_count = _get_followers_count(conn, account_id)

    by_type: Dict[str, List[float]] = defaultdict(list)
    for post in posts:
        media_type = (post["media_type"] or "UNKNOWN").upper()
        by_type[media_type].append(post["engagement_rate"])

    result = [
        {
            "media_type": media_type,
            "followers_count": followers_count,
            "post_count": len(rates),
            "avg_engagement_rate": round(sum(rates) / len(rates), 2),
        }
        for media_type, rates in sorted(by_type.items())
    ]

    logger.info(
        "content_type_performance(%s) = %s media types",
        account_id,
        len(result),
    )
    return result
