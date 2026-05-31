from datetime import date, datetime, timedelta
from typing import Any, Dict

import anthropic

from app.ai.benchmarks import BENCHMARK_CONTEXT
from app.analytics.analysis import analyze_account
from app.analytics.report_builder import build_prompt_context, build_report
from app.config import load_settings
from app.utils_logger import setup_logger


logger = setup_logger("weekly_planner")

MODEL = "claude-sonnet-4-6"
SYSTEM_PROMPT = (
    "You are a weekly Instagram growth coach for Albanian-speaking "
    "businesses. Generate a CONCRETE weekly action plan for the "
    "coming week based on REAL performance data.\n\n"
    "The plan must include:\n\n"
    "MONDAY: Exact post idea + caption ready to copy-paste\n"
    "TUESDAY: Exact post idea + caption ready to copy-paste\n"
    "WEDNESDAY: Stories idea (3 specific story frames)\n"
    "THURSDAY: Exact post idea + caption ready to copy-paste\n"
    "SATURDAY: Best day - most important post of the week + caption\n"
    "SUNDAY: Weekly review checklist\n\n"
    "For each post include:\n"
    "- Exact caption in Albanian (ready to use, not a template)\n"
    "- 15-20 specific hashtags\n"
    "- Best time to post (based on data)\n"
    "- What photo/video to take (specific instructions)\n"
    "- Expected engagement based on historical data\n\n"
    "Base EVERYTHING on the real account data provided.\n\n"
    + BENCHMARK_CONTEXT
)


def coming_week_bounds(today: date | None = None) -> tuple[date, date]:
    """Return (Monday, Sunday) for the coming week (today if today is Monday)."""
    today = today or date.today()
    days_ahead = (0 - today.weekday()) % 7
    week_start = today + timedelta(days=days_ahead)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def _build_plan_context(account_id: str) -> tuple[str, str, str, str]:
    """Assemble the prompt context plus account/week metadata."""
    report = build_report(account_id)
    analysis = analyze_account(account_id)
    username = report["account_summary"]["username"]

    report_context = build_prompt_context(report)

    best_day = analysis.get("best_posting_day", {})
    frequency = analysis.get("posting_frequency", {})
    content_types = analysis.get("content_type_performance", [])

    week_start, week_end = coming_week_bounds()

    pattern_lines = [
        "",
        "=== PATTERNS FOR WEEKLY PLANNING ===",
        f"Planning for the week: {week_start.isoformat()} (Mon) to {week_end.isoformat()} (Sun)",
        f"Best posting day: {best_day.get('day', 'unknown')} "
        f"(avg engagement {best_day.get('avg_engagement_rate', 'n/a')}%)",
        f"Current posting frequency: {frequency.get('posts_per_week', 'n/a')} posts/week",
    ]
    if content_types:
        pattern_lines.append("Content type performance:")
        for item in content_types:
            pattern_lines.append(
                f"- {item['media_type']}: {item['post_count']} posts, "
                f"avg engagement {item['avg_engagement_rate']}%"
            )
    pattern_lines.extend(
        [
            "",
            "Generate the weekly plan strictly from the metrics above.",
        ]
    )

    context = report_context + "\n" + "\n".join(pattern_lines)
    return context, username, week_start.isoformat(), week_end.isoformat()


def generate_weekly_plan(account_id: str) -> Dict[str, Any]:
    """
    Build account data and request a concrete weekly action plan from Claude.
    """
    settings = load_settings()
    context, username, week_start, week_end = _build_plan_context(account_id)

    logger.info(
        "Generating weekly plan for @%s (account_id=%s, week %s to %s)",
        username,
        account_id,
        week_start,
        week_end,
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context}],
    )

    plan_text = ""
    for block in response.content:
        if block.type == "text":
            plan_text += block.text

    plan_text = plan_text.strip()
    generated_at = datetime.now().replace(microsecond=0).isoformat()

    result = {
        "account_id": account_id,
        "username": username,
        "week_start": week_start,
        "week_end": week_end,
        "plan": plan_text,
        "generated_at": generated_at,
    }

    logger.info(
        "Weekly plan generated for @%s (%s characters)",
        username,
        len(plan_text),
    )
    return result
