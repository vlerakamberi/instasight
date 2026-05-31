from app.api.meta_client import MetaClient
from app.analytics.sync_service import sync_account_data
from app.database.connection import init_db
from app.utils_logger import setup_logger


def main() -> None:
    logger = setup_logger("main")
    logger.info("Initializing database...")
    init_db()

    logger.info("Starting account sync...")
    client = MetaClient()
    summary = sync_account_data(client)
    logger.info("Sync completed: %s", summary)


if __name__ == "__main__":
    main()
