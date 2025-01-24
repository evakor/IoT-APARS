import folium
from PIL import Image
import matplotlib.colors as mcolors
import numpy as np
import os
import matplotlib.pyplot as plt
import requests
from scipy.spatial import cKDTree
import json

accuracy = 10  # Set accuracy in meters
# Patras
lat_min, lat_max = 38.205683, 38.294508
lon_min, lon_max = 21.688356, 21.830913
apiToken = 'ecaa84eb1dbceeaf83c27c213369e4cf372c03c8'
url = f"https://api.waqi.info/map/bounds/?token={apiToken}&latlng={lat_min},{lon_min},{lat_max},{lon_max}"
data_file = "datae.json"
default_aqi = 10  # Default AQI value
radius_km = 0.08

# Convert accuracy in meters to degrees
meters_to_degrees_lat = accuracy / 111320  # 1 degree latitude is ~111.32 km
meters_to_degrees_lon = accuracy / (40075000 * np.cos(np.radians((lat_min + lat_max) / 2)) / 360)

if os.path.exists(data_file):
    with open(data_file, "r") as file:
        data = json.load(file)
else:
    print("Getting data...")
    response = requests.get(url)
    data = response.json()['data']
    with open(data_file, "w") as file:
        json.dump(data, file)

clip_points = [
    {"lat": point['lat'], "lon": point['lon'], "value": int(point['aqi'] if point['aqi'] != '-' else 40)}
    for point in data
    if lat_min <= point['lat'] <= lat_max and lon_min <= point['lon'] <= lon_max
]

latitudes = [point['lat'] for point in clip_points]
longitudes = [point['lon'] for point in clip_points]
aqi_values = [int(point['value']) for point in clip_points]

grid_lat, grid_lon = np.mgrid[
    lat_min:lat_max:meters_to_degrees_lat,
    lon_min:lon_max:meters_to_degrees_lon
]
grid_shape = grid_lat.shape
combined_aqi = np.full(grid_shape, default_aqi)  # Initialize with default AQI

station_coords = np.array(list(zip(latitudes, longitudes)))
station_tree = cKDTree(station_coords)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    d_lat = np.radians(lat2 - lat1)
    d_lon = np.radians(lon2 - lon1)
    a = np.sin(d_lat / 2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(d_lon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

def radial_decay(distance, max_radius):
    if distance > max_radius:
        return 0
    return 1 - (distance / max_radius)  # Linear decay to zero at max_radius

if True:
    for i in range(grid_shape[0]):
        if i%5:
            print(i/grid_shape[0] * 100)
        for j in range(grid_shape[1]):
            grid_point = (grid_lat[i, j], grid_lon[i, j])
            total_weight = 0
            weighted_sum = 0

            for lat, lon, aqi in zip(latitudes, longitudes, aqi_values):
                distance = haversine(grid_point[0], grid_point[1], lat, lon)
                decay_weight = radial_decay(distance, radius_km)

                if decay_weight > 0:  # Only consider points within `radius_km`
                    total_weight += decay_weight
                    weighted_sum += decay_weight * aqi

            # Assign interpolated AQI or default value if no influence
            combined_aqi[i, j] = (weighted_sum / total_weight) if total_weight > 0 else default_aqi

def save_aqi_image(data, bounds, filename="aqi_overlay.png"):
    lat_min, lat_max, lon_min, lon_max = bounds

    color_list = ["green", "yellow", "orange", "red", "purple", "maroon"]
    color_bounds = [0, 50, 100, 150, 200, 300, 500]
    norm = mcolors.BoundaryNorm(color_bounds, len(color_list))
    cmap = mcolors.ListedColormap(color_list)

    normalized_data = np.clip(data, color_bounds[0], color_bounds[-1])
    normalized_data = (normalized_data - color_bounds[0]) / (color_bounds[-1] - color_bounds[0])
    image_data = (cmap(normalized_data) * 255).astype(np.uint8)

    height, width = data.shape
    image = Image.fromarray(image_data, mode="RGBA")
    aspect_ratio = (lat_max - lat_min) / (lon_max - lon_min)
    new_height = int(width * aspect_ratio)
    image = image.resize((width, new_height), Image.Resampling.BILINEAR)

    image.save(filename)
    print(f"AQI image saved as {filename} with shape {data.shape}")

def add_aqi_overlay_to_map(aqi_image_path, lat_min, lat_max, lon_min, lon_max, clip_points):
    center_lat = (lat_min + lat_max) / 2
    center_lon = (lon_min + lon_max) / 2
    folium_map = folium.Map(location=[center_lat, center_lon], zoom_start=15)

    offset =  776 / (111320*np.cos(center_lat))

    bounds = [[lat_min - offset, lon_min], [lat_max - offset, lon_max]]
    image_overlay = folium.raster_layers.ImageOverlay(
        image=aqi_image_path,
        bounds=bounds,
        opacity=0.6,
        interactive=True
    )
    image_overlay.add_to(folium_map)

    for point in clip_points:
        folium.CircleMarker(
            location=[point['lat'], point['lon']],
            radius=1,
            color='black',
            fill=True,
            fill_color='black'
        ).add_to(folium_map)

    folium.LayerControl().add_to(folium_map)

    map_filename = "aqi_map_with_dots.html"
    folium_map.save(map_filename)
    print(f"AQI map saved as {map_filename} with bounds {bounds}")

# Save and add overlay
save_aqi_image(combined_aqi, (lat_min, lat_max, lon_min, lon_max))
add_aqi_overlay_to_map("aqi_overlay.png", lat_min, lat_max, lon_min, lon_max, clip_points)
