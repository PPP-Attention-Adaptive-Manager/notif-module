import sqlite3
import time
import math
import numpy as np

WINDOW_SECONDS = 60
DB_PATH = "data/notif_log.db"


def fetch_window():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cutoff = time.time() - WINDOW_SECONDS
        cursor.execute(
            """
            SELECT timestamp_arrival, timestamp_action, app_name, interaction_type, response_time
            FROM notifications
            WHERE timestamp_arrival >= ?
            """,
            (cutoff,),
        )
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as error:
        print(error)
        return []
    finally:
        if conn is not None:
            conn.close()
