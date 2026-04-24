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


def compute_source_entropy(rows):
    added_rows = [row for row in rows if row.get("interaction_type") == "added"]
    if len(added_rows) < 2:
        return np.float32(0.0)

    counts = {}
    for row in added_rows:
        app_name = row.get("app_name")
        counts[app_name] = counts.get(app_name, 0) + 1

    total = len(added_rows)
    entropy = 0.0
    for count in counts.values():
        proportion = count / total
        entropy -= proportion * math.log2(proportion)

    return np.float32(entropy)


def compute_disruption_score(rows):
    qualifying = [
        row
        for row in rows
        if row.get("interaction_type") == "dismissed"
        and row.get("response_time") is not None
        and row.get("response_time") > 0
    ]

    if not qualifying:
        return np.float32(0.0)

    score_sum = sum(1.0 / row.get("response_time") for row in qualifying)
    return np.float32(score_sum / WINDOW_SECONDS)
