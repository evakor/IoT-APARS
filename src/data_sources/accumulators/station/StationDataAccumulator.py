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


def send_data_to_orion(entity_id, timestamp, latitude, longitude, aqi):
    headers = {
        "Content-Type": "application/json"
        # "Fiware-Service": "openiot",
        # "Fiware-ServicePath": "/"
    }
    
    data = {
        "id": f"station_{entity_id}",
        "type": "ground_station",
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
        logger.info(f"Data posted successfully! STATION ID: station_{entity_id}")
    elif response.status_code == 422 and eval(response.text)["description"] == "Already Exists":
        response = requests.patch(ORION_URL, headers=headers, data=json.dumps(data))
        logger.info(f"Data updated successfully! STATION ID: station_{entity_id}")
    else:
        logger.error(f"Failed to send data: {response.status_code} - {response.text}")

if __name__=="__main__":
    data_file = "station_aqi_data.json"

    data, message = load_data(data_file)

    logger.info(message)

    for station in data:
        send_data_to_orion(
            station["uid"], 
            station["station"]["time"], 
            station["lat"], 
            station["lon"], 
            station["aqi"]
        )