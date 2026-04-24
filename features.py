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


def compute_arrival_rate(rows):
    if not rows:
        return np.float32(0.0)

    added_count = sum(1 for row in rows if row.get("interaction_type") == "added")
    per_minute = added_count / (WINDOW_SECONDS / 60)
    return np.float32(per_minute)


def compute_burstiness(rows):
    added_arrivals = sorted(
        row.get("timestamp_arrival")
        for row in rows
        if row.get("interaction_type") == "added"
    )

    if len(added_arrivals) < 2:
        return np.float32(0.0)

    inter_arrival_times = [
        added_arrivals[i] - added_arrivals[i - 1] for i in range(1, len(added_arrivals))
    ]
    return np.float32(np.var(inter_arrival_times))
