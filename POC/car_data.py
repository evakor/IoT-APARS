# In this script data gets fetched from an API or the universities lab and then passed to the context broker
# TODO: In production this service will get triggerd every 1 hour. There will also be a function that will chech if the station
#       exists in the database. If it exists, then it will update it. Otherwise it will post the new station

import os
import json
import requests
import logging
import logging.config
from datetime import datetime

logging.config.fileConfig('../logging.conf')
logger = logging.getLogger('CAR_DATA')

# Here it will connect with an mqtt broker

ORION_URL = "http://localhost:1026/v2/entities"


def load_data():
    # Sub and get data from car's topic
    dummy_data = {
        "temperature": 23,             # Compensated temperature in degrees Celsius
        "pressure": 101320,            # Pressure in hPa, rounded to the nearest 10
        "humidity": 55,                # Humidity in percentage
        "oxidised": 15,                # Oxidised gas reading (kO)
        "reduced": 10,                 # Reduced gas reading (kO)
        "nh3": 12,                     # NH3 gas reading (kO)
        "lux": 320,                    # Ambient light level (lux)
        "pm1": 5,                      # PM1.0 particle count in µg/m³ (if PMS5003 is connected)
        "pm25": 12,                    # PM2.5 particle count in µg/m³ (if PMS5003 is connected)
        "pm10": 25,                    # PM10 particle count in µg/m³ (if PMS5003 is connected)
        "serial": "000000009abcdef",   # Raspberry Pi serial number (device ID)
        "lat": 35.2342,
        "lon": 24.6357,
    }
    return dummy_data, "No data yet"


def send_data_to_orion(entity_id, timestamp, data):
    headers = {
        "Content-Type": "application/json"
        # "Fiware-Service": "openiot",
        # "Fiware-ServicePath": "/"
    }
    
    data = {
        "id": f"car_{entity_id}",
        "type": "car",
        "timestamp": {
            "type": "DateTime",
            "value": timestamp
        },
        "latitude": {
            "type": "Float",
            "value": float(data["lat"])
        },
        "longitude": {
            "type": "Float",
            "value": float(data["lon"])
        },
        "oxidised": {
            "type": "Float",
            "value": float(data["oxidised"])
        },
        "humidity": {
            "type": "Float",
            "value": float(data["humidity"])
        },
        "temperature": {
            "type": "Float",
            "value": float(data["temperature"])
        },
        "pm1": {
            "type": "Float",
            "value": float(data["pm1"])
        },
        "pm25": {
            "type": "Float",
            "value": float(data["pm25"])
        },
        "pm10": {
            "type": "Float",
            "value": float(data["pm10"])
        },
        "reduced": {
            "type": "Float",
            "value": float(data["reduced"])
        },
        "nh3": {
            "type": "Float",
            "value": float(data["nh3"])
        }
    }

    response = requests.post(ORION_URL, headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        logger.info(f"Data posted successfully! CAR ID: car_{entity_id}")
    elif response.status_code == 422 and eval(response.text)["description"] == "Already Exists":
        response = requests.patch(ORION_URL, headers=headers, data=json.dumps(data))
        logger.info(f"Data updated successfully! CAR ID: car_{entity_id}")
    else:
        logger.error(f"Failed to send data: {response.status_code} - {response.text}")

if __name__=="__main__":
    data, message = load_data()

    logger.info(message)

    send_data_to_orion(datetime.now().isoformat(), data)