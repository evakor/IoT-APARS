import paho.mqtt.client as mqtt
import requests
import logging
import logging.config
import json
import os
from dotenv import load_dotenv

load_dotenv()

class CarMQTTListener:
    def __init__(self):
        self.broker_address = os.getenv('MQTT_ADDRESS')
        self.broker_port = int(os.getenv('MQTT_PORT'))
        self.topics = ["apars_cars"]
        self.orion_url = os.getenv('ORION_URL') + "/entities"

        logging.config.fileConfig('../../../logging.conf')
        self.logger = logging.getLogger("MQTT-To-Orion")

        self.client = mqtt.Client()
        self.client.username_pw_set("user", "password")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("Connected to MQTT broker successfully!")
            for topic in self.topics:
                client.subscribe(topic)
                self.logger.info(f"Subscribed to topic: {topic}")
        else:
            self.logger.error(f"Failed to connect to MQTT broker, return code {rc}")

    def on_message(self, client, userdata, msg):
        self.logger.info(f"Message received from topic {msg.topic}")
        try:
            payload = msg.payload.decode("utf-8")
            self.logger.info(f"Payload: {payload}")
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
                self.logger.info(f"Data updated successfully! CAR ID: {entity_id}")
            elif response.status_code == 404:
                response = requests.post(self.orion_url, headers=headers, json=data)
                if response.status_code == 201:
                    self.logger.info(f"Data created successfully! CAR ID: {entity_id}")
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
            "dateObserved": {"type": "DateTime", "value": payload[1]},   
            "co": {"type": "Float", "value": 10.0}, 
            "co2": {"type": "Float", "value": 10.0},
            "pm1": {"type": "Float", "value": payload[5]},
            "pm25": {"type": "Float", "value": payload[6]},
            "pm10": {"type": "Float", "value": payload[7]},
            "oxidised": {"type": "Float", "value": payload[4]},
            "reduced": {"type": "Float", "value": payload[8]},
            "nh3": {"type": "Float", "value": payload[9]},
            "location": {
                "type": "geo:json",
                "value": {"type": "Point", "coordinates": [payload[2], payload[3]]}
            }
        }

    def listen(self):
        try:
            self.client.connect(self.broker_address, self.broker_port)
            self.client.loop_start()
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {str(e)}")
