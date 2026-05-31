"""
Standalone script to test the real Meta Graph API connection and sync pipeline.

Run from project root:
    python tests/test_real_api.py
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.analytics.sync_service import sync_account_data  # noqa: E402
from app.api.meta_client import MetaClient  # noqa: E402
from app.database.connection import get_connection, init_db  # noqa: E402


def _caption_preview(caption: str | None, max_len: int = 50) -> str:
    text = (caption or "").strip().replace("\n", " ")
    if len(text) <= max_len:
        return text or "(no caption)"
    return text[:max_len] + "..."


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass


def main() -> None:
    _configure_stdout()
    try:
        print("Initializing database...")
        init_db()

        print("Connecting to Meta Graph API...")
        client = MetaClient()

        print("Running full sync pipeline...")
        summary = sync_account_data(client)
        print()
        print("Sync summary:")
        print(f"  Account: {summary['account']}")
        print(f"  Posts synced: {summary['posts_synced']}")
        print(f"  Insights synced: {summary['insights_synced']}")
        print()

        with get_connection() as conn:
            account = conn.execute(
                """
                SELECT username, followers_count, media_count
                FROM accounts
                ORDER BY synced_at DESC
                LIMIT 1
                """
            ).fetchone()

            if account is None:
                print("No account data found in database.")
                return

            username = account["username"]
            followers = account["followers_count"]
            media_count = account["media_count"]

            posts_in_db = conn.execute("SELECT COUNT(*) AS c FROM posts").fetchone()["c"]

            print(
                f"✅ Account: @{username} | Followers: {followers:,} | Posts: {posts_in_db}"
            )
            print(f"   (API media_count: {media_count})")
            print()

            posts = conn.execute(
                """
                SELECT
                    p.id,
                    p.caption,
                    i.likes_count,
                    i.reach
                FROM posts p
                INNER JOIN insights i ON i.id = (
                    SELECT id
                    FROM insights
                    WHERE post_id = p.id
                    ORDER BY synced_at DESC
                    LIMIT 1
                )
                ORDER BY p.timestamp DESC
                LIMIT 3
                """
            ).fetchall()

            if not posts:
                print("No posts with insights found in database.")
                return

            print("Recent posts (latest insights):")
            for row in posts:
                caption = _caption_preview(row["caption"])
                likes = row["likes_count"] or 0
                reach = row["reach"] or 0
                print(f"📸 Post: [{caption}] | Likes: {likes:,} | Reach: {reach:,}")

    except Exception as exc:  # noqa: BLE001 - top-level script error reporting
        print()
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
