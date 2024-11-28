from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route("/notify", methods=["POST"])
def notify():
    # Get the notification payload
    data = request.json
    print("Notification received:")
    print(json.dumps(data, indent=2))
    
    # Extract the data from the notification
    for entity in data.get("data", []):
        if entity["type"] == "ground_station":
            print(f"Station ID: {entity['id']}")
            print(f"AQI: {entity['aqi']['value']}")
            print(f"Latitude: {entity['latitude']['value']}")
            print(f"Longitude: {entity['longitude']['value']}")
            print(f"Timestamp: {entity['timestamp']['value']}")
    
    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
