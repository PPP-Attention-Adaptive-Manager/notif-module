import asyncio
import sqlite3
import time
import threading

db_conn = None
previous_notif_ids = set()


def init_db() -> sqlite3.Connection:
    import os
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/notif_log.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_arrival REAL,
            timestamp_action REAL,
            app_name TEXT,
            notif_id INTEGER,
            interaction_type TEXT CHECK (interaction_type IN ('added', 'dismissed', 'expired')),
            response_time REAL
        )
    """)
    conn.commit()
    return conn


async def poll_notifications() -> None:
    global db_conn, previous_notif_ids
    try:
        from winsdk.windows.ui.notifications import NotificationKinds
        from winsdk.windows.ui.notifications.management import UserNotificationListener

        listener = UserNotificationListener.current
        notifications = await listener.get_notifications_async(NotificationKinds.TOAST)
        current_notifs = {
            notif.id: notif.app_info.display_info.display_name
            for notif in notifications
        }

        current_ids = set(current_notifs.keys())
        added_ids = current_ids - previous_notif_ids
        removed_ids = previous_notif_ids - current_ids

        for notif_id in added_ids:
            db_conn.execute("""
                INSERT INTO notifications (timestamp_arrival, timestamp_action, app_name, notif_id, interaction_type, response_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (time.time(), None, current_notifs[notif_id], notif_id, "added", None))

        for notif_id in removed_ids:
            cursor = db_conn.execute("""
                SELECT id, timestamp_arrival FROM notifications
                WHERE notif_id = ? ORDER BY id DESC LIMIT 1
            """, (notif_id,))
            row = cursor.fetchone()
            if row:
                row_id, timestamp_arrival = row
                timestamp_action = time.time()
                db_conn.execute("""
                    UPDATE notifications
                    SET timestamp_action = ?, interaction_type = ?, response_time = ?
                    WHERE id = ?
                """, (timestamp_action, "dismissed", timestamp_action - timestamp_arrival, row_id))

        previous_notif_ids = current_ids
        db_conn.commit()

    except Exception as error:
        print(f"[poll_notifications] {error!r}")


async def run_listener() -> None:
    from winsdk.windows.ui.notifications.management import UserNotificationListener

    listener = UserNotificationListener.current
    access_status = await listener.request_access_async()
    print(f"Access status: {access_status}")

    while True:
        await poll_notifications()
        await asyncio.sleep(2)


def sta_thread_main():
    global db_conn
    import ctypes
    ctypes.windll.ole32.CoInitializeEx(None, 0)
    try:
        db_conn = init_db()  # ← créé dans le bon thread
        asyncio.run(run_listener())
    finally:
        if db_conn is not None:
            db_conn.close()
        ctypes.windll.ole32.CoUninitialize()


if __name__ == "__main__":
    print("Notification listener started. Press Ctrl+C to stop.")
    try:
        thread = threading.Thread(target=sta_thread_main, daemon=True)
        thread.start()
        thread.join()
    except KeyboardInterrupt:
        print("Stopping...")