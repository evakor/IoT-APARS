import paho.mqtt.client as mqtt
import ssl
import time
import base64
from PIL import Image

broker = "labserver.sense-campus.gr"
port = 9002
topic = "image"

client = mqtt.Client(transport="websockets")

# Enable SSL/TLS
client.tls_set()  # Use system's CA certificates

# For debugging self-signed certificates, uncomment the following:
# client.tls_insecure_set(True)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe(topic)
    else:
        print(f"Connection failed with code {rc}")

def on_publish(client, userdata, mid):
    print(f"Message {mid} published successfully.")

client.on_connect = on_connect
client.on_publish = on_publish

try:
    client.connect(broker, port, 60)
    client.loop_start()

    while True:
        with Image.open("heatmap.png") as img:
            flipped_img = img.transpose(Image.FLIP_TOP_BOTTOM)
            flipped_img.save("flipped_heatmap.png")

        with open("flipped_heatmap.png", "rb") as image_file:
            message = base64.b64encode(image_file.read()).decode("utf-8")

        result = client.publish(topic, message)
        result.wait_for_publish()

        time.sleep(20)

except ssl.SSLError as e:
    print(f"SSL Error: {e}")

except KeyboardInterrupt:
    print("Disconnected.")
    client.disconnect()
    client.loop_stop()
