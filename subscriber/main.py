import os
import threading

from database import get_all_sensors, get_sensor_stats, init_db
from flask import Flask, jsonify, render_template_string, request
from mqtt_handler import run_mqtt

WEB_PORT = int(os.environ.get("WEB_PORT", 8000))
REFRESH_INTERVAL = int(os.environ.get("PUBLISH_INTERVAL", 1))

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>MQTT Sensor Stats</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: sans-serif; background-color: #f4f4f9; display: flex; flex-direction: column; align-items: center; min-height: 100vh; margin: 0; padding: 2rem; }
        .card { background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%; max-width: 400px; margin-bottom: 2rem; }
        .chart-container { display: flex; flex-direction: column; align-items: center; gap: 2rem; width: 100%; max-width: 800px; }
        .chart-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%; height: 350px; display: flex; flex-direction: column; }
        .chart-card h3 { margin-top: 0; font-size: 1rem; color: #555; }
        .chart-card canvas { flex: 1; min-height: 0; }
        h1 { color: #333; font-size: 1.5rem; margin-bottom: 2rem; }
        h2 { color: #555; font-size: 1.2rem; border-bottom: 2px solid #eee; padding-bottom: 0.5rem; margin-top: 0; }
        .stat { margin: 1rem 0; display: flex; justify-content: space-between; }
        .label { font-weight: bold; color: #666; }
        .value { color: #007bff; font-family: monospace; font-size: 1.2rem; }
        .footer { font-size: 0.8rem; color: #999; margin-top: 1.5rem; border-top: 1px solid #eee; padding-top: 0.5rem; }
        select { padding: 0.5rem 1rem; border-radius: 4px; border: 1px solid #ccc; font-size: 1rem; margin-bottom: 2rem; width: 100%; max-width: 400px; }
    </style>
</head>
<body>
    <h1>MQTT Sensor Dashboard</h1>

    <select id="sensor-select" onchange="changeSensor(this.value)">
        <option value="" {% if not selected_sensor %}disabled selected{% endif %}>Select a sensor...</option>
        {% for s_id in all_sensors %}
        <option value="{{ s_id }}" {% if s_id == selected_sensor %}selected{% endif %}>{{ s_id }}</option>
        {% endfor %}
    </select>

    <div class="card" id="sensor-card" {% if not stats %}style="display: none;"{% endif %}>
        <h2 id="sensor-name">{{ selected_sensor }}</h2>
        <div class="stat">
            <span class="label">Temperature:</span>
            <span class="value"><span id="temp-val">{{ stats.readings.temperature | default(0) | round(2) if stats else 0 }}</span> °C</span>
        </div>
        <div class="stat">
            <span class="label">Humidity:</span>
            <span class="value"><span id="hum-val">{{ stats.readings.humidity | default(0) | round(2) if stats else 0 }}</span> %</span>
        </div>
        <div class="stat">
            <span class="label">Light:</span>
            <span class="value"><span id="light-val">{{ stats.readings.light | default(0) | round(2) if stats else 0 }}</span> lux</span>
        </div>
        <div class="stat">
            <span class="label">Messages Received:</span>
            <span class="value" id="msg-count">{{ stats.count if stats else 0 }}</span>
        </div>
        <div class="footer">
            Last Updated: <span id="last-updated">{{ stats.timestamp if stats else 'N/A' }}</span>
        </div>
    </div>

    <div class="chart-container" id="chart-container" {% if not stats %}style="display: none;"{% endif %}>
        <div class="chart-card">
            <h3>Temperature (°C)</h3>
            <canvas id="temp-chart"></canvas>
        </div>
        <div class="chart-card">
            <h3>Humidity (%)</h3>
            <canvas id="hum-chart"></canvas>
        </div>
        <div class="chart-card">
            <h3>Light (lux)</h3>
            <canvas id="light-chart"></canvas>
        </div>
    </div>

    <div class="card" id="no-data-card" {% if stats %}style="display: none;"{% endif %} style="text-align: center;">
        <p>No sensor selected or no data received yet.</p>
    </div>

    <script>
        const REFRESH_INTERVAL = {{ refresh_interval }} * 1000;
        let SELECTED_SENSOR = "{{ selected_sensor }}";
        let refreshTimer = null;
        let charts = {};

        function initCharts() {
            const chartConfigs = [
                { id: 'temp-chart', label: 'Temp (°C)', color: '#ff6384' },
                { id: 'hum-chart', label: 'Humidity (%)', color: '#36a2eb' },
                { id: 'light-chart', label: 'Light (lux)', color: '#ffce56' }
            ];

            chartConfigs.forEach(cfg => {
                const ctx = document.getElementById(cfg.id).getContext('2d');
                charts[cfg.id] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: cfg.label,
                            borderColor: cfg.color,
                            backgroundColor: cfg.color + '22',
                            data: [],
                            fill: true,
                            tension: 0.3,
                            pointRadius: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: {
                                display: true,
                                ticks: {
                                    autoSkip: true,
                                    maxTicksLimit: 10
                                }
                            },
                            y: { beginAtZero: false }
                        },
                        animation: false,
                        plugins: { legend: { display: false } }
                    }
                });
            });
        }

        async function updateStats() {
            if (!SELECTED_SENSOR) return;

            try {
                const response = await fetch(`/api/stats/${SELECTED_SENSOR}`);
                if (!response.ok) throw new Error('Sensor not found');
                const stats = await response.json();

                if (stats) {
                    document.getElementById('sensor-name').textContent = SELECTED_SENSOR;
                    document.getElementById('temp-val').textContent = stats.readings.temperature.toFixed(2);
                    document.getElementById('hum-val').textContent = stats.readings.humidity.toFixed(2);
                    document.getElementById('light-val').textContent = stats.readings.light.toFixed(2);
                    document.getElementById('msg-count').textContent = stats.count;
                    document.getElementById('last-updated').textContent = stats.timestamp;

                    document.getElementById('sensor-card').style.display = 'block';
                    document.getElementById('chart-container').style.display = 'flex';
                    document.getElementById('no-data-card').style.display = 'none';

                    if (Object.keys(charts).length === 0) initCharts();

                    if (stats.history) {
                        const labels = stats.history.map(h => {
                            // Extract HH:MM:SS from ISO timestamp
                            const t = h.timestamp.split('T');
                            return t.length > 1 ? t[1].split('+')[0] : h.timestamp;
                        });

                        charts['temp-chart'].data.labels = labels;
                        charts['temp-chart'].data.datasets[0].data = stats.history.map(h => h.temperature);
                        charts['temp-chart'].update();

                        charts['hum-chart'].data.labels = labels;
                        charts['hum-chart'].data.datasets[0].data = stats.history.map(h => h.humidity);
                        charts['hum-chart'].update();

                        charts['light-chart'].data.labels = labels;
                        charts['light-chart'].data.datasets[0].data = stats.history.map(h => h.light);
                        charts['light-chart'].update();
                    }
                }
            } catch (error) {
                console.error('Error fetching stats:', error);
            }
        }

        function changeSensor(sensorId) {
            SELECTED_SENSOR = sensorId;
            const newurl = window.location.protocol + "//" + window.location.host + window.location.pathname + '?sensor_id=' + sensorId;
            window.history.pushState({path:newurl}, '', newurl);

            updateStats();

            if (!refreshTimer) {
                refreshTimer = setInterval(updateStats, REFRESH_INTERVAL);
            }
        }

        if (SELECTED_SENSOR) {
            refreshTimer = setInterval(updateStats, REFRESH_INTERVAL);
            updateStats(); // Initial fetch
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    selected_sensor = request.args.get("sensor_id")
    all_sensors = get_all_sensors()

    # Default to first sensor if none selected and sensors exist
    if not selected_sensor and all_sensors:
        selected_sensor = all_sensors[0]

    stats = get_sensor_stats(selected_sensor) if selected_sensor else None

    return render_template_string(
        HTML_TEMPLATE,
        all_sensors=all_sensors,
        selected_sensor=selected_sensor,
        stats=stats,
        refresh_interval=REFRESH_INTERVAL,
    )


@app.route("/api/stats/<sensor_id>")
def get_stats(sensor_id):
    stats = get_sensor_stats(sensor_id)
    if stats:
        return jsonify(stats)
    return jsonify({"error": "Sensor not found"}), 404


if __name__ == "__main__":
    # Initialize the database
    init_db()

    # Start MQTT client in a background thread
    mqtt_thread = threading.Thread(target=run_mqtt, daemon=True)
    mqtt_thread.start()

    # Start Flask web server
    print(f"Starting web app on http://localhost:{WEB_PORT}")
    app.run(host="0.0.0.0", port=WEB_PORT)
