import random
import requests
import json
import numpy as np
from geopy.distance import geodesic
import time
import paho.mqtt.client as mqtt
from datetime import datetime, timezone
import threading
import random
import os
from dotenv import load_dotenv

load_dotenv()

BROKER_ADDRESS = "localhost"
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
    n_routes = 3
    print(f"Generating {n_routes} routes based on traffic level and area size.")

    car_data = []

    for i in range(n_routes):
        while True:
            start = generate_random_coordinates(east, west, north, south)
            end = generate_random_coordinates(east, west, north, south)
            distance = calculate_distance(start, end)
            if 5 <= distance <= 20:  # Min max based on the square size
                break

        route = generate_route(start, end)
        pollution_profile = generate_pollution_profile()

        route_with_pollution = []
        for point in route["routes"][0]["geometry"]["coordinates"]:
            route_with_pollution.append({
                "lat": point[1],  # Latitude
                "lon": point[0],  # Longitude
                "oxidised": round(np.random.normal(loc=pollution_profile["oxidised"]["value"], scale=5), 2),
                "reduced": round(np.random.normal(loc=pollution_profile["reduced"]["value"], scale=5), 2),
                "pm1": round(np.random.normal(loc=pollution_profile["pm1"]["value"], scale=2), 2),
                "pm25": round(np.random.normal(loc=pollution_profile["pm25"]["value"], scale=3), 2),
                "pm10": round(np.random.normal(loc=pollution_profile["pm10"]["value"], scale=4), 2),
                "nh3": round(np.random.normal(loc=pollution_profile["nh3"]["value"], scale=5), 2)
            })

        car_data.append({
            "car_id": i + 1,
            "route": route_with_pollution
        })

        print(f"Car {i + 1}: Route generated with pollution data added.")

    save_car_data_to_json(car_data)


def load_car_data(filename="car_data.json"):
    with open(filename, "r") as f:
        return json.load(f)


def publish_to_mqtt(client, topic, payload):
    client.publish(topic, json.dumps(payload))
    print(f"Published to {topic}: {json.dumps(payload)}")


def post_car_data_to_mqtt(car_data):
    def post_for_car(car):
        client = mqtt.Client()
        client.username_pw_set("user", "password")
        client.connect(BROKER_ADDRESS, BROKER_PORT)

        car_id = car["car_id"]
        topic = f"car_{car_id}"
        route = car["route"]

        for point in route[0:5]:
            timestamp = datetime.now().isoformat()

            payload = [f"car_{car_id}", timestamp, point["lat"], point["lon"], point["oxidised"], point["pm1"], point["pm25"], point["pm10"], point["reduced"], point["nh3"]]
            
            publish_to_mqtt(client, topic, payload)
            
            time.sleep(random.uniform(1.8, 2.2))

        client.disconnect()

    # Create and start a thread for each car
    threads = []
    for car in car_data:
        thread = threading.Thread(target=post_for_car, args=(car,))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()



if __name__ == "__main__":
    faker_input = {
        "east": float(os.getenv('WEST')),
        "west": float(os.getenv('EAST')),
        "north": float(os.getenv('SOUTH')),
        "south": float(os.getenv('NORTH')),
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

