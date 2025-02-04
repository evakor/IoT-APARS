import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

ORION_URL = os.getenv('ORION_URL')+"/subscriptions"

MQTT_BROKER = f"mqtt://{os.getenv('MQTT_ADDRESS')}:{os.getenv('MQTT_PORT')}"

station_data_subscription_payload = {
    "description": "Subscription for ground_station updates",
    "subject": {
        "entities": [
            {
                "idPattern": ".*",  # Subscribe to all ground_station entities
                "type": "StationAirQualityObserved"
            }
        ],
        "condition": {
            "attrs": ["aqi", "dateObserved"]  # Trigger notifications when these update
        }
    },
    "notification": {
        "mqtt": {
            "url": MQTT_BROKER,
            "topic": "apars/station/waqi"
        },
        "attrs": ["aqi", "location", "dateObserved"]  # Attributes to include in notifications
    },
    "expires": "2040-01-01T14:00:00.00Z"
}

patras_station_data_subscription_payload = {
    "description": "Subscription for patras_station updates",
    "subject": {
        "entities": [
            {
                "idPattern": ".*",
                "type": "PatrasSensorAirQualityObserved"
            }
        ],
        "condition": {
            "attrs": ["pm25", "dateObserved"]
        }
    },
    "notification": {
        "mqtt": {
            "url": MQTT_BROKER,
            "topic": "apars/station/patras"
        },
        "attrs": ["pm25", "location", "dateObserved"]
    },
    "expires": "2040-01-01T14:00:00.00Z"
}


car_data_subscription_payload = {
    "description": "Subscription for car data updates",
    "subject": {
        "entities": [
            {
                "idPattern": ".*",
                "type": "CarAirQualityObserved"
            }
        ],
        "condition": {
            "attrs": ["co","co2","pm1","pm25","pm10","oxidised","nh3"]
        }
    },
    "notification": {
        "mqtt": {
            "url": MQTT_BROKER,
            "topic": "apars/car"
        },
        "attrs": ["dateObserved", "location", "temperature",  "humidity",  "pressure", "pm1", 
                  "pm25",  "pm10",  "lpg",  "benzene",  "co", "oxidised", "reduced", "nh3", "co2",
                  "eco2", "tvoc", "aqi"]
    },
    "expires": "2040-01-01T14:00:00.00Z"
}


satellite_data_subscription_payload = {
    "description": "Subscription for satellite air quality data updates",
    "subject": {
        "entities": [
            {
                "idPattern": ".*",
                "type": "SatelliteAirQualityObserved"
            }
        ],
        "condition": {
            "attrs": ["dust", "nitrogen_monoxide", "non_methane_vocs", "particulate_matter_2.5um", 
                "particulate_matter_10um", "pm2.5_total_organic_matter", "pm10_sea_salt_dry", 
                "pm10_wildfires"]
        }
    },
    "notification": {
        "mqtt": {
            "url": MQTT_BROKER,
            "topic": "satellite"
        },
        "attrs": ["dust", "nitrogen_monoxide", "non_methane_vocs", "particulate_matter_2.5um", 
            "particulate_matter_10um", "pm2.5_total_organic_matter", "pm10_sea_salt_dry", 
            "pm10_wildfires", "residential_elementary_carbon", "secondary_inorganic_aerosol", 
            "sulphur_dioxide", "total_elementary_carbon", "location", "dateObserved"
        ]
    },
    "expires": "2040-01-01T14:00:00.00Z",
    "throttling": 5
}


def subscribe(payload):
    response = requests.post(
        ORION_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )

    # Check the response
    if response.status_code == 201:
        print("Subscription created successfully!")
        print(f"Subscription ID: {response.headers.get('Location')}")
    else:
        print(f"Failed to create subscription: {response.status_code} - {response.text}")


if __name__=="__main__":
    subscriptions = [car_data_subscription_payload] # station_data_subscription_payload, patras_station_data_subscription_payload, 
    for subscription in subscriptions:
        subscribe(subscription)