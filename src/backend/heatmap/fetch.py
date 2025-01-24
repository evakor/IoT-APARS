from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, QueryApi
import pandas as pd
import json
import logging
import os
from dotenv import load_dotenv

import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import numpy as np
from scipy.interpolate import griddata
import rasterio
from rasterio.transform import from_origin

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("INFLUXDB-RETRIEVER")

# InfluxDB credentials and setup
token = os.getenv('GRAFANA_READ_AND_WRITE')
org = 'students'
bucket = 'APARS'
client = InfluxDBClient(url=os.getenv("INFLUX_URL"), token=token, org=org)
query_api = client.query_api()

def query_last_hour_data():
    """
    Query data from InfluxDB for the last hour.
    """
    try:
        # Calculate time range for the last hour
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)

        # Flux query for the last hour data
        flux_query = f'''
        from(bucket: "{bucket}")
        |> range(start: {one_hour_ago.isoformat()}, stop: {now.isoformat()})
        |> filter(fn: (r) => r._measurement == "car_metrics")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        flux_query = '''
        from(bucket: "APARS")
        |> range(start: 0)  // No specific time range
        |> filter(fn: (r) => r._measurement == "car_metrics")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> limit(n: 1000)
        '''

        # Execute query
        result = query_api.query(flux_query)
        logger.info("Data successfully retrieved from InfluxDB.")

        # Parse result to a pandas DataFrame
        data = []
        for table in result:
            for record in table.records:
                data.append(record.values)

        df = pd.DataFrame(data)

        # Keep only relevant columns (adjust as needed)
        if not df.empty:
            df = df[["id", "_time", "latitude", "longitude", "pm1", "pm25", "pm10", "co", "co2", "aqi"]]
            df.rename(columns={"_time": "timestamp"}, inplace=True)
            logger.info(f"Retrieved {len(df)} records.")
        else:
            logger.warning("No data found for the last hour.")
        
        return df

    except Exception as e:
        logger.error(f"Error querying InfluxDB: {e}")
        return pd.DataFrame()


last_hour_data = query_last_hour_data()
if last_hour_data.empty:
    print("paparia")
    quit()
# Continue with processing as DataFrame
df = last_hour_data
# Keep only necessary columns
df = df[['latitude', 'longitude', 'aqi']]  # Adjust based on required fields


#------------------------------------------------------
# Step 2: Round Coordinates to 4 Decimal Places (Tiling)
#------------------------------------------------------
df['lat_tile'] = df['latitude'].round(4)
df['lon_tile'] = df['longitude'].round(4)

# Group by these tile coordinates and average rssi
grouped = df.groupby(['lat_tile', 'lon_tile'], as_index=False).agg({'aqi': 'mean'})

#------------------------------------------------------
# Step 3: Create a GeoDataFrame of the Averaged Points
#------------------------------------------------------
geometry = [Point(xy) for xy in zip(grouped['lon_tile'], grouped['lat_tile'])]
gdf = gpd.GeoDataFrame(grouped, geometry=geometry)
gdf.set_crs(epsg=4326, inplace=True)  # WGS84

#------------------------------------------------------
# Step 4: Interpolate to Create a Continuous Scalar Field (Raster)
#------------------------------------------------------
# Extract coordinates and values
points = np.array(list(zip(gdf['lon_tile'], gdf['lat_tile'])))
values = gdf['aqi'].values

# Define a grid over the area of interest
min_lon, min_lat, max_lon, max_lat = gdf.total_bounds
num_cols = 3000  # choose resolution (number of pixels horizontally)
num_rows = 3000  # choose resolution (number of pixels vertically)

lon_lin = np.linspace(min_lon, max_lon, num_cols)
lat_lin = np.linspace(min_lat, max_lat, num_rows)
lon_grid, lat_grid = np.meshgrid(lon_lin, lat_lin)

# Perform interpolation
rssi_grid = griddata(points, values, (lon_grid, lat_grid), method="linear")

#------------------------------------------------------
# Step 5: Export the Raster as GeoTIFF
#------------------------------------------------------
# Define transform (affine) for raster
# Note: lat_grid[0,0], lon_grid[0,0] is top-left corner of the grid.
# Raster origin usually top-left. lat decreases going down, so we have to be careful.
x_res = (max_lon - min_lon) / (num_cols - 1)
y_res = (max_lat - min_lat) / (num_rows - 1)

transform = from_origin(min_lon, max_lat, x_res, y_res)

# Set CRS to EPSG:4326
raster_crs = "EPSG:4326"

# Create a single-band raster
new_dataset = rasterio.open(
    'aqi_field.tif',
    'w',
    driver='GTiff',
    height=num_rows,
    width=num_cols,
    count=1,
    dtype=str(rssi_grid.dtype),
    crs=raster_crs,
    transform=transform,
)

# Write the interpolated values to the raster
new_dataset.write(rssi_grid, 1)
new_dataset.close()

#------------------------------------------------------
# Step 6: Visualization as Semi-Transparent Overlay
#------------------------------------------------------

import rasterio
import numpy as np

# Open the existing raster
with rasterio.open('aqi_field.tif', 'r+') as src:
    data = src.read(1)
    # Create an alpha channel (fully opaque = 255, here we choose 128 for ~50% transparency)
    alpha = np.full(data.shape, 128, dtype=np.uint8)
    
    # Update count if necessary (if you are adding a new band)
    # Make sure your file is opened in 'r+' mode and support adding bands
    # Some formats may require creating a new file for adding alpha
    
    # Example: Creating a new file with alpha channel
    profile = src.profile
    profile.update(count=2, dtype='uint8')  # 1 band data + 1 band alpha

# Write data + alpha to a new GeoTIFF
with rasterio.open('aqi_field_alpha.tif', 'w', **profile) as dst:
    # Normalize rssi values into a displayable range (e.g., 0-255)
    # Here assume data was float and we need to scale it, otherwise just cast
    # For simplicity, let's just write a grayscale approximation
    # Normalize scalar_field safely
    norm_scalar_field = rssi_grid.copy()

    # Replace NaN with a placeholder value (e.g., 0 or minimum valid value)
    nan_mask = np.isnan(norm_scalar_field)
    norm_scalar_field[nan_mask] = np.nanmin(rssi_grid)  # Replace NaNs with the minimum valid value

    # Perform normalization
    norm_data = ((norm_scalar_field - np.nanmin(norm_scalar_field)) / 
                (np.nanmax(norm_scalar_field) - np.nanmin(norm_scalar_field)) * 255).astype(np.uint8)

    dst.write(norm_data, 1)
    dst.write(alpha, 2)


import folium
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import imageio

# Load the raster file
raster_file = 'aqi_field.tif'

# Open the GeoTIFF and extract bounds
with rasterio.open(raster_file) as src:
    bounds = src.bounds  # Bounding box of the raster
    data = src.read(1)   # Read the first band

# Replace NaNs in data with minimum value
nan_mask = np.isnan(data)
data[nan_mask] = np.nanmin(data)

# Normalize the data for color mapping (0-1)
norm = Normalize(vmin=np.nanmin(data), vmax=np.nanmax(data))
normalized_data = norm(data)

# Apply a colormap (e.g., 'plasma' for heatmap)
cmap = plt.cm.coolwarm  # You can replace 'plasma' with 'coolwarm' or others
heatmap = cmap(normalized_data)

# Convert the RGBA heatmap to an RGB image (uint8)
heatmap_rgb = (heatmap[:, :, :3] * 255).astype(np.uint8)

# Save the heatmap as an image for overlay
overlay_image = 'aqi_overlay_colored.png'
imageio.imwrite(overlay_image, heatmap_rgb)

# Calculate bounds for folium overlay
min_lat, max_lat = bounds.bottom, bounds.top
min_lon, max_lon = bounds.left, bounds.right

# Create a base map centered on the data
map_center = [(min_lat + max_lat) / 2, (min_lon + max_lon) / 2]
m = folium.Map(location=map_center, zoom_start=19)
# Automatically adjust the zoom to fit all data
#m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])


# Add the colorized overlay image to the map
folium.raster_layers.ImageOverlay(
    image=overlay_image,
    bounds=[[min_lat, min_lon], [max_lat, max_lon]],
    opacity=0.8
).add_to(m)

import branca.colormap as cm

# Create a color scale based on RSSI values
boundaries = [0, 50, 100, 150, 200, 300, 500]
colors = ["green", "yellow", "orange", "red", "maroon", "purple"]

# Create a custom LinearColormap with fixed boundaries
color_scale = cm.StepColormap(
    colors=colors,
    index=boundaries,
    vmin=min(boundaries),
    vmax=max(boundaries),
    caption='AQI Signal Strength'
)


# Add the color scale to the map
color_scale.add_to(m)

# Add a layer control
folium.LayerControl().add_to(m)

# Save and display the map
m.save('map_with_colored_aqi.html')