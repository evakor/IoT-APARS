import requests
import json

# Orion Context Broker URL
ORION_URL = "http://localhost:1026/v2/subscriptions"
WEBHOOK_SERVER_URL = "http://localhost:5001"

#theloume na anoixei ena mqtt apo cb se webhook kai meta na ta stelnei influx

# Subscription payload test
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
            "attrs": ["aqi"]  # Trigger notifications when 'aqi' is updated
        }
    },
    "notification": {
        "http": {
            # "url": "http://localhost:5000/notify"  # Webhook server URL
            "url": f"{WEBHOOK_SERVER_URL}/station-data-upload"
        },
        "attrs": ["aqi", "location","dateObserved"]  # Attributes to include in notifications
    },
    "expires": "2040-01-01T14:00:00.00Z",
    "throttling": 5
}


# Id based! Need research
car_data_subscription_payload = {
    "description": "Subscription for car data updates",
    "subject": {
        "entities": [
            {
                "idPattern": ".*",  # NEED TO GET ID
                "type": "CarAirQualityObserved"
            }
        ],
        "condition": {
            "attrs": ["dateObserved"]  # NEED TO DEFINE WHEN TRIGGERED
        }
    },
    "notification": {
        "http": {
            # "url": "http://localhost:5000/notify"  # Webhook server URL
            "url":f"{WEBHOOK_SERVER_URL}/car-data-upload"
        },
        "attrs": ["location","pm1","pm25", "pm10", "co","co2", "dateObserved"]  # Attributes to include in notifications
    },
    "expires": "2040-01-01T14:00:00.00Z",
    "throttling": 5
}

satellite_data_subscription_payload = {
    "description": "Subscription for satellite air quality data updates",
    "subject": {
        "entities": [
            {
                "idPattern": ".*",  # NEED TO GET ID
                "type": "SatelliteAirQualityObserved"
            }
        ],
        "condition": {
            "attrs": ["dust", "nitrogen_monoxide", "non_methane_vocs", "particulate_matter_2.5um", 
                "particulate_matter_10um", "pm2.5_total_organic_matter", "pm10_sea_salt_dry", 
                "pm10_wildfires"]  # NEED TO DEFINE WHEN TRIGGERED
        }
    },
    "notification": {
        "http": {
            # "url": "http://localhost:5000/notify"  # Webhook server URL
            "url":f"{WEBHOOK_SERVER_URL}/satellite-upload"
        },
        "attrs": ["dust", "nitrogen_monoxide", "non_methane_vocs", "particulate_matter_2.5um", 
            "particulate_matter_10um", "pm2.5_total_organic_matter", "pm10_sea_salt_dry", 
            "pm10_wildfires", "residential_elementary_carbon", "secondary_inorganic_aerosol", 
            "sulphur_dioxide", "total_elementary_carbon", "location", "dateObserved"
        ]  # Attributes to include in notifications
    },
    "expires": "2040-01-01T14:00:00.00Z",
    "throttling": 5
}



def subscribe(payload):
    # Check existing subscriptions
    response = requests.get(ORION_URL)
    if response.status_code == 200:
        subscriptions = response.json()
        for sub in subscriptions:
            if sub["description"] == payload["description"] and sub["notification"]["http"]["url"] == payload["notification"]["http"]["url"]:
                print("Subscription already exists. Skipping...")
                return
    
    response = requests.post(
        ORION_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(station_data_subscription_payload)
    )

    # Check the response
    if response.status_code == 201:
        print("Subscription created successfully!")
        print(f"Subscription ID: {response.headers.get('Location')}")
    else:
        print(f"Failed to create subscription: {response.status_code} - {response.text}")

def get_subscriptions():
    response = requests.get(ORION_URL)

    # Check the response
    if response.status_code == 200:
        print("Subscription created successfully!\nSubscriptions: \n")
        for sub in list(response.json()):
            print(json.dumps(sub, indent=2))
    else:
        print(f"Failed to get subscriptions: {response.status_code} - {response.text}")


if __name__=="__main__":
    #Create subscriptions
    #subscribe(station_data_subscription_payload)
    subscribe(car_data_subscription_payload)
    #subscribe(satellite_data_subscription_payload)
    
    get_subscriptions()
    # subscribe(station_data_subscription_payload)
# /v2/subscriptions/67484efb121e579a23020eea