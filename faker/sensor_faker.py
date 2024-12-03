import time
import random
import requests

# Configuration
INFLUXDB_URL = "http://labserver.sense-campus.gr:8086/api/v2/write"
ORG = "students"  # Provided organization
BUCKET = "OMADA 13- APARS"  # Replace with your bucket name
TOKEN = "Jr1yuGJCjKbFPip_9wnl9ZY98nUQ9AhR4WEu5ITQf155GyTDuH6WSfyBQn1PuTjY1kNmW_9d2dnJ3_AJEval3A=="  # Replace with your read/write token

# Generate fake data and write to InfluxDB
def write_fake_data():
    while True:
        # Generate random sensor values
        temperature = random.uniform(20.0, 30.0)
        humidity = random.uniform(30.0, 60.0)

        # Create InfluxDB line protocol data
        data = f"sensor_data temperature={temperature},humidity={humidity}"

        # Make the API request
        headers = {
            "Authorization": f"Token {TOKEN}",
            "Content-Type": "text/plain"
        }
        params = {
            "org": ORG,
            "bucket": BUCKET,
            "precision": "s"
        }
        response = requests.post(INFLUXDB_URL, headers=headers, params=params, data=data)

        if response.status_code == 204:
            print("Data written successfully")
        else:
            print(f"Failed to write data: {response.text}")

        # Wait 10 seconds before sending the next batch
        time.sleep(10)


if __name__ == "__main__":
    write_fake_data()
