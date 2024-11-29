import random
import requests
import json
import numpy as np
from geopy.distance import geodesic
import time
import paho.mqtt.client as mqtt
from datetime import datetime

BROKER_ADDRESS = "mqqt.address"
BROKER_PORT = 1883


def generate_random_coordinates(east, west, north, south):
    lat = random.uniform(south, north)
    lon = random.uniform(west, east)
    return lat, lon


def calculate_distance(coord1, coord2):
    return geodesic(coord1, coord2).km


def generate_route(start, end, osrm_server="http://router.project-osrm.org"):
    url = f"{osrm_server}/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"OSRM API error: {response.content}")
    return response.json()


def calculate_area_size(east, west, north, south):
    """Calculate the approximate area size of the bounding box."""
    top_left = (north, west)
    top_right = (north, east)
    bottom_left = (south, west)
    width = geodesic(top_left, top_right).km
    height = geodesic(top_left, bottom_left).km
    return width * height


def get_traffic_level(lat, lon, time):
    """Fake traffic API simulation based on hour of the day."""
    hour = int(time.split(":")[0])
    if 6 <= hour < 10 or 16 <= hour < 19:
        return "High"
    elif 10 <= hour < 16 or 19 <= hour < 22:
        return "Medium"
    else:
        return "Low"


def calculate_route_count(area_size, traffic_level):
    """Determine the number of routes based on traffic level and area size."""
    if traffic_level == "Low":
        return random.randint(10, 30) * int(area_size)
    elif traffic_level == "Medium":
        return random.randint(50, 200) * int(area_size)
    elif traffic_level == "High":
        return random.randint(250, 400) * int(area_size)


def generate_pollution_profile():
    """Generate a pollution levels for a car using a normal distribution."""
    return {
        "oxidised": {
            "type": "Float",
            "value": round(np.random.normal(loc=100, scale=30), 2)
        },
        "pm1": {
            "type": "Float",
            "value": round(np.random.normal(loc=9, scale=10), 2)
        },
        "pm25": {
            "type": "Float",
            "value": round(np.random.normal(loc=15, scale=20), 2)
        },
        "pm10": {
            "type": "Float",
            "value": round(np.random.normal(loc=60, scale=30), 2)
        },
        "reduced": {
            "type": "Float",
            "value": round(np.random.normal(loc=100, scale=30), 2)
        },
        "nh3": {
            "type": "Float",
            "value": round(np.random.normal(loc=150, scale=30), 2)
        }
    }


def save_car_data_to_json(car_data, filename="car_data.json"):
    """Save car data to a JSON file."""
    with open(filename, "w") as f:
        json.dump(car_data, f, indent=4)
    print(f"Car data saved to {filename}")


def generate_routes_with_cars(east, west, north, south, time):
    """Main function to generate routes and assign cars with pollution profiles."""
    lat, lon = (north + south) / 2, (east + west) / 2
    traffic_level = get_traffic_level(lat, lon, time)
    print(f"Traffic level at {time}: {traffic_level}")

    area_size = calculate_area_size(east, west, north, south)
    n_routes = calculate_route_count(area_size, traffic_level)
    print(n_routes)
    n_routes = 3
    print(f"Generating {n_routes} routes based on traffic level and area size.")

    car_data = []

    for i in range(n_routes):
        while True:
            start = generate_random_coordinates(east, west, north, south)
            end = generate_random_coordinates(east, west, north, south)
            distance = calculate_distance(start, end)
            if 5 <= distance <= 25: # Min max based on the square size
                break

        route = generate_route(start, end)
        pollution_level = generate_pollution_profile()

        car_data.append({
            "car_id": i + 1,
            "route": route["routes"][0]["geometry"]["coordinates"],
            "pollution_level": pollution_level
        })

        print(f"Car {i + 1}: Route generated with pollution level {pollution_level}")

    save_car_data_to_json(car_data)


def load_car_data(filename="car_data.json"):
    with open(filename, "r") as f:
        return json.load(f)


def publish_to_mqtt(client, topic, payload):
    client.publish(topic, json.dumps(payload))
    print(f"Published to {topic}: {json.dumps(payload)}")


def post_car_data_to_mqtt(car_data, interval=2):
    # Create MQTT client
    client = mqtt.Client()
    client.connect(BROKER_ADDRESS, BROKER_PORT)

    for car in car_data:
        car_id = car["car_id"]
        topic = f"car_{car_id}"
        route = car["route"]
        pollution = car["pollution_level"]

        for point in route:
            timestamp = datetime.now().isoformat()
            payload = {
                "id": f"car_{car_id}",
                "type": "car",
                "timestamp": {"type": "DateTime", "value": timestamp},
                "latitude": {"type": "Float", "value": float(point[1])},
                "longitude": {"type": "Float", "value": float(point[0])},
                "oxidised": {"type": "Float", "value": float(pollution["oxidised"]["value"])},
                "pm1": {"type": "Float", "value": float(pollution["pm1"]["value"])},
                "pm25": {"type": "Float", "value": float(pollution["pm25"]["value"])},
                "pm10": {"type": "Float", "value": float(pollution["pm10"]["value"])},
                "reduced": {"type": "Float", "value": float(pollution["reduced"]["value"])},
                "nh3": {"type": "Float", "value": float(pollution["nh3"]["value"])},
            }
            publish_to_mqtt(client, topic, payload)
            time.sleep(interval)

    client.disconnect()


if __name__ == "__main__":
    faker_input = {
        "east": 23.8,
        "west": 23.7,
        "north": 37.9,
        "south": 37.8,
        "time": "08:00"
    }

    generate_routes_with_cars(
        faker_input["east"],
        faker_input["west"],
        faker_input["north"],
        faker_input["south"],
        faker_input["time"]
    )

    car_data = load_car_data("car_data.json")

    post_car_data_to_mqtt(car_data)

