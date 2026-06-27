import sys

import pytest

from app.config import load_settings
from app.database.connection import DB_PATH
from app.notifications.email_sender import send_weekly_plan_email


pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(),
    reason="Real database not found; run python tests/test_real_api.py first",
)

ACCOUNT_ID = "17841409576371357"

# Real recipient for the live email test. Defaults to the configured Gmail
# sender so the test mailbox receives its own message.
_settings = load_settings()
RECIPIENT_EMAIL = _settings.gmail_address or "test@example.com"


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass


@pytest.mark.skipif(
    not (_settings.gmail_address and _settings.gmail_app_password),
    reason="Gmail credentials not configured (GMAIL_ADDRESS / GMAIL_APP_PASSWORD)",
)
def test_send_weekly_plan_email_returns_true() -> None:
    _configure_stdout()
    sent = send_weekly_plan_email(ACCOUNT_ID, RECIPIENT_EMAIL)

    assert sent is True

    print("\n" + "=" * 60)
    print(f"✅ Weekly plan email sent to {RECIPIENT_EMAIL}")
    print("=" * 60 + "\n")
