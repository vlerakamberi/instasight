from datetime import datetime
from typing import Any, Dict, List, Optional

from app.analytics.analysis import analyze_account
from app.database.connection import get_connection
from app.utils_logger import setup_logger


logger = setup_logger("report_builder")


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.strip()
    if normalized.endswith("+0000"):
        normalized = normalized[:-5] + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _normalize_caption(caption: Optional[str]) -> str:
    return (caption or "").strip().replace("\n", " ")


def _best_content_type(content_types: List[Dict[str, Any]]) -> str:
    if not content_types:
        return "UNKNOWN"
    ranked = sorted(
        content_types,
        key=lambda item: item.get("avg_engagement_rate", 0.0),
        reverse=True,
    )
    return ranked[0].get("media_type", "UNKNOWN")


def _load_posting_timeline(account_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, timestamp
            FROM posts
            WHERE account_id = ? AND timestamp IS NOT NULL
            ORDER BY timestamp DESC
            """,
            (account_id,),
        ).fetchall()

    timeline: List[Dict[str, Any]] = []
    previous_date: Optional[datetime] = None

    for row in rows:
        parsed = _parse_timestamp(row["timestamp"])
        if parsed is None:
            continue

        gap_days: Optional[int] = None
        if previous_date is not None:
            gap_days = (previous_date - parsed).days

        timeline.append(
            {
                "post_id": row["id"],
                "timestamp": row["timestamp"],
                "date": parsed.date().isoformat(),
                "days_since_previous": gap_days,
            }
        )
        previous_date = parsed

    return timeline


def build_report(account_id: str) -> Dict[str, Any]:
    """
    Build an LLM-ready report dict from full account analysis.
    """
    analysis = analyze_account(account_id)
    account = analysis["account"]
    avg = analysis["avg_engagement_rate"]
    frequency = analysis["posting_frequency"]
    best_day = analysis["best_posting_day"]
    content_types = analysis["content_type_performance"]
    posting_timeline = _load_posting_timeline(account_id)

    report: Dict[str, Any] = {
        "account_id": account_id,
        "account_summary": {
            "username": account["username"],
            "followers": account["followers_count"],
            "total_posts": account["media_count"],
            "synced_posts_in_db": avg["post_count"],
            "avg_engagement_rate": avg["avg_engagement_rate"],
        },
        "posting_frequency_detail": {
            "posts_per_week": frequency.get("posts_per_week", 0.0),
            "weeks_span": frequency.get("weeks_span", 0.0),
            "synced_post_count": frequency.get("post_count", 0),
        },
        "best_posting_day": {
            "day": best_day.get("day"),
            "avg_engagement_rate": best_day.get("avg_engagement_rate", 0.0),
            "post_count": best_day.get("post_count", 0),
        },
        "top_posts": [
            {
                "post_id": post.get("post_id"),
                "caption": _normalize_caption(post.get("caption")),
                "media_type": post.get("media_type") or "UNKNOWN",
                "likes_count": post.get("likes_count", 0),
                "comments_count": post.get("comments_count", 0),
                "engagement_rate": post["engagement_rate"],
                "followers_count": post.get("followers_count", 0),
            }
            for post in analysis["top_performing_posts"][:3]
        ],
        "posting_timeline": posting_timeline,
        "media_type_breakdown": [
            {
                "media_type": item["media_type"],
                "post_count": item["post_count"],
                "avg_engagement_rate": item["avg_engagement_rate"],
            }
            for item in content_types
        ],
        "patterns": {
            "best_day": best_day.get("day") or "Unknown",
            "posts_per_week": frequency.get("posts_per_week", 0.0),
            "best_content_type": _best_content_type(content_types),
        },
        "growth_insights": list(analysis["growth_insights"]),
        "generated_at": datetime.now().replace(microsecond=0).isoformat(),
    }

    post_ids = {post["post_id"] for post in report["top_posts"] if post.get("post_id")}
    timestamps_by_id = {
        entry["post_id"]: entry["timestamp"]
        for entry in posting_timeline
        if entry["post_id"] in post_ids
    }
    for post in report["top_posts"]:
        post["timestamp"] = timestamps_by_id.get(post.get("post_id"))

    logger.info(
        "build_report(%s) for @%s at %s",
        account_id,
        report["account_summary"]["username"],
        report["generated_at"],
    )
    return report


def build_prompt_context(report: Dict[str, Any]) -> str:
    """
    Format a report dict as plain text for LLM prompt context (real DB metrics only).
    """
    summary = report["account_summary"]
    patterns = report["patterns"]
    frequency = report.get("posting_frequency_detail", {})
    best_day = report.get("best_posting_day", {})
    username = summary["username"]

    lines = [
        "=== REAL INSTAGRAM DATA (from database sync) ===",
        "Use ONLY the metrics below. Do not invent numbers.",
        "",
        f"Account: @{username} (id: {report.get('account_id', 'n/a')})",
        f"Followers: {summary['followers']:,}",
        f"Total posts on profile (API media_count): {summary['total_posts']}",
        f"Synced posts in database: {summary.get('synced_posts_in_db', 0)}",
        (
            f"Avg engagement rate: {summary['avg_engagement_rate']}% "
            f"(formula: (likes + comments) / followers * 100 per post, then averaged)"
        ),
        "",
        "Benchmarks (industry reference — not account-specific):",
        "- Good business engagement rate: 1-3%",
        "- Growing accounts typically post: 3-5 times/week",
        "- Reels often get ~30% more reach than static images",
        "",
        "Posting frequency (computed from synced post timestamps):",
        f"- Posts per week: {frequency.get('posts_per_week', patterns['posts_per_week'])}",
        f"- Weeks span of synced data: {frequency.get('weeks_span', 'n/a')}",
        f"- Synced posts used: {frequency.get('synced_post_count', 'n/a')}",
        "",
        "Best posting day (from synced posts):",
        f"- Day: {best_day.get('day', patterns['best_day'])}",
        f"- Avg engagement that day: {best_day.get('avg_engagement_rate', 'n/a')}%",
        f"- Posts on that day in sample: {best_day.get('post_count', 'n/a')}",
        "",
        "Top 3 posts by engagement rate:",
    ]

    top_posts = report.get("top_posts", [])
    if top_posts:
        for index, post in enumerate(top_posts, start=1):
            caption = post.get("caption") or "(no caption)"
            lines.extend(
                [
                    f"{index}. post_id={post.get('post_id', 'n/a')}",
                    f"   Date: {post.get('timestamp') or 'unknown'}",
                    f"   Media type: {post['media_type']}",
                    (
                        f"   Likes: {post.get('likes_count', 0):,} | "
                        f"Comments: {post.get('comments_count', 0):,} | "
                        f"Engagement rate: {post['engagement_rate']}% "
                        f"(followers base: {post.get('followers_count', summary['followers']):,})"
                    ),
                    f"   Caption: {caption}",
                ]
            )
    else:
        lines.append("- No top posts in synced data.")

    lines.extend(["", "Posting timeline (newest first, gaps between posts):"])
    timeline = report.get("posting_timeline", [])
    if timeline:
        for entry in timeline[:10]:
            gap = entry.get("days_since_previous")
            gap_text = (
                f"{gap} days since previous post"
                if gap is not None
                else "most recent post in sample"
            )
            lines.append(
                f"- {entry.get('date')} | post_id={entry.get('post_id')} | {gap_text}"
            )
        if len(timeline) > 10:
            lines.append(f"- ... {len(timeline) - 10} older synced posts not shown")
    else:
        lines.append("- insufficient data: no timestamps in synced posts")

    lines.extend(["", "Media type breakdown (synced posts):"])
    breakdown = report.get("media_type_breakdown", [])
    if breakdown:
        for item in breakdown:
            lines.append(
                f"- {item['media_type']}: {item['post_count']} posts | "
                f"avg engagement {item['avg_engagement_rate']}%"
            )
    else:
        lines.append("- insufficient data: no media types in synced posts")

    lines.extend(
        [
            "",
            "Computed growth insights (from metrics module):",
        ]
    )
    insights = report.get("growth_insights", [])
    if insights:
        for insight in insights:
            lines.append(f"- {insight}")
    else:
        lines.append("- insufficient data: no growth insights generated")

    context = "\n".join(lines)
    logger.info(
        "build_prompt_context(@%s) produced %s characters",
        username,
        len(context),
    )
    return context
