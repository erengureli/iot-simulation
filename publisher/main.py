import os
import time

from sensor_sim import SensorSimulator
from mqtt_publisher import create_mqtt_client, publish_payload

PUBLISH_INTERVAL = int(os.environ.get("PUBLISH_INTERVAL", 2))
NUM_SENSORS = int(os.environ.get("NUM_SENSORS", 100))
TOPIC = "5/telemetry"


def main():
    simulators = [SensorSimulator(f"sensor_{i + 1}") for i in range(NUM_SENSORS)]
    client = create_mqtt_client()

    # Start the network loop in a background thread
    client.loop_start()

    print(f"[★] Publishing started on topic: {TOPIC} for {NUM_SENSORS} sensors\n")
    try:
        while True:
            for simulator in simulators:
                payload = simulator.get_next_payload()
                publish_payload(client, payload)

            time.sleep(PUBLISH_INTERVAL)
    except KeyboardInterrupt:
        print("\n[!] Stopping publisher...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
