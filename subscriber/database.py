import os
import re
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "sensors.db")


def natural_sort_key(s):
    """Helper for naturally sorting sensor IDs."""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split("([0-9]+)", s)
    ]


def init_db():
    """Initializes the SQLite database and creates the readings table."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT,
                timestamp TEXT,
                temperature REAL,
                humidity REAL,
                light REAL
            )
        """
        )
        conn.commit()


def get_all_sensors():
    """Returns a naturally sorted list of all sensor IDs in the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT sensor_id FROM readings")
        sensors = [row[0] for row in cursor.fetchall()]
    return sorted(sensors, key=natural_sort_key)


def get_sensor_stats(sensor_id):
    """Retrieves the latest stats and history for a given sensor."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get total count
        cursor.execute(
            "SELECT COUNT(*) FROM readings WHERE sensor_id = ?", (sensor_id,)
        )
        count = cursor.fetchone()[0]

        if count == 0:
            return None

        # Get latest reading
        cursor.execute(
            "SELECT * FROM readings WHERE sensor_id = ? ORDER BY id DESC LIMIT 1",
            (sensor_id,),
        )
        latest = cursor.fetchone()

        # Get history (last 50 readings)
        cursor.execute(
            "SELECT * FROM readings WHERE sensor_id = ? ORDER BY id DESC LIMIT 50",
            (sensor_id,),
        )
        history_rows = cursor.fetchall()

        # Reverse history to be in chronological order
        history = [
            {
                "timestamp": row["timestamp"],
                "temperature": row["temperature"],
                "humidity": row["humidity"],
                "light": row["light"],
            }
            for row in reversed(history_rows)
        ]

        return {
            "count": count,
            "timestamp": latest["timestamp"],
            "readings": {
                "temperature": latest["temperature"],
                "humidity": latest["humidity"],
                "light": latest["light"],
            },
            "history": history,
        }


def insert_reading(sensor_id, timestamp, temperature, humidity, light):
    """Inserts a sensor reading into the database."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO readings (sensor_id, timestamp, temperature, humidity, light)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sensor_id, timestamp, temperature, humidity, light),
        )
        conn.commit()
