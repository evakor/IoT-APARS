# Subscription creation to send notifications to your webhook

import requests

# Orion Context Broker URL
context_broker_url = "http://localhost:1026/v2/subscriptions"

# Webhook URL
webhook_url = "http://<webhook_server_ip>:5000/webhook"

# Create a subscription for GPS data
subscription = {
    "description": "Notify GPS data changes",
    "subject": {
        "entities": [
            {"idPattern": ".*", "type": "GPS"}
        ],
        "condition": {
            "attrs": ["location", "speed"]
        }
    },
    "notification": {
        "http": {
            "url": webhook_url
        },
        "attrs": ["location", "speed"]
    }
}

response = requests.post(context_broker_url, json=subscription)
if response.status_code == 201:
    print("Subscription created successfully.")
else:
    print(f"Failed to create subscription: {response.text}")
