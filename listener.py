import sqlite3


def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect("data/notif_log.db")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_arrival REAL,
            timestamp_action REAL,
            app_name TEXT,
            notif_id INTEGER,
            interaction_type TEXT CHECK (interaction_type IN ('added', 'dismissed', 'expired')),
            response_time REAL
        )
        """
    )
    conn.commit()
    return conn