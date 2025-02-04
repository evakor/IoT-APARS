import json
import os
import logging
import logging.config
from datetime import datetime, timedelta
import pytz
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from paho.mqtt.client import Client
from dotenv import load_dotenv
import Converters as c

load_dotenv()

logging.basicConfig(level=logging.INFO)
logging.config.fileConfig('../../logging.conf')

class WebhookBase:
    def __init__(self, topic, measurement, logger_name):
        self.logger = logging.getLogger(logger_name)
        self.topic = topic
        self.measurement = measurement
        self.client = InfluxDBClient(url=os.getenv("INFLUX_URL"), token=os.getenv('GRAFANA_READ_AND_WRITE'), org='students')
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.mqtt_client = Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(os.getenv("MQTT_ADDRESS"), int(os.getenv("MQTT_PORT")), 60)
        self.converter = c.Converters()

    def toUTC(self, timestamp):
        if timestamp.endswith("Z"):
            utc_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
            adjusted_time = utc_time - timedelta(hours=2)
            return adjusted_time.isoformat(timespec='microseconds')
        else:
            local_time = datetime.fromisoformat(timestamp)
            utc_plus_2 = pytz.timezone('Europe/Athens')
            localized_time = utc_plus_2.localize(local_time)
            utc_time = localized_time.astimezone(pytz.utc)
            return utc_time.replace(tzinfo=None).isoformat(timespec='microseconds')

    def send_to_influxdb(self, data):
        raise NotImplementedError("Subclasses must implement this method")

    def on_connect(self, client, userdata, flags, rc):
        self.logger.info(f"Connected to MQTT broker with result code {rc}")
        client.subscribe(self.topic)
        self.logger.info(f"Subscribed to topic: {self.topic}")

    def on_message(self, client, userdata, msg):
        self.logger.info(f"Received MQTT message on topic {msg.topic}: {msg.payload.decode()}")
        try:
            data = json.loads(msg.payload.decode())
            self.send_to_influxdb(data)
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")

    def listen(self):
        self.mqtt_client.loop_forever()

class CarWebhook(WebhookBase):
    def __init__(self):
        super().__init__(topic="apars/car", measurement="car_metrics", logger_name="CAR-WEBHOOK")

    def send_to_influxdb(self, data):
        try:
            payload = data["data"][0]
            max_aqi = 0
            for param in ['pm1', 'pm25', 'pm10', 'benzene', 'co', 'nh3', 'co2']: # ['pm1', 'pm25', 'pm10', 'lpg', 'benzene', 'co', 'oxidised', 'reduced', 'nh3', 'co2']
                payload[param]['value'] = self.converter.getAQI(param, payload[param]['value'])
                if payload[param]['value'] is None:
                    payload[param]['value'] = 10
                if payload[param]['value'] >= max_aqi:
                    max_aqi = payload[param]['value']

            point = Point(self.measurement) \
                .tag("id", str(payload['id'])) \
                .field("temperature", float(payload['temperature']['value'])) \
                .field("humidity", float(payload['humidity']['value'])) \
                .field("pressure", float(payload['pressure']['value'])) \
                .field("pm1", float(payload['pm1']['value'])) \
                .field("pm25", float(payload['pm25']['value'])) \
                .field("pm10", float(payload['pm10']['value'])) \
                .field("lpg", float(payload['lpg']['value'])) \
                .field("benzene", float(payload['benzene']['value'])) \
                .field("co", float(payload['co']['value'])) \
                .field("oxidised", float(payload['oxidised']['value'])) \
                .field("reduced", float(payload['reduced']['value'])) \
                .field("nh3", float(payload['nh3']['value'])) \
                .field("co2", float(payload['co2']['value'])) \
                .field("eco2", float(payload['eco2']['value'])) \
                .field("tvoc", float(payload['tvoc']['value'])) \
                .field("aqi", int(max_aqi)) \
                .time(self.toUTC(payload['dateObserved']['value'])) \
                .field("latitude", float(payload['location']['value']['coordinates'][0])) \
                .field("longitude", float(payload['location']['value']['coordinates'][1]))

            self.write_api.write(bucket='APARS', org='students', record=point)
            self.logger.info(f"Data for ID '{payload['id']}' successfully written to InfluxDB under measurement '{self.measurement}'.")
        except Exception as e:
            self.logger.error(f"Failed to write data to InfluxDB: {str(e)}")

class StationWebhook(WebhookBase):
    def __init__(self):
        super().__init__(topic="apars/station/waqi", measurement="station_aqi", logger_name="STATION-WEBHOOK")

    def send_to_influxdb(self, data):
        try:
            payload = data["data"][0]
            point = Point(self.measurement) \
                .tag("id", str(payload['id'])) \
                .field("aqi", int(payload['aqi']['value'])) \
                .time(self.toUTC(payload['dateObserved']['value'])) \
                .field("latitude", float(payload['location']['value']['coordinates'][0])) \
                .field("longitude", float(payload['location']['value']['coordinates'][1]))

            self.write_api.write(bucket='APARS', org='students', record=point)
            self.logger.info(f"Data for ID '{payload['id']}' successfully written to InfluxDB under measurement '{self.measurement}'.")
        except Exception as e:
            self.logger.error(f"Failed to write data to InfluxDB: {str(e)}")

class PatrasStationWebhook(WebhookBase):
    def __init__(self):
        super().__init__(topic="apars/station/patras", measurement="patras_station_aqi", logger_name="STATION-PATRAS-WEBHOOK")

    def send_to_influxdb(self, data):
        try:
            payload = data["data"][0]
            point = Point(self.measurement) \
                .tag("id", str(payload['id'])) \
                .field("aqi", self.converter.getAQI('pm25', payload['pm25']['value'])) \
                .field("pm25", int(payload['pm25']['value'])) \
                .time(self.toUTC(payload['dateObserved']['value'])) \
                .field("latitude", float(payload['location']['value']['coordinates'][0])) \
                .field("longitude", float(payload['location']['value']['coordinates'][1]))

            self.write_api.write(bucket='APARS', org='students', record=point)
            self.logger.info(f"Data for ID '{payload['id']}' successfully written to InfluxDB under measurement '{self.measurement}'.")
        except Exception as e:
            self.logger.error(f"Failed to write data to InfluxDB: {str(e)}")

if __name__ == '__main__':
    car_webhook = CarWebhook()
    station_webhook = StationWebhook()
    patras_station_webhook = PatrasStationWebhook()

    car_webhook.listen()
    station_webhook.listen()
    patras_station_webhook.listen()
