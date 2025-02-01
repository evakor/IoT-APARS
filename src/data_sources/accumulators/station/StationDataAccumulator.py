import os
import json
import requests
import logging
import logging.config
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class StationDataCollector:
    def __init__(self):
        self.lat_min, self.lat_max = float(os.getenv('SOUTH')), float(os.getenv('NORTH'))
        self.lon_min, self.lon_max = float(os.getenv('WEST')), float(os.getenv('EAST'))
        self.orion_url = os.getenv('ORION_URL') + "/entities"
        self.api_token = os.getenv('STATION_API')
        self.url = f"https://api.waqi.info/map/bounds/?token={self.api_token}&latlng={self.lat_min},{self.lon_min},{self.lat_max},{self.lon_max}"
        
        logging.config.fileConfig('../../../logging.conf')
        self.logger = logging.getLogger('STATION_DATA')

    def load_data(self):
        try:
            response = requests.get(self.url)
            data = response.json()['data']
            return data
        except Exception as e:
            self.logger.error(f"Error fetching station data: {str(e)}")
            return None

    def send_data_to_orion(self, payload):
        headers = {"Content-Type": "application/json"}
        try:
            entity_id = payload["id"]
            url = f"{self.orion_url}/{entity_id}/attrs"

            response = requests.patch(url, headers=headers, json={k: v for k, v in payload.items() if k not in ["id", "type"]})

            if response.status_code == 204:
                self.logger.info(f"Data updated successfully! Station ID: {entity_id}")
            elif response.status_code == 404:
                response = requests.post(self.orion_url, headers=headers, json=payload)
                if response.status_code == 201:
                    self.logger.info(f"Data created successfully! Station ID: {entity_id}")
                else:
                    self.logger.error(f"Failed to create entity: {response.status_code} - {response.text}")
            else:
                self.logger.error(f"Failed to send data: {response.status_code} - {response.text}")
        except Exception as e:
            self.logger.error(f"Error sending data to Orion: {str(e)}")

    def accumulate(self):
        data = self.load_data()
        if data:
            for station in data:
                payload = {
                    "id": f"station_{station['uid']}",  
                    "type": "StationAirQualityObserved",  
                    "dateObserved": {"type": "DateTime", "value": datetime.utcnow().isoformat()},
                    "aqi": {"type": "Float", "value": station["aqi"]},
                    "location": {"type": "geo:json", "value": {"type": "Point", "coordinates": [station["lat"], station["lon"]]}}
                }
                self.send_data_to_orion(payload)
                time.sleep(0.1)
