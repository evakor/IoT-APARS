import json
import numpy as np
import folium
from scipy.spatial import distance
from PIL import Image
import matplotlib.colors as mcolors
from multiprocessing import Pool, cpu_count

# Constants
EARTH_RADIUS = 6371000  # Radius of the Earth in meters

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

    with Pool(cpu_count()) as pool:
        args = [(lat_range, lon_range, point, radical_decay) for point in points]
        results = pool.map(interpolate_point, args)

    for result in results:
        interpolated_grid += result

    return interpolated_grid

def generate_heatmap(grid, values):
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
    return image

def overlay_heatmap_on_map(image, lat_min, lat_max, lon_min, lon_max):
    """Overlay the heatmap on a Folium map."""
    folium_map = folium.Map(location=[(lat_min + lat_max) / 2, (lon_min + lon_max) / 2], zoom_start=12)
    img_overlay = folium.raster_layers.ImageOverlay(
        image=np.array(image),
        bounds=[[lat_min, lon_min], [lat_max, lon_max]],
        opacity=0.6,
        interactive=True,
    )
    img_overlay.add_to(folium_map)
    return folium_map

# Main script
def main(json_file, lat_min, lat_max, lon_min, lon_max, accuracy_m, radical_decay):
    with open(json_file, 'r') as f:
        points = json.load(f)

    grid = create_grid(lat_min, lat_max, lon_min, lon_max, accuracy_m)
    interpolated_values = interpolate_aqi(grid, points, radical_decay)
    heatmap_image = generate_heatmap(grid, interpolated_values)

    folium_map = overlay_heatmap_on_map(heatmap_image, lat_min, lat_max, lon_min, lon_max)
    folium_map.save('aqi_heatmap.html')
    print("Heatmap saved as 'aqi_heatmap.html'")


if __name__ == "__main__":
    main(
        json_file='car_data.json',
        lat_min=38.205683,
        lat_max=38.294508,
        lon_min=21.688356,
        lon_max=21.830913,
        accuracy_m=5,
        radical_decay=30
    )