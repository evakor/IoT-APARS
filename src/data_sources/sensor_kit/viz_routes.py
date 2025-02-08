import folium
import json
import os
import random

# Load car data from the JSON file
car_data_file = "car_data.json"

if not os.path.exists(car_data_file):
    print(f"File {car_data_file} not found.")
    exit()

with open(car_data_file, "r") as file:
    car_data = json.load(file)

# Create a Folium map centered on the average location
map_center = [38.285387, 21.795022]  # Default center point
car_map = folium.Map(location=map_center, zoom_start=12)

colors = ["blue", "red", "green", "yellow", "purple", "orange", "pink", "black", "white", "brown"]
# Function to add routes to the map
def add_routes_to_map(data, car_map):
    for car in data:
        car_id = car["car_id"]
        route = car["route"]

        n = 2

        print(f"Car {car_id} has {len(route)} points")

        if len(route) > 100:
            print(f"Car {car_id} from {len(route)} to {len(route[n-1::n])}")
            route = route[n-1::n]
        
        # Extract coordinates and create polyline
        coordinates = [(point["lat"], point["lon"]) for point in route]
        
        # Add polyline to the map
        folium.PolyLine(
            coordinates, 
            color=random.choice(colors), 
            weight=2.5, 
            opacity=0.8, 
            tooltip=f"Car ID: {car_id}"
        ).add_to(car_map)
        
        # Add markers for each point in the route
        # for point in route:
        #     popup_text = (
        #         f"<b>Car ID:</b> {car_id}<br>"
        #     )
        #     folium.Marker(
        #         [point["lat"], point["lon"]],
        #         popup=popup_text,
        #         icon=folium.Icon(color="blue", icon="info-sign")
        #     ).add_to(car_map)

# Add routes to the map
add_routes_to_map(car_data, car_map)

# Save the map to an HTML file and display it
map_output_file = "car_routes_map.html"
car_map.save(map_output_file)
print(f"Map has been saved to {map_output_file}. Open it in a browser to view the car routes.")
