import requests
import json
from datetime import datetime

# Orion Context Broker URL
ORION_URL = "http://localhost:1026/v2/entities"

# Function to send data
def send_data_to_orion(entity_id, timestamp, latitude, longitude, aqi):
    headers = {
        "Content-Type": "application/json"
        # "Fiware-Service": "openiot",
        # "Fiware-ServicePath": "/"
    }
    
    data = {
        "id": f"GridStationAQI_{entity_id}",
        "type": "GridStationAQI",
        "timestamp": {
            "type": "DateTime",
            "value": timestamp
        },
        "latitude": {
            "type": "Float",
            "value": latitude
        },
        "longitude": {
            "type": "Float",
            "value": longitude
        },
        "aqi": {
            "type": "Integer",
            "value": aqi
        }
    }

    response = requests.post(ORION_URL, headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        print("Data sent successfully!")
    else:
        print(f"Failed to send data: {response.status_code} - {response.text}")

# Example Usage
if __name__ == "__main__":
    # Example data
    entity_id = 1
    timestamp = datetime.now().isoformat()
    latitude = 37.9838
    longitude = 23.7275
    aqi = 85
    
    send_data_to_orion(entity_id, timestamp, latitude, longitude, aqi)
