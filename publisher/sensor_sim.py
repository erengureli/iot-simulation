import datetime
import random


class SensorSimulator:
    """Simulates realistic sensor data using a random walk."""

    def __init__(self, sensor_id):
        self.sensor_id = sensor_id
        # Define min/max ranges for sensors
        self.ranges = {
            "temperature": (15.0, 40.0),
            "humidity": (20.0, 95.0),
            "light": (0, 1200),
        }
        # Initial starting values
        self.current_values = {
            "temperature": 24.0,
            "humidity": 60.0,
            "light": 400.0,
        }

    def get_next_payload(self) -> dict:
        """Generates the next telemetry data packet."""
        for key, (lo, hi) in self.ranges.items():
            # Apply a small random change (max 4% of range)
            delta = (hi - lo) * 0.04
            val = self.current_values[key] + random.uniform(-delta, delta)
            # Keep value within bounds and round to 2 decimals
            self.current_values[key] = round(max(lo, min(hi, val)), 2)

        return {
            "sensor_id": self.sensor_id,
            "values": self.current_values.copy(),
            "unit": "metric",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(
                timespec="seconds"
            ),
        }
