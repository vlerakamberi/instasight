from typing import Dict

from app.api.meta_client import MetaClient
from app.database.connection import get_connection, init_db
from app.utils_logger import setup_logger


logger = setup_logger("sync_service")


def sync_account_data(client: MetaClient) -> Dict:
    """
    Syncs account profile, posts, and insights into SQLite.
    Returns a summary of posts and insights written during this run.
    """
    init_db()
    posts_synced = 0
    insights_synced = 0

    logger.info("Fetching account profile...")
    profile = client.get_profile_info()
    account_id = profile["instagram_account_id"]
    username = profile["username"]

    logger.info("Fetching recent media...")
    posts = client.get_recent_media()
    logger.info("Retrieved %s posts for account %s", len(posts), username)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO accounts (
                id, username, followers_count, media_count, biography, synced_at
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                account_id,
                username,
                profile["followers_count"],
                profile["media_count"],
                profile["biography"],
            ),
        )
        logger.info("Account saved: %s (id=%s)", username, account_id)

        for post in posts:
            post_id = post["post_id"]
            existing = conn.execute(
                "SELECT 1 FROM posts WHERE id = ?",
                (post_id,),
            ).fetchone()

            if existing is None:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO posts (
                        id, account_id, caption, media_type, timestamp, permalink
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        post_id,
                        account_id,
                        post["caption"],
                        post["media_type"],
                        post["timestamp"],
                        post["permalink"],
                    ),
                )
                posts_synced += 1
                logger.info("Post saved: %s", post_id)
            else:
                logger.info("Post skipped (already exists): %s", post_id)

            try:
                logger.info("Fetching insights for post: %s", post_id)
                insights = client.get_media_insights(post_id)
                conn.execute(
                    """
                    INSERT INTO insights (
                        post_id,
                        likes_count,
                        comments_count,
                        shares,
                        saves,
                        reach,
                        impressions
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        post_id,
                        insights["likes_count"],
                        insights["comments_count"],
                        insights["shares"],
                        insights["saves"],
                        insights["reach"],
                        insights["impressions"],
                    ),
                )
                insights_synced += 1
                logger.info("Insights saved for post: %s", post_id)
            except Exception as exc:  # noqa: BLE001 - continue sync on single post failure
                logger.error(
                    "Failed to sync insights for post %s: %s",
                    post_id,
                    exc,
                )

        conn.commit()

    summary = {
        "posts_synced": posts_synced,
        "insights_synced": insights_synced,
        "account": username,
    }
    logger.info(
        "Sync completed: account=%s, posts_synced=%s, insights_synced=%s",
        username,
        posts_synced,
        insights_synced,
    )
    return summary
