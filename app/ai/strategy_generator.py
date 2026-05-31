from datetime import datetime
from typing import Any, Dict

import anthropic

from app.analytics.report_builder import build_prompt_context, build_report
from app.config import load_settings
from app.utils_logger import setup_logger


logger = setup_logger("strategy_generator")

MODEL = "claude-sonnet-4-6"
SYSTEM_PROMPT = (
    "You are a senior Instagram marketing consultant with deep "
    "expertise in growing healthcare brands for Albanian-speaking "
    "audiences across North Macedonia, Kosovo, Albania and diaspora.\n\n"
    "BUSINESS CONTEXT:\n"
    "- Dental-B (@dentalb_ku) — dental clinic in Kumanovo, RMV\n"
    "- Target: ALL Albanian speakers, not just Kumanovo\n"
    "- Goal: Become a recognized dental brand across the region\n"
    "- Current: 998 followers, early stage\n\n"
    "Use your expertise to provide:\n"
    "- Specific hashtags that actually work for this niche and audience\n"
    "- Real caption examples in Albanian that drive engagement\n"
    "- Content ideas proven to work for dental clinics\n"
    "- Growth tactics used by successful healthcare accounts\n\n"
    "Every recommendation must reference the real account data provided.\n"
    "Never be generic. Be specific like a real consultant.\n"
    "Respond in Albanian."
)


def generate_strategy(account_id: str) -> Dict[str, Any]:
    """
    Build an analytics report and request a personalized growth strategy from Claude.
    """
    settings = load_settings()
    report = build_report(account_id)
    context = build_prompt_context(report)
    username = report["account_summary"]["username"]

    logger.info("Generating strategy for @%s (account_id=%s)", username, account_id)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context}],
    )

    strategy_text = ""
    for block in response.content:
        if block.type == "text":
            strategy_text += block.text

    strategy_text = strategy_text.strip()
    generated_at = datetime.now().replace(microsecond=0).isoformat()

    result = {
        "account_id": account_id,
        "username": username,
        "strategy": strategy_text,
        "generated_at": generated_at,
    }

    logger.info(
        "Strategy generated for @%s (%s characters)",
        username,
        len(strategy_text),
    )
    return result
