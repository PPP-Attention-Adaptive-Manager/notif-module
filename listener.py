import asyncio
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


async def on_notification_removed(sender, args) -> None:
    global db_conn
    try:
        from winsdk.windows.ui.notifications import UserNotificationChangedKind  # pyright: ignore[reportMissingImports]

        notif_id = args.user_notification.id
        timestamp_action = time.time()
        interaction_type = (
            "dismissed"
            if args.change_kind == UserNotificationChangedKind.REMOVED
            else "expired"
        )

        cursor = db_conn.execute(
            """
            SELECT id, timestamp_arrival
            FROM notifications
            WHERE notif_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (notif_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return

        row_id, timestamp_arrival = row
        response_time = None
        if timestamp_arrival is not None:
            response_time = timestamp_action - timestamp_arrival

        db_conn.execute(
            """
            UPDATE notifications
            SET timestamp_action = ?,
                interaction_type = ?,
                response_time = ?
            WHERE id = ?
            """,
            (timestamp_action, interaction_type, response_time, row_id),
        )
        db_conn.commit()
    except Exception as error:
        print(error)


async def run_listener() -> None:
    from winsdk.windows.ui.notifications import UserNotificationChangedKind  # pyright: ignore[reportMissingImports]
    from winsdk.windows.ui.notifications.management import UserNotificationListener  # pyright: ignore[reportMissingImports]

    listener = UserNotificationListener.current
    access_status = await listener.request_access_async()
    print(access_status)

    def _handle_added(sender, args) -> None:
        if args.change_kind == UserNotificationChangedKind.ADDED:
            asyncio.create_task(on_notification_added(sender, args))

    def _handle_removed(sender, args) -> None:
        if args.change_kind == UserNotificationChangedKind.REMOVED:
            asyncio.create_task(on_notification_removed(sender, args))

    listener.add_notification_changed(_handle_added)
    listener.add_notification_changed(_handle_removed)

    while True:
        await asyncio.sleep(1)