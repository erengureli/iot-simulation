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


def get_sensor_analysis(sensor_id):
    """Calculates min, max, average, and variance for a sensor's readings."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Check if sensor has data
        cursor.execute(
            "SELECT COUNT(*) FROM readings WHERE sensor_id = ?", (sensor_id,)
        )
        count = cursor.fetchone()[0]
        if count == 0:
            return None

        # Get min, max, avg for all three metrics
        cursor.execute(
            """
            SELECT
                MIN(temperature), MAX(temperature), AVG(temperature),
                MIN(humidity), MAX(humidity), AVG(humidity),
                MIN(light), MAX(light), AVG(light)
            FROM readings WHERE sensor_id = ?
            """,
            (sensor_id,),
        )
        row = cursor.fetchone()

        # Calculate variance manually:
        # VAR = AVG(x^2) - (AVG(x))^2
        cursor.execute(
            """
            SELECT
                AVG(temperature * temperature) - AVG(temperature) * AVG(temperature),
                AVG(humidity * humidity) - AVG(humidity) * AVG(humidity),
                AVG(light * light) - AVG(light) * AVG(light)
            FROM readings WHERE sensor_id = ?
            """,
            (sensor_id,),
        )
        var_row = cursor.fetchone()

        return {
            "count": count,
            "temperature": {
                "min": round(row[0], 2),
                "max": round(row[1], 2),
                "avg": round(row[2], 2),
                "variance": round(var_row[0], 4),
            },
            "humidity": {
                "min": round(row[3], 2),
                "max": round(row[4], 2),
                "avg": round(row[5], 2),
                "variance": round(var_row[1], 4),
            },
            "light": {
                "min": round(row[6], 2),
                "max": round(row[7], 2),
                "avg": round(row[8], 2),
                "variance": round(var_row[2], 4),
            },
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
