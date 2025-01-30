import os
import json
import requests
import logging
import logging.config
from datetime import datetime
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.config.fileConfig('../../../logging.conf')
logger = logging.getLogger('STATION_DATA')

# Orion Context Broker URL
ORION_URL = os.getenv('ORION_URL') + "/entities"

def fetch_station_data(station_id, token):
    """Fetch station data from the API."""
    url = f"http://labserver.sense-campus.gr:5047/exmi_patras?token={token}&sensorid={station_id}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch data for station {station_id}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error fetching data for station {station_id}: {str(e)}")
        return None

def send_data_to_orion(payload):
    """Send data to Orion Context Broker."""
    headers = {
        "Content-Type": "application/json"
    }
    try:
        entity_id = payload["id"]
        url = f"{ORION_URL}/{entity_id}/attrs"

        response = requests.patch(url, headers=headers, json={key: value for key, value in payload.items() if key not in ["id", "type"]})

        if response.status_code == 204:
            logger.info(f"Data updated successfully! Station ID: {entity_id}")
        elif response.status_code == 404:  # Entity not found, create it
            response = requests.post(ORION_URL, headers=headers, json=payload)
            if response.status_code == 201:
                logger.info(f"Data created successfully! Station ID: {entity_id}")
            else:
                logger.error(f"Failed to create entity: {response.status_code} - {response.text}")
        else:
            logger.error(f"Failed to send data: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error while sending data to Orion: {str(e)}")

def main():
    station_ids = [101589, 105810, 17, 1566, 101609, 47413, 1006, 741, 14857, 56113, 1592, 749, 1712, 116401, 1672]
    token = os.getenv('PATRAS_STATION_TOKEN')

    for station_id in station_ids:
        data = fetch_station_data(station_id, token)

        if data:
            payload = {
                "id": f"patras_station_{station_id}",
                "type": "StationAirQualityObserved",
                "dateObserved": {
                    "type": "DateTime",
                    "value": data.get("date")
                },
                "temperature": {
                    "type": "Float",
                    "value": data.get("temp")
                },
                "humidity": {
                    "type": "Float",
                    "value": data.get("hum")
                },
                "pm25": {
                    "type": "Float",
                    "value": data.get("pm25")
                },
                "location": {
                    "type": "geo:json",
                    "value": {
                        "type": "Point",
                        "coordinates": [
                            float(data.get("lon")),
                            float(data.get("lat"))
                        ]
                    }
                }
            }

            send_data_to_orion(payload)
        
        # Respect the 400ms time limit between API calls
        time.sleep(0.4)

if __name__ == "__main__":
    main()
