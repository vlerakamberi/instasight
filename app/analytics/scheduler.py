import threading
import time
from typing import Any, Dict

import schedule

from app.analytics.monitoring import run_daily_monitoring
from app.config import load_settings
from app.notifications.email_sender import send_alert_email
from app.utils_logger import setup_logger


ACCOUNT_ID = "17841409576371357"

logger = setup_logger("scheduler")


def run_monitoring_job() -> Dict[str, Any]:
    """
    Run one monitoring cycle and email any alerts that were raised.
    """
    logger.info("Running scheduled monitoring job")
    result = run_daily_monitoring(ACCOUNT_ID)

    if result["alerts_count"] > 0:
        send_alert_email(ACCOUNT_ID, result["alerts"])
        logger.info("Alert email sent for %s alerts", result["alerts_count"])
    else:
        logger.info("No alerts — account performing normally")

    logger.info("Job complete")
    return result


def start_scheduler() -> threading.Thread:
    """
    Run monitoring once now, then every 24 hours on a background daemon thread.
    """
    settings = load_settings()
    if not settings.gmail_address or not settings.gmail_app_password:
        logger.warning(
            "Gmail not configured — alert emails will fail until "
            "GMAIL_ADDRESS and GMAIL_APP_PASSWORD are set in .env"
        )

    schedule.every(24).hours.do(run_monitoring_job)

    # Run once immediately on start.
    run_monitoring_job()

    def scheduler_loop() -> None:
        while True:
            schedule.run_pending()
            time.sleep(60)

    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()

    logger.info("Scheduler started — monitoring every 24 hours")
    return thread


def get_scheduler_status() -> Dict[str, Any]:
    """
    Report the current scheduler state and next scheduled run.
    """
    return {
        "is_running": True,
        "next_run": str(schedule.next_run()),
        "account_id": ACCOUNT_ID,
        "job_count": len(schedule.jobs),
    }
