from flask import Flask, request, jsonify
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import json
from datetime import datetime

from paho.mqtt.client import Client
import threading
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

token = os.getenv('GRAFANA_READ_AND_WRITE')
org = 'students'
bucket = 'OMADA 13- APARS'
client = InfluxDBClient(url=os.getenv("INFLUX_URL"), token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

MQTT_BROKER = os.getenv("MQTT_ADDRESS")
MQTT_PORT = os.getenv("MQTT_PORT")
MQTT_TOPICS = {
    "station": "station",
    "car": "car",
    "satellite": "satellite"
}


def send_to_influxdb(data, measurement):
    point = Point(measurement) \
        .tag("id", data['id'])
    for key, value in data.items():
        if key != 'id':  # Assuming 'id' is used as a tag and not a field
            point.field(key, float(value['value']))
    point.time(datetime.utcnow(), WritePrecision.NS)
    write_api.write(bucket=bucket, org=org, record=point)


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
        

def start_mqtt():
    mqtt_client = Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_forever() 


if __name__ == '__main__':
    start_mqtt()
