from flask import Flask, request, jsonify
import requests

# Webhook handler

app = Flask(__name__)

# InfluxDB Configuration (hosted by lab)
INFLUXDB_URL = "http://labserver.sense-campus.gr:8086/api/v2/write"
ORG = "students"  # Organization provided in instructions
BUCKET = "OMADA 13- APARS"  # Replace with your bucket name
WRITE_TOKEN = "Jr1yuGJCjKbFPip_9wnl9ZY98nUQ9AhR4WEu5ITQf155GyTDuH6WSfyBQn1PuTjY1kNmW_9d2dnJ3_AJEval3A=="  # Replace with your write token

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook to handle notifications from Context Broker and write data to InfluxDB.
    """
    data = request.get_json()

    # Example: Extracting relevant attributes (customize as needed)
    entity = data.get("data", [{}])[0]
    entity_id = entity.get("id", "unknown")
    temperature = entity.get("temperature", {}).get("value", None)
    timestamp = entity.get("temperature", {}).get("metadata", {}).get("timestamp", {}).get("value", None)

    if temperature is not None and timestamp is not None:
        # Format InfluxDB line protocol
        influx_line = f"temperature_data,entity={entity_id} value={temperature} {int(timestamp)}"

        # Write to InfluxDB
        headers = {
            "Authorization": f"Token {WRITE_TOKEN}",
            "Content-Type": "text/plain"
        }
        params = {
            "org": ORG,
            "bucket": BUCKET,
            "precision": "ms"
        }
        response = requests.post(INFLUXDB_URL, headers=headers, params=params, data=influx_line)

        if response.status_code == 204:
            return jsonify({"status": "success", "message": "Data written to InfluxDB"}), 200
        else:
            return jsonify({"status": "error", "message": response.text}), 500
    else:
        return jsonify({"status": "error", "message": "Invalid data"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)