import json
import ssl
import numpy as np
import folium
from scipy.spatial import distance
from PIL import Image
import matplotlib.colors as mcolors
from multiprocessing import Pool, cpu_count
import time
import paho.mqtt.client as mqtt
from fetcher import InfluxDataFetcher
import base64
import os
from dotenv import load_dotenv

load_dotenv()

EARTH_RADIUS = 6371000  # In meters
BROKER = os.getenv('MQTT_ADDRESS')
PORT = 9002
TOPIC = "image"

def meters_to_degrees(meters, lat):
    """Convert meters to degrees for latitude and longitude."""
    lat_deg = meters / EARTH_RADIUS * (180 / np.pi)
    lon_deg = meters / (EARTH_RADIUS * np.cos(lat * np.pi / 180)) * (180 / np.pi)
    return lat_deg, lon_deg

def create_grid(lat_min, lat_max, lon_min, lon_max, accuracy_m):
    """Create a grid of latitude and longitude points."""
    lat_step, lon_step = meters_to_degrees(accuracy_m, (lat_min + lat_max) / 2)
    lat_range = np.arange(lat_min, lat_max, lat_step)
    lon_range = np.arange(lon_min, lon_max, lon_step)
    return lat_range, lon_range

def interpolate_point(args):
    """Helper function to interpolate AQI for a single point on the grid."""
    lat_range, lon_range, point, radical_decay = args
    lat, lon, aqi = point['lat'], point['lon'], float(point['aqi'])
    center = np.array([lat, lon])

    grid_lats, grid_lons = np.meshgrid(lat_range, lon_range, indexing='ij')
    grid_points = np.stack((grid_lats.ravel(), grid_lons.ravel()), axis=-1)
    dists = np.linalg.norm(grid_points - center, axis=1).reshape(len(lat_range), len(lon_range)) * EARTH_RADIUS * np.pi / 180

    decay_mask = dists <= radical_decay
    decay_values = np.maximum(0, 1 - (dists / radical_decay))
    interpolated_values = np.where(decay_mask, aqi * decay_values, 0)
    return interpolated_values

def interpolate_aqi(grid, points, radical_decay):
    """Interpolate AQI values onto the grid using radial decay."""
    lat_range, lon_range = grid
    interpolated_grid = np.full((len(lat_range), len(lon_range)), 10.0)  # Base AQI value

    args = [(lat_range, lon_range, point, radical_decay) for point in points]

    # Split tasks into manageable chunks to avoid MemoryError
    chunk_size = max(1, len(args) // cpu_count())
    chunks = [args[i:i + chunk_size] for i in range(0, len(args), chunk_size)]

    with Pool(cpu_count()) as pool:
        for chunk in chunks:
            results = pool.map(interpolate_point, chunk)
            for result in results:
                interpolated_grid += result

    return interpolated_grid

def generate_heatmap(grid, values, image_path):
    """Generate a heatmap image from the interpolated grid values."""
    lat_range, lon_range = grid

    # Define colors and bounds for AQI levels
    color_list = ["green", "yellow", "orange", "red", "purple", "maroon"]
    color_bounds = [0, 50, 100, 150, 200, 300, 500]
    cmap = mcolors.LinearSegmentedColormap.from_list("smooth_colormap", color_list, N=256)

    # Normalize values for coloring
    normalized_values = (values - np.min(values)) / (np.max(values) - np.min(values))

    # Convert to image using colormap
    heatmap = cmap(normalized_values)
    image = Image.fromarray((heatmap[:, :, :3] * 255).astype(np.uint8), mode='RGB')
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image.save(image_path)
    print(f"Heatmap image saved as '{image_path}'")
    return image

def overlay_heatmap_on_map(image, lat_min, lat_max, lon_min, lon_max, points):
    """Overlay the heatmap and data points on a Folium map."""
    folium_map = folium.Map(location=[(lat_min + lat_max) / 2, (lon_min + lon_max) / 2], zoom_start=12)

    image = np.flipud(image)

    # Add the heatmap image overlay
    img_overlay = folium.raster_layers.ImageOverlay(
        image=np.array(image),
        bounds=[[lat_min, lon_min], [lat_max, lon_max]],
        opacity=0.6,
        interactive=True,
    )
    img_overlay.add_to(folium_map)

    return folium_map

def publish(image_path: str) -> None:
    client = mqtt.Client(transport="websockets")
    client.tls_set()  # Use system's CA certificates
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
        else:
            print(f"Connection failed with code {rc}")
    
    def on_publish(client, userdata, mid):
        print(f"Message {mid} published successfully.")
    
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        
        with open(image_path, "rb") as image_file:
            message = base64.b64encode(image_file.read()).decode("utf-8")
        
        result = client.publish(TOPIC, message)
        result.wait_for_publish()
        
        print("Image sent successfully.")
        
    except ssl.SSLError as e:
        print(f"SSL Error: {e}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        client.loop_stop()
        client.disconnect()
        print("Disconnected from MQTT broker.")


def main(json_file, lat_min, lat_max, lon_min, lon_max, accuracy_m, radical_decay):
    image_path = "heatmap.png"

    start_time = time.time()

    # with open(json_file, 'r') as f:
    #     points = json.load(f)
    
    fetcher = InfluxDataFetcher()
    latest_patras_station_data = fetcher.fetch_latest_patras_station_data()
    latest_station_data = fetcher.fetch_latest_station_data()
    last_n_car_data = fetcher.fetch_last_n_car_data(200)

    points = latest_patras_station_data + latest_station_data + last_n_car_data

    #points = points[0:50]

    print(f"Interpolating {len(points)} points")

    grid = create_grid(lat_min, lat_max, lon_min, lon_max, accuracy_m)
    interpolated_values = interpolate_aqi(grid, points, radical_decay)
    heatmap_image = generate_heatmap(grid, interpolated_values, image_path)


    heatmap_image = Image.open(image_path)
    publish(image_path)

    folium_map = overlay_heatmap_on_map(heatmap_image, lat_min, lat_max, lon_min, lon_max, points)
    folium_map.save('aqi_heatmap.html')

    elapsed_time = time.time() - start_time
    print(f"Heatmap with points saved as 'aqi_heatmap.html' in {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main(
        json_file='car_data.json',
        lat_min=float(os.getenv('SOUTH')),
        lat_max=float(os.getenv('NORTH')),
        lon_min=float(os.getenv('WEST')),
        lon_max=float(os.getenv('EAST')),
        accuracy_m=5,
        radical_decay=15
    )
