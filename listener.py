import sqlite3
import time


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


async def on_notification_added(sender, args) -> None:
    global db_conn
    try:
        from winsdk.windows.ui.notifications.management import UserNotificationListener  # pyright: ignore[reportMissingImports]

        app_name = args.user_notification.app_info.display_info.display_name
        notif_id = args.user_notification.id
        timestamp_arrival = time.time()

        db_conn.execute(
            """
            INSERT INTO notifications (
                timestamp_arrival,
                timestamp_action,
                app_name,
                notif_id,
                interaction_type,
                response_time
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (timestamp_arrival, None, app_name, notif_id, "added", None),
        )
        db_conn.commit()
        _ = UserNotificationListener
    except Exception as error:
        print(error)