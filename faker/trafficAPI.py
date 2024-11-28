import requests
import json
from collections import Counter

# Replace with your Google Maps API key
google_maps_api_key = "enter_your_api_key"

def fetch_route_and_traffic(south, west, north, east, google_maps_api_key):
    """Fetch route and traffic data for the bounding box using the Google Maps API."""
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{south},{west}",
        "destination": f"{north},{east}",
        "mode": "driving",
        "departure_time": "now",  # Fetch real-time traffic
        "key": google_maps_api_key
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()
    
    if data["status"] != "OK":
        return None

    route = data["routes"][0]["legs"][0]["steps"]
    traffic_conditions = []
    for step in route:
        if "duration_in_traffic" in step and step["duration_in_traffic"]["value"] > step["duration"]["value"]:
            traffic_conditions.append("High")
        elif "duration_in_traffic" in step and step["duration_in_traffic"]["value"] > 1.1 * step["duration"]["value"]:
            traffic_conditions.append("Medium")
        else:
            traffic_conditions.append("Low")
    
    return {
        "traffic_conditions": traffic_conditions,
        "steps": len(route)
    }


def save_athens_traffic_to_json(filename, api_key):
    """Fetch and save traffic data for a grid covering Athens."""
    # Define a grid over Athens (you might need to adjust these based on the area coverage)
    west, east = 23.65, 23.85  # Longitude bounds
    south, north = 37.85, 38.05  # Latitude bounds
    step = 0.02  # Grid size

    athens_traffic_data = {}

    lat = south
    while lat < north:
        lon = west
        while lon < east:
            region_id = f"region_{lat}_{lon}"
            try:
                data = fetch_route_and_traffic(lat, lon, lat + step, lon + step, api_key)
                athens_traffic_data[region_id] = {
                    "coordinates": {"south": lat, "west": lon, "north": lat + step, "east": lon + step},
                    "traffic_data": data if data else {"error": "Unable to fetch data"}
                }
            except Exception as e:
                athens_traffic_data[region_id] = {"error": str(e)}
            lon += step
        lat += step

    with open(filename, 'w') as json_file:
        json.dump(athens_traffic_data, json_file, indent=4)

    print(f"Athens traffic data saved to {filename}")
    
if __name__ == "__main__":
    save_athens_traffic_to_json("athens_traffic_data.json", google_maps_api_key)