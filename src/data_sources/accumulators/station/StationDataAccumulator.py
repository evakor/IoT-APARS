# In this script data gets fetched from an API or the universities lab and then passed to the context broker
# TODO: In production this service will get triggerd every 1 hour. There will also be a function that will chech if the station
#       exists in the database. If it exists, then it will update it. Otherwise it will post the new station

import os
import json
import requests
import logging
import logging.config

logging.config.fileConfig('../logging.conf')
logger = logging.getLogger('STATION_DATA')

# Greece
lat_min, lat_max = 34.8021, 41.7489
lon_min, lon_max = 19.3646, 29.6425

# World
lat_min, lat_max = -90, 90
lon_min, lon_max = -180, 180

apiToken = 'ecaa84eb1dbceeaf83c27c213369e4cf372c03c8'
url = f"https://api.waqi.info/map/bounds/?token={apiToken}&latlng={lat_min},{lon_min},{lat_max},{lon_max}"

ORION_URL = "http://localhost:1026/v2/entities"


def load_data(data_file):
    if os.path.exists(data_file):
        with open(data_file, "r") as file:
            data = json.load(file)
        return data, "Fetched from local file"
    else:
        logger.info("Fetching data...")
        try:
            response = requests.get(url)
            data = response.json()['data']
            with open(data_file, "w") as file:
                json.dump(data, file)
            return data, "Fetched from api"
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            return None, f"An error occurred: {str(e)}"


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

if __name__=="__main__":
    data_file = "station_aqi_data.json"

    data, message = load_data(data_file)

    logger.info(message)

    for station in data:
        payload = {
            "id": f"station_{station["uid"]}",
            "type": "ground_station",
            "timestamp": {
                "type": "DateTime",
                "value": station["station"]["time"]
            },
            "latitude": {
                "type": "Float",
                "value": station["lat"]
            },
            "longitude": {
                "type": "Float",
                "value": station["lon"]
            },
            "aqi": {
                "type": "Integer",
                "value": station["aqi"]
            }
        }

        send_data_to_orion(payload)