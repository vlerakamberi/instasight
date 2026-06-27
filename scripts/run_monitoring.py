import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.connection import init_db
from app.analytics.monitoring import run_daily_monitoring
from app.notifications.email_sender import send_alert_email

ACCOUNT_ID = "17841409576371357"

if __name__ == "__main__":
    init_db()
    result = run_daily_monitoring(ACCOUNT_ID)
    print(f"Monitoring complete: {result['alerts_count']} alerts")

    if result["alerts_count"] > 0:
        sent = send_alert_email(ACCOUNT_ID, result["alerts"])
        print(f"Alert email sent: {sent}")
    else:
        print("No alerts — account performing normally")
