import os
import json
import requests
import logging
import logging.config
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class PatrasSensorDataCollector:
    def __init__(self):
        self.sensor_ids = [105810, 741, 1672, 56113, 101589, 17, 101609, 1566, 749, 1592, 14857, 1006, 47413, 116401, 1712]
        self.token = os.getenv('PATRAS_STATION_TOKEN')
        self.api_url = "http://labserver.sense-campus.gr:5047/exmi_patras"
        self.orion_url = os.getenv('ORION_URL') + "/entities"

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_config_path = os.path.join(base_dir, 'logging.conf')

        if os.path.exists(log_config_path):
            logging.config.fileConfig(log_config_path)
        else:
            logging.basicConfig(level=logging.INFO)

        self.logger = logging.getLogger('PATRAS-STATION-ACCUMULATOR')

    def load_data(self, sensor_id):
        try:
            response = requests.get(f"{self.api_url}?token={self.token}&sensorid={sensor_id}")
            data = json.loads(response.content)
            return data
        except Exception as e:
            self.logger.error(f"Error fetching data for sensor ID {sensor_id}: {str(e)}")
            return None

    def send_data_to_orion(self, payload):
        headers = {"Content-Type": "application/json"}
        try:
            entity_id = payload["id"]
            url = f"{self.orion_url}/{entity_id}/attrs"

            response = requests.patch(url, headers=headers, json={k: v for k, v in payload.items() if k not in ["id", "type"]})

            if response.status_code == 204:
                print(f"PATRAS-STATION-ACCUMULATOR - Data updated successfully! Sensor ID: {entity_id}")
            elif response.status_code == 404:
                response = requests.post(self.orion_url, headers=headers, json=payload)
                if response.status_code == 201:
                    print(f"PATRAS-STATION-ACCUMULATOR - Data created successfully! Sensor ID: {entity_id}")
                else:
                    self.logger.error(f"Failed to create entity: {response.status_code} - {response.text}")
            else:
                self.logger.error(f"Failed to send data: {response.status_code} - {response.text}")
        except Exception as e:
            self.logger.error(f"Error sending data to Orion: {str(e)}")

    def accumulate(self):
        for sensor_id in self.sensor_ids:
            data = self.load_data(sensor_id)
            if data and "label" in data and data["label"]:
                try:
                    lat = float(data["lat"])
                    lon = float(data["lon"])
                    pm25 = float(data["pm25"])

                    try:
                        date_observed = datetime.strptime(data.get("date"), "%Y-%m-%d %H:%M:%S").isoformat()
                    except Exception as e:
                        date_observed = datetime.utcnow().isoformat()
                    
                    payload = {
                        "id": f"patras_sensor_{sensor_id}",
                        "type": "PatrasSensorAirQualityObserved",
                        "dateObserved": {"type": "DateTime", "value": date_observed},
                        "humidity": {"type": "Float", "value": data.get("hum")},
                        "temperature": {"type": "Float", "value": data.get("temp")},
                        "pm25": {"type": "Float", "value": pm25},
                        "location": {
                            "type": "geo:json",
                            "value": {"type": "Point", "coordinates": [lat, lon]}
                        },
                        "label": {"type": "Text", "value": data.get("label")}
                    }
                    self.send_data_to_orion(payload)
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid data for sensor ID {sensor_id}: lat={data.get('lat')}, lon={data.get('lon')}, pm25={data.get('pm25')}")
            time.sleep(0.4)
