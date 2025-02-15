import json
import os
import logging
import logging.config
from datetime import datetime, timedelta
import pytz
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from paho.mqtt.client import Client
from dotenv import load_dotenv
from utils.Converters import Converters

load_dotenv()

class WebhookBase:
    def __init__(self, topic, measurement, logger_name):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_config_path = os.path.join(base_dir, 'logging.conf')

        if os.path.exists(log_config_path):
            logging.config.fileConfig(log_config_path)
        else:
            logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(logger_name)
        self.topic = topic
        self.measurement = measurement
        self.client = InfluxDBClient(url=os.getenv("INFLUX_URL"), token=os.getenv('GRAFANA_READ_AND_WRITE'), org='students')
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.mqtt_client = Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(os.getenv("MQTT_ADDRESS"), int(os.getenv("MQTT_PORT")), 60)
        self.converter = Converters()


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
        print(f"BASE-WEBHOOK - Connected to MQTT broker with result code {rc}")
        client.subscribe(self.topic)
        print(f"BASE-WEBHOOK - Subscribed to topic: {self.topic}")


    def on_message(self, client, userdata, msg):
        print(f"BASE-WEBHOOK - Received MQTT message on topic {msg.topic}: {msg.payload.decode()}")
        try:
            data = json.loads(msg.payload.decode())
            self.send_to_influxdb(data)
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")


    def listen(self):
        self.mqtt_client.loop_forever()