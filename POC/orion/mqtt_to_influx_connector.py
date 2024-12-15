import paho.mqtt.client as mqtt
import requests
import json

# InfluxDB Configuration
INFLUXDB_URL = "http://labserver.sense-campus.gr:8086/api/v2/write"
ORG = "students"  # Your InfluxDB organization
BUCKET = "OMADA 13- APARS"  # Replace with your bucket name
TOKEN = "Jr1yuGJCjKbFPip_9wnl9ZY98nUQ9AhR4WEu5ITQf155GyTDuH6WSfyBQn1PuTjY1kNmW_9d2dnJ3_AJEval3A=="  # Replace with your read/write token

# MQTT Broker Configuration
MQTT_BROKER = "labserver.sense-campus.gr"  # Lab's MQTT broker
MQTT_PORT = 1883  # Default MQTT port
MQTT_TOPIC = "lab/sensors/#"  # Topic to subscribe to (replace with the actual topic)

def write_to_influx(measurement, fields, tags=None):
    """
    Write data to InfluxDB in line protocol format.
    """
    tags_line = ",".join([f"{k}={v}" for k, v in (tags or {}).items()])
    fields_line = ",".join([f"{k}={v}" for k, v in fields.items()])
    line = f"{measurement},{tags_line} {fields_line}"
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "text/plain"
    }
    params = {
        "org": ORG,
        "bucket": BUCKET,
        "precision": "s"
    }
    response = requests.post(INFLUXDB_URL, headers=headers, params=params, data=line)
    if response.status_code == 204:
        print("Data written to InfluxDB")
    else:
        print(f"Failed to write to InfluxDB: {response.text}")

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    """
    Callback when the MQTT client connects to the broker.
    """
    print(f"Connected to MQTT Broker with code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    """
    Callback when a message is received from the MQTT broker.
    """
    print(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

    try:
        # Parse the MQTT message payload
        data = json.loads(msg.payload.decode())
        
        # Example: Assume payload contains temperature and humidity
        fields = {
            "temperature": data.get("temperature", 0),
            "humidity": data.get("humidity", 0)
        }
        tags = {"sensor_id": data.get("sensor_id", "unknown")}
        
        # Write to InfluxDB
        write_to_influx(measurement="sensor_data", fields=fields, tags=tags)
    except json.JSONDecodeError:
        print("Failed to parse JSON payload")

# Main Function
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()
