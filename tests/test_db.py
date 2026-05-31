from app.database.connection import get_connection, init_db


def test_init_db_creates_required_tables():
    init_db()

    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = {row["name"] for row in cursor.fetchall()}

    expected = {"accounts", "posts", "insights"}
    assert expected.issubset(table_names)
