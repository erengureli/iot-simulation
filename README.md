# 📡 MQTT IoT Sensor Monitoring System

A real-time IoT sensor data pipeline built with **Python**, **MQTT**, **SQLite**, and **Flask** — fully containerized with Docker Compose.

Simulates up to 100 independent sensors publishing temperature, humidity, and light data to an MQTT broker, which is then stored in a database and visualized on a live web dashboard.

---

## 🏗️ Architecture

```
┌─────────────────┐        ┌──────────────────┐        ┌──────────────────────┐
│   Publisher     │        │    Mosquitto     │        │    Subscriber        │
│                 │        │    MQTT Broker   │        │                      │
│  SensorSim x100 │ ──────▶│   5/telemetry    │──────▶│  mqtt_handler.py     │
│  mqtt_publisher │  MQTT  │   port 1883      │  MQTT  │  database.py         │
└─────────────────┘        └──────────────────┘        │  Flask :8000         │
                                                       └──────────────────────┘
                                                                  │
                                                          http://localhost:8000
```

**Three Docker services communicate over a shared bridge network:**

| Service | Image / Build | Role |
|---|---|---|
| `mosquitto` | `eclipse-mosquitto:latest` | MQTT message broker |
| `publisher` | Custom Python image | Sensor simulation & publishing |
| `subscriber` | Custom Python image | Data ingestion, storage & web UI |

---

## ✨ Features

- 🔄 **Real-time data pipeline** — sensor → broker → database → dashboard
- 🌡️ **Multi-sensor simulation** — up to 100 independent sensors with realistic random-walk values
- 📊 **Live dashboard** — Chart.js graphs for temperature, humidity, and light; auto-refreshes every second
- 💾 **Persistent storage** — SQLite on a named Docker volume; survives container restarts
- 🔁 **Auto-reconnect** — both publisher and subscriber retry broker connection automatically
- ⚙️ **Fully configurable** — all key parameters adjustable via environment variables

---

## 🚀 Getting Started

### Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/) 24+
- [Docker Compose](https://docs.docker.com/compose/install/) v2+

### Run

```bash
# Clone the repo
git clone https://github.com/erengureli/iot-simulation.git
cd iot-simulation

# Build and start all services
docker compose up -d --build

# Follow logs
docker compose logs -f
```

Open the dashboard at **http://localhost:8000**

### Stop

```bash
docker compose down        # Stop services, keep data
docker compose down -v     # Stop services and delete volume
```

---

## 📁 Project Structure

```
├── docker-compose.yml
├── mosquitto.conf
├── publisher/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py            # Entry point — runs publish loop
│   ├── sensor_sim.py      # SensorSimulator class (random walk)
│   └── mqtt_publisher.py  # MQTT client setup & publish helper
└── subscriber/
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py            # Flask app + starts MQTT thread
    ├── mqtt_handler.py    # MQTT subscriber & message parser
    └── database.py        # SQLite read/write layer
```

---

## ⚙️ Configuration

All parameters are set via environment variables in `docker-compose.yml`.

| Variable | Service | Description | Default |
|---|---|---|---|
| `BROKER_HOST` | Publisher, Subscriber | MQTT broker hostname | `localhost` |
| `BROKER_PORT` | Publisher, Subscriber | MQTT broker port | `1883` |
| `PUBLISH_INTERVAL` | Publisher | Seconds between publish cycles | `2` |
| `NUM_SENSORS` | Publisher | Number of simulated sensors | `100` |
| `DB_PATH` | Subscriber | SQLite file path | `sensors.db` |
| `WEB_PORT` | Subscriber | Flask server port | `8000` |
| `REFRESH_INTERVAL` | Subscriber | Dashboard auto-refresh (seconds) | `1` |

---

## 📡 MQTT Details

| Property | Value |
|---|---|
| Topic | `5/telemetry` |
| QoS | 1 (at least once) |
| Payload format | JSON |
| Broker | Eclipse Mosquitto (anonymous, no TLS) |

**Example payload:**

```json
{
  "sensor_id": "sensor_42",
  "values": {
    "temperature": 23.15,
    "humidity": 61.40,
    "light": 412.00
  },
  "unit": "metric",
  "timestamp": "2025-04-20T14:32:01+00:00"
}
```

---

## 🗄️ Database Schema

```sql
CREATE TABLE readings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id   TEXT,
    timestamp   TEXT,
    temperature REAL,
    humidity    REAL,
    light       REAL
);
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web dashboard (accepts `?sensor_id=sensor_1`) |
| `GET` | `/api/stats/<sensor_id>` | JSON stats + last 50 readings for a sensor |

**Example API response:**

```json
{
  "count": 312,
  "timestamp": "2025-04-20T14:32:01+00:00",
  "readings": {
    "temperature": 23.15,
    "humidity": 61.40,
    "light": 412.00
  },
  "history": [ ... ]
}
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Messaging | [Eclipse Mosquitto](https://mosquitto.org/) + [Paho-MQTT](https://pypi.org/project/paho-mqtt/) |
| Backend | Python 3.14, Flask |
| Database | SQLite 3 |
| Frontend | Vanilla JS + [Chart.js](https://www.chartjs.org/) |
| Containers | Docker, Docker Compose |

---

## 🔒 Production Considerations

This project is configured for development. Before deploying to production:

- [ ] Enable MQTT TLS encryption (`port 8883`)
- [ ] Add username/password authentication to Mosquitto
- [ ] Replace SQLite with PostgreSQL or TimescaleDB for high write throughput
- [ ] Add data retention policy (e.g. auto-delete records older than 30 days)
- [ ] Set up alerting for threshold breaches (e.g. temperature > 35°C)

---

## 📄 License

MIT
