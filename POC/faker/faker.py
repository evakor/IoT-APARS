import random
import requests
import json
import numpy as np
from geopy.distance import geodesic

from trafficCharac import get_region_from_coordinates

def generate_random_coordinates(east, west, north, south):
    lat = random.uniform(south, north)
    lon = random.uniform(west, east)
    print(f"Generated coordinates: Latitude {lat}, Longitude {lon}")
    return lat, lon

def calculate_distance(coord1, coord2):
    distance = geodesic(coord1, coord2).km
    print(f"Calculated distance between {coord1} and {coord2}: {distance} km")
    return distance

def generate_route(start, end, osrm_server="http://router.project-osrm.org"):
    url = f"{osrm_server}/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson"
    print(f"Requesting route from OSRM server with URL: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"OSRM API error: {response.content}")
    print("Route generated successfully.")
    return response.json()

def calculate_area_size(east, west, north, south):
    top_left = (north, west)
    top_right = (north, east)
    bottom_left = (south, west)
    width = geodesic(top_left, top_right).km
    height = geodesic(top_left, bottom_left).km
    area_size = width * height
    print(f"Calculated area size: {area_size} square km")
    return area_size

def get_traffic_level(lat, lon, time):
    hour = int(time.split(":")[0])
    traffic_level = "Low"
    if 6 <= hour < 10 or 16 <= hour < 19:
        traffic_level = "High"
    elif 10 <= hour < 16 or 19 <= hour < 22:
        traffic_level = "Medium"
    print(f"Traffic level based on time {time} ({hour}h): {traffic_level}")
    return traffic_level

def calculate_route_count(area_size, traffic_level):
    count = 10
    if traffic_level == "Low":
        count = random.randint(10, 30)
    elif traffic_level == "Medium":
        count = random.randint(50, 200)
    elif traffic_level == "High":
        count = random.randint(250, 400)
    route_count = count * int(area_size)
    print(f"Calculated number of routes: {route_count} based on traffic level {traffic_level} and area size {area_size}")
    return route_count

def generate_pollution_profile():
    pollution_level = round(np.random.normal(loc=150, scale=30), 2)  # Mean 150, std dev 30
    print(f"Generated pollution level: {pollution_level}")
    return pollution_level

def save_car_data_to_json(car_data, filename="car_data.json"):
    with open(filename, "w") as f:
        json.dump(car_data, f, indent=4)
    print(f"Car data saved to {filename}")

def generate_routes_with_cars(east, west, north, south, time):
    traffic_level = get_region_from_coordinates("athens_traffic_data.json", south, west, north, east)
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
            if 5 <= distance <= 25:  # Min max based on the square size
                print(f"Valid route found for car {i+1} within the required distance range.")
                break
            else:
                print(f"Discarded route for car {i+1} outside the required distance range.")

        route = generate_route(start, end)
        pollution_level = generate_pollution_profile()

        car_data.append({
            "car_id": i + 1,
            "route": route["routes"][0]["geometry"]["coordinates"],
            "pollution_level": pollution_level
        })

        print(f"Car {i + 1}: Route generated with pollution level {pollution_level}")

    save_car_data_to_json(car_data)

   
# Example input
faker_input = {
    "east": 23.77,
    "west": 23.9,
    "north": 37.8,
    "south": 37.95,
    "time": "10:00"
}

if __name__ == "__main__":
    generate_routes_with_cars(
        faker_input["east"],
        faker_input["west"],
        faker_input["north"],
        faker_input["south"],
        faker_input["time"]
    )
