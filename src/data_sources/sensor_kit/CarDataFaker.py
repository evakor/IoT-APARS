import random
import requests
import json
import numpy as np
from geopy.distance import geodesic
import time
import paho.mqtt.client as mqtt
from datetime import datetime
import threading
import os
from dotenv import load_dotenv

load_dotenv()

BROKER_ADDRESS = os.getenv('MQTT_ADDRESS')
BROKER_PORT = int(os.getenv('MQTT_PORT'))

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
    top_left = (north, west)
    top_right = (north, east)
    bottom_left = (south, west)
    width = geodesic(top_left, top_right).km
    height = geodesic(top_left, bottom_left).km
    return width * height

def get_traffic_level(lat, lon, time):
    hour = int(time.split(":")[0])
    if 6 <= hour < 10 or 16 <= hour < 19:
        return "High"
    elif 10 <= hour < 16 or 19 <= hour < 22:
        return "Medium"
    else:
        return "Low"

def calculate_route_count(area_size, traffic_level):
    if traffic_level == "Low":
        return random.randint(10, 30) * int(area_size)
    elif traffic_level == "Medium":
        return random.randint(50, 200) * int(area_size)
    elif traffic_level == "High":
        return random.randint(250, 400) * int(area_size)

def generate_pollution_profile():
    return {
        "temperature": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=20, scale=2), 15, 25), 2))},
        "humidity": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=20, scale=20), 0, 100), 2))},
        "pressure": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=999, scale=0.1), 0, 1001), 2))},
        "oxidised": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=1, scale=5), 0.05, 10), 2))},
        "pm1": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=50, scale=100), 0, 1000), 2))},
        "pm25": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=50, scale=100), 0, 1000), 2))},
        "pm10": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=50, scale=100), 0, 1000), 2))},
        "reduced": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=100, scale=200), 1, 1000), 2))},
        "nh3": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=50, scale=100), 1, 300), 2))},
        "lpg": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=750, scale=1200), 200, 10000), 2))},
        "benzene": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=300, scale=120), 10, 1000), 2))},
        "co": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=300, scale=500), 20, 2000), 2))},
        "co2": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=1500, scale=5000), 400, 10000), 2))},
        "eco2": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=10000, scale=5000), 400, 60000), 2))},
        "tvoc": {"type": "Float", "value": abs(round(np.clip(np.random.normal(loc=10000, scale=5000), 0, 60000), 2))}
    }

def save_car_data_to_json(car_data, filename="car_data.json"):
    with open(filename, "w") as f:
        json.dump(car_data, f, indent=4)
    print(f"Car data saved to {filename}")

def generate_routes_with_cars(east, west, north, south, time):
    lat, lon = (north + south) / 2, (east + west) / 2
    traffic_level = get_traffic_level(lat, lon, time)
    print(f"Traffic level at {time}: {traffic_level}")

    area_size = calculate_area_size(east, west, north, south)
    #n_routes = calculate_route_count(area_size, traffic_level)
    n_routes = 3
    print(f"Generating {n_routes} routes based on traffic level and area size.")

    car_data = []

    for i in range(n_routes):
        while True:
            start = generate_random_coordinates(east, west, north, south)
            end = generate_random_coordinates(east, west, north, south)
            distance = calculate_distance(start, end)
            if 5 <= distance <= 20:
                break

        route = generate_route(start, end)
        pollution_profile = generate_pollution_profile()

        route_with_pollution = []
        for point in route["routes"][0]["geometry"]["coordinates"]:
            route_with_pollution.append({
                "lat": point[1],
                "lon": point[0],
                **{k: round(np.random.normal(loc=v["value"], scale=5), 2) for k, v in pollution_profile.items()}
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
        client.connect(BROKER_ADDRESS, BROKER_PORT)

        car_id = car["car_id"]
        topic = f"apars_cars"
        route = car["route"]

        for point in route[0:20]:
            timestamp = datetime.now().isoformat()
            payload = [f"car_{car_id}", timestamp, point["lat"], point["lon"], 
                       point["temperature"], point["humidity"], point["pressure"], 
                       point["pm1"], point["pm25"], point["pm10"], point["lpg"], 
                       point["benzene"], point["co"], point["oxidised"],  
                       point["reduced"], point["nh3"], point["co2"], 
                       point["eco2"], point["tvoc"]]
            publish_to_mqtt(client, topic, payload)
            time.sleep(random.uniform(1.8, 2.2))

        client.disconnect()

    threads = []
    for car in car_data:
        thread = threading.Thread(target=post_for_car, args=(car,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    faker_input = {
        "east": float(os.getenv('EAST')),
        "west": float(os.getenv('WEST')),
        "north": float(os.getenv('NORTH')),
        "south": float(os.getenv('SOUTH')),
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
