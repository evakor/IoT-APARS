from flask import Flask, request, jsonify
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import json
from datetime import datetime

from paho.mqtt.client import Client
import threading


app = Flask(__name__)

#theloume na anoixei ena mqtt apo cb se webhook kai meta na ta stelnei influx

# InfluxDB 2.0 settings
token = '3C4tpppV6mLJ85ArlFx4Cazj55KnM2xWJcuTnCCZLfsSalCym88_C1tSERzuLUzZ6IWth9Y4_x_tx_FWiq8jNA=='
org = 'students'
bucket = 'OMADA 13- APARS'
client = InfluxDBClient(url="http://labserver.sense-campus.gr:8086", token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# MQTT settings
MQTT_BROKER = "apars-greece-mqtt-broker"
MQTT_PORT = 1883
MQTT_TOPICS = {
    "car": "car/data",
    "satellite": "satellite/data",
    "station": "station/data"
}

# def send_to_influxdb(data):
#     point = Point("car_metrics") \
#         .tag("car_id", data['id']) \
#         .field("latitude", float(data["latitude"]["value"])) \
#         .field("longitude", float(data["longitude"]["value"])) \
#         .field("oxidised", float(data["oxidised"]["value"])) \
#         .field("pm1", float(data["pm1"]["value"])) \
#         .field("pm25", float(data["pm25"]["value"])) \
#         .field("pm10", float(data["pm10"]["value"])) \
#         .field("reduced", float(data["reduced"]["value"])) \
#         .field("nh3", float(data["nh3"]["value"])) \
#         .time(datetime.utcnow(), WritePrecision.NS)

#     write_api.write(bucket=bucket, org=org, record=point)d

# @app.route('/notifications', methods=['POST'])
# def handle_notification():
#     # Get the JSON data sent to the endpoint
#     data = request.get_json()
#     print("Received notification:", json.dumps(data, indent=4))
    
#     # Access the 'data' field directly
#     car_data = data['data']
    
#     # Pass this data to the function that handles database insertion
#     send_to_influxdb(car_data)
    
#     return jsonify(success=True), 200

# def send_to_influxdb(data, measurement):
#     point = Point(measurement) \
#         .tag("id", data['id'])
#     for key, value in data.items():
#         if key != 'id':  # Assuming 'id' is used as a tag and not a field
#             point.field(key, float(value['value']))
#     point.time(datetime.utcnow(), WritePrecision.NS)
#     write_api.write(bucket=bucket, org=org, record=point)

# @app.route('/car-data-upload', methods=['POST'])
# def car_data():
#     data = request.get_json()
#     print("Received notification:", json.dumps(data, indent=4))
#     car_data = data['data']
#     send_to_influxdb(car_data, 'car_metrics')
#     return jsonify(success=True), 200

# @app.route('/satellite-upload', methods=['POST'])
# def handle_satellite_data():
#     data = request.get_json()
#     print("Received satellite data:", data)
#     satellite_data = data['data']
#     send_to_influxdb(satellite_data, 'satellite_metrics')
#     return jsonify(success=True), 200

# @app.route('/station-data-upload', methods=['POST'])
# def handle_station_data():
#     data = request.get_json()
#     print("Received station data:", data)
#     station_data = data['data']
#     send_to_influxdb(station_data, 'station_metrics')
#     return jsonify(success=True), 200

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    # Subscribe to topics
    for topic in MQTT_TOPICS.values():
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")

def on_message(client, userdata, msg):
    print(f"Received MQTT message on topic {msg.topic}: {msg.payload.decode()}")
    try:
        data = json.loads(msg.payload.decode())
        if msg.topic == MQTT_TOPICS["car"]:
            send_to_influxdb(data, 'car_metrics')
        elif msg.topic == MQTT_TOPICS["satellite"]:
            send_to_influxdb(data, 'satellite_metrics')
        elif msg.topic == MQTT_TOPICS["station"]:
            send_to_influxdb(data, 'station_metrics')
    except Exception as e:
        print(f"Error processing MQTT message: {e}")
        
# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5001)  # Changed it from 5000

# Run Flask app and MQTT client concurrently
def start_flask():
    app.run(debug=True, host='0.0.0.0', port=5001)

def start_mqtt():
    mqtt_client = Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever() 


if __name__ == '__main__':
    # Use threading to run Flask and MQTT simultaneously
    flask_thread = threading.Thread(target=start_flask)
    mqtt_thread = threading.Thread(target=start_mqtt)
    flask_thread.start()
    mqtt_thread.start()
    flask_thread.join()
    mqtt_thread.join()
