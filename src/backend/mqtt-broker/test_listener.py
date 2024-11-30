import paho.mqtt.client as mqtt
import json

BROKER_ADDRESS = "localhost"
BROKER_PORT = 1883

# List of topics to listen to
car_topics = [f"car_{i}" for i in range(1, 4)]  # Adjust range as needed

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    if rc == 0:
        print("Connected to MQTT Broker!")
        for topic in car_topics:
            client.subscribe(topic)
            print(f"Subscribed to topic: {topic}")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received."""
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        print(f"Received message on topic {msg.topic}:")
        print(json.dumps(payload, indent=4))
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
    

if __name__ == "__main__":
    # Create MQTT client
    client = mqtt.Client()

    client.username_pw_set("user", "password")

    # Assign callback functions
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to the MQTT broker
    client.connect(BROKER_ADDRESS, BROKER_PORT)

    # Start the MQTT client loop
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Disconnecting from broker...")
        client.disconnect()
