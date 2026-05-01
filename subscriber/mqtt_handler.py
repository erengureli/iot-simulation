import json
import os
import time

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from database import insert_reading

BROKER_HOST = os.environ.get("BROKER_HOST", "localhost")
BROKER_PORT = int(os.environ.get("BROKER_PORT", 1883))
TOPIC = "5/telemetry"


def on_connect(client, userdata, flags, rc, properties=None):
    """Callback triggered when the client connects to the broker."""
    if rc == 0:
        print(f"[✓] Connected to Broker: {BROKER_HOST}:{BROKER_PORT}")
        client.subscribe(TOPIC)
        print(f"[★] Subscribed to topic: {TOPIC}")
    else:
        print(f"[✗] Connection failed with code: {rc}")


def on_message(client, userdata, msg):
    """Callback triggered when a message is received."""
    try:
        payload = json.loads(msg.payload.decode())
        sensor_id = payload.get("sensor_id", "Unknown")
        readings = payload.get("values", {})
        timestamp = payload.get("timestamp", "N/A")

        insert_reading(
            sensor_id,
            timestamp,
            readings.get("temperature", 0),
            readings.get("humidity", 0),
            readings.get("light", 0),
        )

        # Consistent output format with publisher
        print(
            f"[SUB] {timestamp} | Sensor: {sensor_id} | "
            f"Temp: {readings.get('temperature', 0)}°C | "
            f"Humidity: {readings.get('humidity', 0)}% | "
            f"Light: {readings.get('light', 0)} lux"
        )
    except Exception as e:
        print(f"[!] Error parsing message: {e}")


def run_mqtt():
    """Connects to MQTT broker and runs the client loop."""
    client = mqtt.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id="multi_sensor_subscriber",
    )
    client.on_connect = on_connect
    client.on_message = on_message

    # Connection retry loop
    connected = False
    while not connected:
        try:
            print(f"Connecting to {BROKER_HOST}...")
            client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
            connected = True
        except Exception as e:
            print(f"Broker not ready ({e}), retrying in 3 seconds...")
            time.sleep(3)

    client.loop_forever()
