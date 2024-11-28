import requests
import json

# Orion Context Broker URL
ORION_URL = "http://localhost:1026/v2/subscriptions"

# Subscription payload
station_data_subscription_payload = {
    "description": "Subscription for ground_station updates",
    "subject": {
        "entities": [
            {
                "idPattern": ".*",  # Subscribe to all ground_station entities
                "type": "ground_station"
            }
        ],
        "condition": {
            "attrs": ["aqi"]  # Trigger notifications when 'aqi' is updated
        }
    },
    "notification": {
        "http": {
            "url": "http://localhost:5000/notify"  # Webhook server URL
        },
        "attrs": ["aqi", "latitude", "longitude", "timestamp"]  # Attributes to include in notifications
    },
    "expires": "2040-01-01T14:00:00.00Z",
    "throttling": 5
}


# Id based! Need research
car_data_subscription_payload = {
    "description": "Subscription for ground_station updates",
    "subject": {
        "entities": [
            {
                "idPattern": ".*",  # NEED TO GET ID
                "type": "car"
            }
        ],
        "condition": {
            "attrs": ["aqi"]  # NEED TO DEFINE WHEN TRIGGERED
        }
    },
    "notification": {
        "http": {
            "url": "http://localhost:5000/notify"  # Webhook server URL
        },
        "attrs": ["aqi", "latitude", "longitude", "timestamp"]  # Attributes to include in notifications
    },
    "expires": "2040-01-01T14:00:00.00Z",
    "throttling": 5
}

def subscribe(payload):
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
    get_subscriptions()
    # subscribe(station_data_subscription_payload)
# /v2/subscriptions/67484efb121e579a23020eea