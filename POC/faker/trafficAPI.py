import requests
import json
from collections import Counter

# Replace with your Google Maps API key
google_maps_api_key = 'AIzaSyC4MVTFv0aWSea92ArNhbpe3m7q16vZgds'
# AIzaSyC43Erm5QrTFeSlobnwQZNufcDdvLtMo3k

import requests
import json



def fetch_route_and_traffic(origin_lat, origin_lon, dest_lat, dest_lon, google_maps_api_key):
    """Fetch route and traffic data for the given origin and destination."""
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{origin_lat},{origin_lon}",
        "destination": f"{dest_lat},{dest_lon}",
        "mode": "driving",
        "departure_time": "now",  # Real-time traffic
        "key": google_maps_api_key
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()

    if data["status"] != "OK":
        print(f"API Error: {data['status']} | Response: {data}")
        return None

    return data

def save_traffic_data_to_json(filename, api_key):
    """Fetch and save traffic data for specific test routes in Athens."""
    # Define specific test routes in Athens or other parts of Greece
    test_routes = [
        {"origin": "37.9838,23.7275", "destination": "37.9755,23.7348"},  # Athens center
        {"origin": "38.2304,21.7531", "destination": "38.2466,21.7346"},  # Patras
        {"origin": "40.6401,22.9444", "destination": "40.6315,22.9603"},  # Thessaloniki
        {"origin": "37.9838,23.7275", "destination": "37.9847,23.7624"},  # Athens to nearby
    ]

    traffic_data = {}

    for i, route in enumerate(test_routes, start=1):
        origin = route["origin"]
        destination = route["destination"]
        print(f"Fetching traffic data for Route {i}: {origin} -> {destination}")

        try:
            data = fetch_route_and_traffic(
                origin_lat=origin.split(",")[0],
                origin_lon=origin.split(",")[1],
                dest_lat=destination.split(",")[0],
                dest_lon=destination.split(",")[1],
                google_maps_api_key=api_key,
            )

            if data:
                traffic_data[f"route_{i}"] = {
                    "origin": origin,
                    "destination": destination,
                    "route_data": data,
                }
            else:
                traffic_data[f"route_{i}"] = {
                    "origin": origin,
                    "destination": destination,
                    "error": "No route or traffic data found",
                }
        except Exception as e:
            traffic_data[f"route_{i}"] = {
                "origin": origin,
                "destination": destination,
                "error": str(e),
            }

    # Save the data to a JSON file
    with open(filename, 'w') as json_file:
        json.dump(traffic_data, json_file, indent=4)

    print(f"Traffic data saved to {filename}")
    
def extract_traffic_data(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    traffic_data = {}

    for route_id, route_info in data.items():
        origin = route_info.get("origin")
        destination = route_info.get("destination")
        route_details = route_info.get("route_data", {}).get("routes", [{}])[0].get("legs", [{}])[0]

        distance = route_details.get("distance", {}).get("text", "N/A")
        duration = route_details.get("duration", {}).get("text", "N/A")
        duration_in_traffic = route_details.get("duration_in_traffic", {}).get("text", "N/A")

        traffic_data[route_id] = {
            "origin": origin,
            "destination": destination,
            "traffic": {
                "distance": distance,
                "duration_without_traffic": duration,
                "duration_with_traffic": duration_in_traffic
            }
        }

    with open(output_file, 'w') as f:
        json.dump(traffic_data, f, indent=4)

    print(f"Traffic-only data saved to {output_file}")


# Example usage


if __name__ == "__main__":
    # Replace "traffic_data.json" with your desired filename
    save_traffic_data_to_json("traffic_data.json", google_maps_api_key)
    extract_traffic_data("traffic_data.json", "traffic_only_data.json")
