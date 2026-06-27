from datetime import datetime
from typing import Any, Dict

import anthropic

from app.analytics.analysis import analyze_account
from app.analytics.report_builder import build_prompt_context, build_report
from app.config import load_settings
from app.utils_logger import setup_logger


logger = setup_logger("performance_advisor")

MODEL = "claude-sonnet-4-6"
SYSTEM_PROMPT = """
You are a senior Instagram performance analyst.
Your job is to diagnose WHY an account is performing the way it is,
and give 3 concrete, data-backed recommendations.

Structure your response EXACTLY like this:

## Performance Diagnosis
One paragraph explaining the account's current state based ONLY
on the numbers provided. Be specific — mention actual percentages
and days.

## Why This Is Happening
2-3 bullet points explaining the root causes of current performance
patterns. Reference specific data points.

## 3 Concrete Actions (This Month)
For each action:
- What to do (specific, not generic)
- Why (based on which specific metric)
- Expected impact (realistic, based on their data)

## What to Watch
2 metrics to monitor over the next 30 days and what change
would indicate progress.

Write in Albanian. Be direct. No generic advice.
Every sentence must reference a specific number from the data.
Do NOT write captions. Do NOT write a weekly plan. Do NOT write hashtags.
"""


def _build_advice_context(account_id: str) -> tuple[str, str, Dict[str, Any]]:
    """Assemble the diagnosis prompt context plus account metadata snapshot."""
    report = build_report(account_id)
    analysis = analyze_account(account_id)

    summary = report["account_summary"]
    patterns = report["patterns"]
    username = summary["username"]

    avg_engagement_rate = summary["avg_engagement_rate"]
    total_posts = summary["total_posts"]
    synced_posts = summary.get("synced_posts_in_db", 0)
    followers = summary["followers"]

    frequency = analysis.get("posting_frequency", {})
    posts_per_week = frequency.get("posts_per_week", patterns["posts_per_week"])
    best_day = analysis.get("best_posting_day", {}).get("day") or patterns["best_day"]
    best_content_type = patterns["best_content_type"]

    base_context = build_prompt_context(report)
    extra_context = (
        "\n\n=== DIAGNOSIS REQUEST ==="
        "\nDo NOT suggest captions or weekly plans."
        f"\nDiagnose: Is {avg_engagement_rate}% engagement good or bad for this account size?"
        f"\nIs {posts_per_week} posts/week optimal?"
        f"\nWhat does the gap between total_posts={total_posts} and "
        f"synced_posts={synced_posts} tell us?"
        "\nWhich content type should they double down on based on the breakdown data?"
    )

    context = base_context + extra_context
    metrics_snapshot = {
        "avg_engagement_rate": avg_engagement_rate,
        "posts_per_week": posts_per_week,
        "best_day": best_day,
        "best_content_type": best_content_type,
        "followers": followers,
    }
    return context, username, metrics_snapshot


def generate_performance_advice(account_id: str) -> Dict[str, Any]:
    """
    Build account data and request a data-backed performance diagnosis from Claude.
    """
    settings = load_settings()
    context, username, metrics_snapshot = _build_advice_context(account_id)

    logger.info(
        "Generating performance advice for @%s (account_id=%s)",
        username,
        account_id,
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    with client.messages.stream(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context}],
    ) as stream:
        full_text = stream.get_final_text()

    advice_text = full_text.strip()
    generated_at = datetime.now().replace(microsecond=0).isoformat()

    result = {
        "account_id": account_id,
        "username": username,
        "advice": advice_text,
        "metrics_snapshot": metrics_snapshot,
        "generated_at": generated_at,
    }

    logger.info(
        "Performance advice generated for @%s (%s characters)",
        username,
        len(advice_text),
    )
    return result
