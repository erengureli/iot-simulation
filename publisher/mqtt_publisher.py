import json
import os
import time

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

BROKER_HOST = os.environ.get("BROKER_HOST", "localhost")
BROKER_PORT = int(os.environ.get("BROKER_PORT", 1883))
TOPIC = "5/telemetry"


def on_connect(client, userdata, flags, rc, properties=None):
    """Callback triggered when the client connects to the broker."""
    if rc == 0:
        print(f"[✓] Connected to Broker: {BROKER_HOST}:{BROKER_PORT}")
    else:
        print(f"[✗] Connection failed with code: {rc}")


def create_mqtt_client():
    """Creates and connects an MQTT client with retry logic."""
    client = mqtt.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id="multi_sensor_publisher",
    )
    client.on_connect = on_connect

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

    return client


def publish_payload(client, payload):
    """Publishes a sensor payload to the MQTT broker."""
    json_payload = json.dumps(payload)
    result = client.publish(TOPIC, json_payload, qos=1)

    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(
            f"[PUB] {payload['timestamp']} | Sensor: {payload['sensor_id']} | "
            f"Temp: {payload['values']['temperature']}°C | "
            f"Humidity: {payload['values']['humidity']}%"
        )
