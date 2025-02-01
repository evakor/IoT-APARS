import os
import json
import requests
import logging
import logging.config
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class StationPatrasCollector:
    def __init__(self):
        self.orion_url = os.getenv('ORION_URL') + "/entities"
        self.station_ids = [101589, 105810, 17, 1566, 101609, 47413, 1006, 741, 14857, 56113, 1592, 749, 1712, 116401, 1672]
        self.token = os.getenv('PATRAS_STATION_TOKEN')

        logging.config.fileConfig('../../../logging.conf')
        self.logger = logging.getLogger('STATION_PATRAS')

    def fetch_station_data(self, station_id):
        """Fetch station data from the API."""
        url = f"http://labserver.sense-campus.gr:5047/exmi_patras?token={self.token}&sensorid={station_id}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to fetch data for station {station_id}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error fetching data for station {station_id}: {str(e)}")
            return None

    def send_data_to_orion(self, payload):
        """Send data to Orion Context Broker."""
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
        """Fetch and send station data to Orion."""
        for station_id in self.station_ids:
            data = self.fetch_station_data(station_id)
            if data:
                payload = {
                    "id": f"patras_station_{station_id}",
                    "type": "PatrasStationAirQualityObserved",
                    "dateObserved": {"type": "DateTime", "value": data.get("date")},
                    # "temperature": {"type": "Float", "value": data.get("temp")},
                    # "humidity": {"type": "Float", "value": data.get("hum")},
                    "pm25": {"type": "Float", "value": data.get("pm25")},
                    "location": {
                        "type": "geo:json",
                        "value": {
                            "type": "Point",
                            "coordinates": [float(data.get("lon")), float(data.get("lat"))]
                        }
                    }
                }
                self.send_data_to_orion(payload)
            
            # Respect the 400ms API call limit
            time.sleep(0.4)
