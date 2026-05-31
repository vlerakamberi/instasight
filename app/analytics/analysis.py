from typing import Any, Dict, List, Optional

from app.analytics.metrics import (
    avg_engagement_rate,
    best_posting_day,
    content_type_performance,
    posting_frequency,
    top_performing_posts,
)
from app.database.connection import get_connection
from app.utils_logger import setup_logger


logger = setup_logger("analysis")


def _load_account_info(account_id: str) -> Dict[str, Any]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, username, followers_count, media_count, biography
            FROM accounts
            WHERE id = ?
            """,
            (account_id,),
        ).fetchone()

    if row is None:
        raise ValueError(f"Account not found: {account_id}")

    return {
        "account_id": row["id"],
        "username": row["username"],
        "followers_count": int(row["followers_count"] or 0),
        "media_count": int(row["media_count"] or 0),
        "biography": row["biography"] or "",
    }


def _caption_preview(caption: Optional[str], max_len: int = 60) -> str:
    text = (caption or "").strip().replace("\n", " ")
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def generate_growth_insights(analysis: Dict[str, Any]) -> List[str]:
    """
    Build human-readable observations from a full analyze_account() result.
    """
    insights: List[str] = []

    account = analysis.get("account", {})
    username = account.get("username", "this account")
    avg_data = analysis.get("avg_engagement_rate", {})
    frequency = analysis.get("posting_frequency", {})
    best_day = analysis.get("best_posting_day", {})
    content_types = analysis.get("content_type_performance", [])
    top_posts = analysis.get("top_performing_posts", [])

    avg_rate = avg_data.get("avg_engagement_rate", 0.0)
    post_count = avg_data.get("post_count", 0)
    if post_count > 0:
        insights.append(
            f"@{username} averages {avg_rate}% engagement across {post_count} synced posts."
        )

    posts_per_week = frequency.get("posts_per_week", 0.0)
    if posts_per_week > 0:
        if posts_per_week < 1:
            pace = "low"
        elif posts_per_week <= 3:
            pace = "moderate"
        elif posts_per_week <= 7:
            pace = "solid"
        else:
            pace = "high"
        insights.append(
            f"Posting frequency is {posts_per_week} posts/week ({pace} cadence)."
        )

    day = best_day.get("day")
    if day:
        day_rate = best_day.get("avg_engagement_rate", 0.0)
        insights.append(
            f"Best day to post is {day} with {day_rate}% avg engagement."
        )

    if len(content_types) >= 2:
        ranked = sorted(
            content_types,
            key=lambda item: item["avg_engagement_rate"],
            reverse=True,
        )
        best = ranked[0]
        runner_up = ranked[1]
        if runner_up["avg_engagement_rate"] > 0:
            multiplier = best["avg_engagement_rate"] / runner_up["avg_engagement_rate"]
            if multiplier >= 1.25:
                insights.append(
                    f"{best['media_type']} posts get {multiplier:.1f}x more engagement "
                    f"than {runner_up['media_type']} "
                    f"({best['avg_engagement_rate']}% vs {runner_up['avg_engagement_rate']}%)."
                )
            else:
                insights.append(
                    f"{best['media_type']} leads with {best['avg_engagement_rate']}% avg engagement, "
                    f"followed by {runner_up['media_type']} at {runner_up['avg_engagement_rate']}%."
                )
        elif best["avg_engagement_rate"] > 0:
            insights.append(
                f"{best['media_type']} is the top content type at "
                f"{best['avg_engagement_rate']}% avg engagement."
            )
    elif len(content_types) == 1:
        only = content_types[0]
        insights.append(
            f"All synced posts are {only['media_type']} with "
            f"{only['avg_engagement_rate']}% avg engagement."
        )

    if top_posts:
        leader = top_posts[0]
        caption = _caption_preview(leader.get("caption"))
        if caption:
            insights.append(
                f"Top post reached {leader['engagement_rate']}% engagement — "
                f"caption: \"{caption}\""
            )
        else:
            insights.append(
                f"Top post reached {leader['engagement_rate']}% engagement "
                f"({leader.get('media_type', 'unknown')} format)."
            )

    if not insights:
        insights.append("Not enough synced data yet to identify clear growth patterns.")

    return insights


def analyze_account(account_id: str) -> Dict[str, Any]:
    """
    Run a full metrics analysis for an Instagram Business account.
    """
    account_info = _load_account_info(account_id)

    analysis: Dict[str, Any] = {
        "account_id": account_id,
        "account": {
            "username": account_info["username"],
            "followers_count": account_info["followers_count"],
            "media_count": account_info["media_count"],
        },
        "avg_engagement_rate": avg_engagement_rate(account_id),
        "top_performing_posts": top_performing_posts(account_id, limit=3),
        "posting_frequency": posting_frequency(account_id),
        "best_posting_day": best_posting_day(account_id),
        "content_type_performance": content_type_performance(account_id),
    }
    analysis["growth_insights"] = generate_growth_insights(analysis)

    logger.info(
        "analyze_account(%s) completed for @%s with %s insights",
        account_id,
        account_info["username"],
        len(analysis["growth_insights"]),
    )
    return analysis
