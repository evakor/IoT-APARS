import random
import requests
import folium
import gpxpy
import gpxpy.gpx
from geopy.distance import geodesic


def generate_random_coordinates(east, west, north, south):
    """Generate random coordinates within the given bounding box."""
    lat = random.uniform(south, north)
    lon = random.uniform(west, east)
    return lat, lon


def calculate_distance(coord1, coord2):
    """Calculate distance between two coordinates."""
    return geodesic(coord1, coord2).km


def generate_route(start, end, osrm_server="http://router.project-osrm.org"):
    """Generate a route using OSRM between start and end points."""
    url = f"{osrm_server}/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"OSRM API error: {response.content}")
    return response.json()


def save_gpx(route, filename):
    """Save route data as GPX."""
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for point in route["routes"][0]["geometry"]["coordinates"]:
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(latitude=point[1], longitude=point[0]))

    with open(filename, "w") as f:
        f.write(gpx.to_xml())


def display_routes_on_map(routes, map_filename="routes_map.html"):
    """Display routes on a map using folium."""
    map_center = routes[0]["routes"][0]["geometry"]["coordinates"][0][::-1]  # Reverse to lat, lon
    m = folium.Map(location=map_center, zoom_start=13)

    for route in routes:
        points = [(point[1], point[0]) for point in route["routes"][0]["geometry"]["coordinates"]]
        folium.PolyLine(points, color="blue", weight=2.5, opacity=0.8).add_to(m)

    m.save(map_filename)
    print(f"Map saved to {map_filename}")


def generate_gpx_routes(east, west, north, south, n_routes):
    """Generate and save multiple GPX routes."""
    routes = []
    for i in range(n_routes):
        while True:
            start = generate_random_coordinates(east, west, north, south)
            end = generate_random_coordinates(east, west, north, south)
            distance = calculate_distance(start, end)
            if 5 <= distance <= 25:
                break

        print(f"Generating route {i + 1}/{n_routes} from {start} to {end} ({distance:.2f} km)")
        route = generate_route(start, end)
        routes.append(route)

        filename = f"route_{i + 1}.gpx"
        save_gpx(route, filename)
        print(f"Route {i + 1} saved to {filename}")

    display_routes_on_map(routes)


# Example usage
if __name__ == "__main__":
    east, west, north, south = 23.8, 23.7, 37.9, 37.8  # Example bounding box for Athens, Greece
    n_routes = 3  # Number of routes to generate
    generate_gpx_routes(east, west, north, south, n_routes)
