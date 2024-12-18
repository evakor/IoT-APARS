from flask import Flask, request, jsonify
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import json
from datetime import datetime
from Converters import Converters

app = Flask(__name__)
conv = Converters()

# InfluxDB 2.0 settings
token = '3C4tpppV6mLJ85ArlFx4Cazj55KnM2xWJcuTnCCZLfsSalCym88_C1tSERzuLUzZ6IWth9Y4_x_tx_FWiq8jNA=='
org = 'students'
bucket = 'OMADA 13- APARS'
client = InfluxDBClient(url="http://labserver.sense-campus.gr:8086", token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)


def send_to_influxdb(data, measurement):
    point = Point(measurement) \
        .tag("id", data['id'])

    for key, value in data.items():
        if key not in ['id', 'type', 'location', 'dateObserved']:
            point.field(key, int(value['value']))
    point.field('lat', data['location']['value']['coordinates'][0])
    point.field('lon', data['location']['value']['coordinates'][0])
    point.time(data['dateObserved']['value'], WritePrecision.NS)
    write_api.write(bucket=bucket, org=org, record=point)


@app.route('/car-data-upload', methods=['POST'])
def car_data():
    data = request.get_json()
    print("Received notification:", json.dumps(data, indent=4))
    for attr in ["co", "co2", "pm1", "pm25", "pm10"]:
        data[attr]['value'] = conv.getAQI(attr, data[attr]['value'])
    send_to_influxdb(data, 'car_metrics')
    return jsonify(success=True), 200


@app.route('/satellite-upload', methods=['POST'])
def handle_satellite_data():
    data = request.get_json()
    print("Received satellite data:", data)
    satellite_data = data['data']
    send_to_influxdb(satellite_data, 'satellite_metrics')
    return jsonify(success=True), 200


@app.route('/station-data-upload', methods=['POST'])
def handle_station_data():
    data = request.get_json()
    print("Received station data:", data)
    station_data = data['data']
    send_to_influxdb(station_data, 'station_metrics')
    return jsonify(success=True), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)  # Changed it from 5000

