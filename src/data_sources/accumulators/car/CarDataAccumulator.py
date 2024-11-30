import paho.mqtt.client as mqtt
import requests
import logging
import json

# Constants
BROKER_ADDRESS = "localhost"
BROKER_PORT = 1883
TOPICS = ["car_1", "car_2", "car_3"]
ORION_URL = "http://localhost:1026/v2/entities"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MQTT-To-Orion")

def send_data_to_orion(payload):
    """Send data to Orion Context Broker."""
    headers = {
        "Content-Type": "application/json"
    }
    try:
        data = json.loads(payload)
        entity_id = data["id"]

        url = f"{ORION_URL}/{entity_id}/attrs"

        response = requests.patch(url, headers=headers, json={key: value for key, value in data.items() if key not in ["id", "type"]})

        if response.status_code == 204:
            logger.info(f"Data updated successfully! CAR ID: {entity_id}")
        elif response.status_code == 404:  # Entity not found, create it
            response = requests.post(ORION_URL, headers=headers, json=data)
            if response.status_code == 201:
                logger.info(f"Data created successfully! CAR ID: {entity_id}")
            else:
                logger.error(f"Failed to create entity: {response.status_code} - {response.text}")
        else:
            logger.error(f"Failed to send data: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error while sending data to Orion: {str(e)}")


# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker successfully!")
        # Subscribe to all topics in the list
        for topic in TOPICS:
            client.subscribe(topic)
            logger.info(f"Subscribed to topic: {topic}")
    else:
        logger.error(f"Failed to connect to MQTT broker, return code {rc}")

def on_message(client, userdata, msg):
    logger.info(f"Message received from topic {msg.topic}")
    try:
        payload = msg.payload.decode("utf-8")
        logger.info(f"Payload: {payload}")
        send_data_to_orion(payload)
    except Exception as e:
        logger.error(f"Error processing message from topic {msg.topic}: {str(e)}")



if __name__ == "__main__":
    client = mqtt.Client()
    client.username_pw_set("user", "password")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER_ADDRESS, BROKER_PORT)
    except Exception as e:
        logger.error(f"Failed to connect to MQTT broker: {str(e)}")
        quit()

    client.loop_forever()