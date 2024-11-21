import requests
import folium
import gpxpy
import gpxpy.gpx
import random
import numpy as np


def decode_polyline(polyline):
    """
    Decode a polyline to get a list of latitude and longitude points.
    """
    index, lat, lng = 0, 0, 0
    coordinates = []
    while index < len(polyline):
        shift, result = 0, 0
        while True:
            b = ord(polyline[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if result & 1 else (result >> 1)
        lat += dlat

        shift, result = 0, 0
        while True:
            b = ord(polyline[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if result & 1 else (result >> 1)
        lng += dlng

        coordinates.append((lat / 1e5, lng / 1e5))
    return coordinates


def fetch_route_and_traffic(start_coords, end_coords, google_maps_api_key):
    """
    Fetch the route and traffic data between start and end coordinates using the Google Maps Directions API.
    """
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{start_coords[0]},{start_coords[1]}",
        "destination": f"{end_coords[0]},{end_coords[1]}",
        "mode": "driving",
        "departure_time": "now",  # Fetch real-time traffic
        "key": google_maps_api_key
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()

    if data["status"] != "OK":
        raise ValueError(f"Error fetching route: {data['status']}")

    # Decode the polyline for detailed route geometry
    polyline = data["routes"][0]["overview_polyline"]["points"]
    geometry = decode_polyline(polyline)

    # Extract traffic conditions
    route = data["routes"][0]["legs"][0]["steps"]
    traffic_conditions = []
    for step in route:
        if "duration_in_traffic" in step and step["duration_in_traffic"]["value"] > step["duration"]["value"]:
            traffic_conditions.append("High")
        elif "duration_in_traffic" in step and step["duration_in_traffic"]["value"] > 1.1 * step["duration"]["value"]:
            traffic_conditions.append("Medium")
        else:
            traffic_conditions.append("Low")

    distance_km = data["routes"][0]["legs"][0]["distance"]["value"] / 1000  # Distance in kilometers

    if not (2 <= distance_km <= 25):
        raise ValueError(f"Route is {distance_km:.2f} km, which is outside the 2-25 km range.")

    print(f"Route found: {distance_km:.2f} km")
    return geometry, traffic_conditions, distance_km


def save_route_to_gpx(route_coords, gpx_filename):
    """
    Save the route to a GPX file.
    """
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for lat, lon in route_coords:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon))

    with open(gpx_filename, 'w') as gpx_file:
        gpx_file.write(gpx.to_xml())

    print(f"GPX file saved as {gpx_filename}")


def determine_traffic_level(traffic_conditions):
    """
    Determine overall traffic level based on traffic conditions.
    """
    high_traffic = traffic_conditions.count("High")
    medium_traffic = traffic_conditions.count("Medium")
    low_traffic = traffic_conditions.count("Low")

    if high_traffic > medium_traffic and high_traffic > low_traffic:
        return "High"
    elif medium_traffic > low_traffic:
        return "Medium"
    else:
        return "Low"


def generate_car_profiles(num_routes):
    """
    Generate pollution profiles for cars using a Normal distribution.
    """
    mean_pollution = 5.0  # Mean pollution level
    std_dev_pollution = 1.5  # Standard deviation for pollution
    profiles = np.random.normal(mean_pollution, std_dev_pollution, num_routes)
    return profiles


def plot_route_with_traffic_and_cars(route_coords, start_coords, end_coords, traffic_conditions, google_maps_api_key, car_profiles):
    """
    Plot the route on a map using folium with traffic data, cars, and traffic visualization layer.
    """
    # Initialize the map centered on the start coordinates
    route_map = folium.Map(location=start_coords, zoom_start=13)

    # Add the route as a polyline
    for i in range(len(route_coords) - 1):
        start = route_coords[i]
        end = route_coords[i + 1]
        traffic_level = traffic_conditions[i] if i < len(traffic_conditions) else "Low"
        color = {"Low": "green", "Medium": "orange", "High": "red"}.get(traffic_level, "blue")
        folium.PolyLine([start, end], color=color, weight=5).add_to(route_map)

    # Add markers for start and end points
    folium.Marker(start_coords, popup="Starting point of the route", icon=folium.Icon(color="black")).add_to(route_map)
    folium.Marker(end_coords, popup="Ending point of the route", icon=folium.Icon(color="gray")).add_to(route_map)

    # Add car markers along the route
    for i, pollution in enumerate(car_profiles):
        car_position = random.choice(route_coords)  # Randomly select a position on the route
        folium.CircleMarker(
            location=car_position,
            radius=3,
            color="blue",
            fill=True,
            fill_opacity=1.0,
            popup=f"Car {i + 1}: Pollution {round(pollution, 2)}"
        ).add_to(route_map)

    # Add Google Maps traffic tiles
    traffic_tile_url = (
        f"https://mt1.google.com/vt/lyrs=h,traffic&x={{x}}&y={{y}}&z={{z}}&key={google_maps_api_key}"
    )
    folium.TileLayer(
        tiles=traffic_tile_url,
        attr="Map data ©2024 Google",
        name="Traffic Layer",
        overlay=True,
        control=True
    ).add_to(route_map)

    # Add layer control for toggling the traffic layer
    folium.LayerControl().add_to(route_map)

    # Save map to HTML
    route_map.save("accurate_route_with_traffic.html")
    print("Map saved as 'accurate_route_with_traffic.html'.")


# Example Input
start_coordinates = (38.0456, 23.7230)  # Near Kifisós River, Metamorfosi
end_coordinates = (37.9842, 23.6825)  # Near Kifisós River, Moschato
google_maps_api_key = "YOUR_GOOGLE_MAPS_API_KEY"  # Replace with your API key

# Fetch the route and traffic data
route, traffic_conditions, distance = fetch_route_and_traffic(start_coordinates, end_coordinates, google_maps_api_key)

# Determine traffic level
traffic_level = determine_traffic_level(traffic_conditions)
print(f"Traffic Level: {traffic_level}")

# Generate car pollution profiles
car_profiles = generate_car_profiles(len(route))

# Save the route to a GPX file
save_route_to_gpx(route, "accurate_route.gpx")

# Plot the route with traffic and cars
plot_route_with_traffic_and_cars(route, start_coordinates, end_coordinates, traffic_conditions, google_maps_api_key, car_profiles)
