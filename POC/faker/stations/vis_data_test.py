import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import json

# MQTT configuration
MQTT_BROKER = "150.140.186.118"
MQTT_PORT = 1883
MQTT_TOPIC = "your_topic_here"  # Replace with the actual topic name

# Initialize plot data
payload_data = {'temperature': 0, 'pressure': 0, 'humidity': 0, 'oxidised': 0, 'reduced': 0, 'nh3': 0, 'lux': 0, 'pm1': 0, 'pm25': 0, 'pm10': 0}

# Callback when a message is received
def on_message(client, userdata, msg):
    global payload_data
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        if isinstance(payload, dict):
            payload_data = payload
    except json.JSONDecodeError:
        print("Failed to decode JSON payload")

# MQTT client setup
client = mqtt.Client()
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPIC)

# Plot setup
fig, ax = plt.subplots()
bars = ax.bar(payload_data.keys(), payload_data.values())

def update_plot(frame):
    global payload_data
    for bar, new_value in zip(bars, payload_data.values()):
        bar.set_height(new_value)
    ax.set_ylim(0, max(payload_data.values()) * 1.2)
    ax.set_title("Live MQTT Data")

# Run MQTT loop in a separate thread
client.loop_start()

# Set up animation
ani = FuncAnimation(fig, update_plot, interval=1000)
plt.show()

# Stop MQTT loop on exit
client.loop_stop()
