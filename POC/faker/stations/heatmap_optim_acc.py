import json
import numpy as np
from numba import njit, prange
from joblib import Parallel, delayed
import time
from PIL import Image
import matplotlib.colors as mcolors
import folium

# Constants
EARTH_RADIUS = 6371000  # Radius of the Earth in meters

@njit
def meters_to_degrees(meters, lat):
    """Convert meters to degrees for latitude and longitude."""
    lat_deg = meters / EARTH_RADIUS * (180 / np.pi)
    lon_deg = meters / (EARTH_RADIUS * np.cos(lat * np.pi / 180)) * (180 / np.pi)
    return lat_deg, lon_deg

def create_grid(lat_min, lat_max, lon_min, lon_max, accuracy_m):
    """Create a grid of latitude and longitude points."""
    lat_step, lon_step = meters_to_degrees(accuracy_m, (lat_min + lat_max) / 2)
    lat_range = np.arange(lat_min, lat_max, lat_step, dtype=np.float32)
    lon_range = np.arange(lon_min, lon_max, lon_step, dtype=np.float32)
    return lat_range, lon_range

@njit(parallel=True)
def calculate_decay(lat_grid, lon_grid, lat, lon, aqi, radical_decay):
    """Calculate decay values for a grid chunk."""
    dists = np.sqrt((lat_grid - lat) ** 2 + (lon_grid - lon) ** 2) * EARTH_RADIUS * np.pi / 180
    decay_mask = dists <= radical_decay
    decay_values = np.maximum(0, 1 - (dists / radical_decay))
    return np.where(decay_mask, aqi * decay_values, 0)

def interpolate_chunk(lat_chunk, lon_chunk, points, radical_decay):
    """Interpolate AQI values for a chunk of the grid."""
    chunk_result = np.zeros((len(lat_chunk), len(lon_chunk)), dtype=np.float32)
    for point in points:
        lat, lon, aqi = point['lat'], point['lon'], float(point['aqi'])
        lat_grid, lon_grid = np.meshgrid(lat_chunk, lon_chunk, indexing='ij')
        chunk_result += calculate_decay(lat_grid, lon_grid, lat, lon, aqi, radical_decay)
    return chunk_result

def interpolate_aqi(grid, points, radical_decay):
    """Interpolate AQI values onto the grid in chunks."""
    lat_range, lon_range = grid
    num_chunks = 10  # Adjust the number of chunks to balance memory and performance

    lat_chunks = np.array_split(lat_range, num_chunks)
    lon_chunks = np.array_split(lon_range, num_chunks)

    result = np.zeros((len(lat_range), len(lon_range)), dtype=np.float32)
    for lat_chunk in lat_chunks:
        for lon_chunk in lon_chunks:
            result_chunk = interpolate_chunk(lat_chunk, lon_chunk, points, radical_decay)
            result[
                lat_range.searchsorted(lat_chunk[0]):lat_range.searchsorted(lat_chunk[-1]) + 1,
                lon_range.searchsorted(lon_chunk[0]):lon_range.searchsorted(lon_chunk[-1]) + 1,
            ] += result_chunk

    return result

def generate_heatmap(grid, values):
    """Generate a heatmap image from the interpolated grid values."""
    lat_range, lon_range = grid

    # Define colors and bounds for AQI levels
    color_list = ["green", "yellow", "orange", "red", "purple", "maroon"]
    cmap = mcolors.LinearSegmentedColormap.from_list("smooth_colormap", color_list, N=256)

    # Normalize values for coloring
    normalized_values = (values - np.min(values)) / (np.max(values) - np.min(values))

    # Convert to image using colormap
    heatmap = cmap(normalized_values)
    image = Image.fromarray((heatmap[:, :, :3] * 255).astype(np.uint8), mode='RGB')
    image.save('heatmap_image.png')
    print("Heatmap image saved as 'heatmap_image.png'")
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

def main(json_file, lat_min, lat_max, lon_min, lon_max, accuracy_m, radical_decay):
    start_time = time.time()

    with open(json_file, 'r') as f:
        points = json.load(f)

    grid = create_grid(lat_min, lat_max, lon_min, lon_max, accuracy_m)
    interpolated_values = interpolate_aqi(grid, points, radical_decay)
    heatmap_image = generate_heatmap(grid, interpolated_values)

    heatmap_image = Image.open("heatmap_image.png")

    folium_map = overlay_heatmap_on_map(heatmap_image, lat_min, lat_max, lon_min, lon_max, points)
    folium_map.save('aqi_heatmap_with_points.html')

    elapsed_time = time.time() - start_time
    print(f"Heatmap with points saved as 'aqi_heatmap_with_points.html' in {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main(
        json_file='car_data.json',
        lat_min=38.205683,
        lat_max=38.294508,
        lon_min=21.688356,
        lon_max=21.830913,
        accuracy_m=5,  # Adjust resolution to reduce memory usage
        radical_decay=15
    )
