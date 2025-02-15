import paho.mqtt.client as mqtt
import requests
import logging
import logging.config
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class CarMQTTListener:
    def __init__(self):
        self.broker_address = os.getenv('MQTT_ADDRESS')
        self.broker_port = int(os.getenv('MQTT_PORT'))
        self.topics = ["apars_cars"]
        self.orion_url = os.getenv('ORION_URL') + "/entities"

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_config_path = os.path.join(base_dir, 'logging.conf')

        if os.path.exists(log_config_path):
            logging.config.fileConfig(log_config_path)
        else:
            logging.basicConfig(level=logging.INFO)

        self.logger = logging.getLogger("CAR-ACCUMULATOR")

        self.client = mqtt.Client()
        self.client.username_pw_set("user", "password")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("CAR-ACCUMULATOR - Connected to MQTT broker successfully!")
            for topic in self.topics:
                client.subscribe(topic)
                print(f"CAR-ACCUMULATOR - Subscribed to topic: {topic}")
        else:
            self.logger.error(f"Failed to connect to MQTT broker, return code {rc}")

    def on_message(self, client, userdata, msg):
        print(f"CAR-ACCUMULATOR - Message received from topic {msg.topic}")
        try:
            payload = msg.payload.decode("utf-8")
            print(f"CAR-ACCUMULATOR - Payload: {payload}")
            self.send_data_to_orion(payload)
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")

    def send_data_to_orion(self, payload):
        headers = {"Content-Type": "application/json"}
        try:
            data = self.to_orion_format(payload)
            entity_id = data["id"]
            url = f"{self.orion_url}/{entity_id}/attrs"

            response = requests.patch(url, headers=headers, json={k: v for k, v in data.items() if k not in ["id", "type"]})

            if response.status_code == 204:
                print(f"CAR-ACCUMULATOR - Data updated successfully! CAR ID: {entity_id}")
            elif response.status_code == 404:
                response = requests.post(self.orion_url, headers=headers, json=data)
                if response.status_code == 201:
                    print(f"CAR-ACCUMULATOR - Data created successfully! CAR ID: {entity_id}")
                else:
                    self.logger.error(f"Failed to create entity: {response.status_code} - {response.text}")
            else:
                self.logger.error(f"Failed to send data: {response.status_code} - {response.text}")
        except Exception as e:
            self.logger.error(f"Error sending data to Orion: {str(e)}")

    def to_orion_format(self, payload):
        payload = list(json.loads(payload))
        return {
            "id": payload[0],
            "type": "CarAirQualityObserved",
            "dateObserved": {"type": "DateTime", "value": datetime.now().isoformat()}, #payload[1]
            "temperature": {"type": "Float", "value": payload[4]},
            "humidity": {"type": "Float", "value": payload[5]},
            "pressure": {"type": "Float", "value": payload[6]},
            "pm1": {"type": "Float", "value": payload[7]},
            "pm25": {"type": "Float", "value": payload[8]},
            "pm10": {"type": "Float", "value": payload[9]},
            "lpg": {"type": "Float", "value": payload[10]},
            "benzene": {"type": "Float", "value": payload[11]},
            "co": {"type": "Float", "value": payload[12]},
            "oxidised": {"type": "Float", "value": payload[13]},
            "reduced": {"type": "Float", "value": payload[14]},
            "nh3": {"type": "Float", "value": payload[15]},
            "co2": {"type": "Float", "value": payload[16]},
            "eco2": {"type": "Float", "value": payload[17]},
            "tvoc": {"type": "Float", "value": payload[18]},
            "location": {
                "type": "geo:json",
                "value": {
                    "type": "Point",
                    "coordinates": [payload[2], payload[3]]
                }
            }
        }

    def listen(self):
        try:
            self.client.connect(self.broker_address, self.broker_port)
            self.client.loop_forever()
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {str(e)}")
            self.logger.error(f"Failed to connect to MQTT broker: {str(e)}")
