import requests

url = "http://150.140.186.118:1026/v2/entities/GridStationAQI_1"
headers = {
    "Accept": "application/json"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    entity = response.json()
    print("Full entity:")
    print(entity)
    print("\nNoise attribute value:")
    print(entity["noise"]["value"])
else:
    print(f"Failed to retrieve entity: {response.status_code}")
    print(response.json())
