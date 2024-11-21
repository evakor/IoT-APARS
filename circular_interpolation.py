import matplotlib.pyplot as plt
import requests
from scipy.interpolate import griddata
import numpy as np
import matplotlib.colors as mcolors
import os
import json
import math
from scipy.spatial import cKDTree
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import psycopg2


accuracy = 10
lat_min, lat_max = -90, 90
lon_min, lon_max = -180, 180
apiToken = 'ecaa84eb1dbceeaf83c27c213369e4cf372c03c8'
url = f"https://api.waqi.info/map/bounds/?token={apiToken}&latlng={lat_min},{lon_min},{lat_max},{lon_max}"
data_file = "data.json"
earth_radius_km = 6371.0  # Earth's radius in km
radius_km = 4.0  # Radius of AQI influence
default_aqi = 5  # Default AQI value

DB_CONFIG = {
    'dbname': 'APARS',
    'user': 'admin',
    'password': 'admin',
    'host': 'localhost',  # Or your DB host
    'port': 5432
}

def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        exit()

def save_to_db(data):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.executemany(
            "INSERT INTO aqi_stations (latitude, longitude, aqi) VALUES (%s, %s, %s)",
            data
        )
        conn.commit()
        print("Data saved to the database successfully.")
    except Exception as e:
        print(f"Error saving data to the database: {e}")
    finally:
        cursor.close()
        conn.close()

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return earth_radius_km * c

if os.path.exists(data_file):
    with open(data_file, "r") as file:
        data = json.load(file)
else:
    print("Getting data...")
    response = requests.get(url)
    data = response.json()['data']
    with open(data_file, "w") as file:
        json.dump(data, file)

latitudes = [point['lat'] for point in data]
longitudes = [point['lon'] for point in data]
aqi_values = [int(point['aqi'] if point['aqi'] != '-' else 40) for point in data]

grid_lat, grid_lon = np.mgrid[
    min(latitudes):max(latitudes):(accuracy*1j/2), 
    min(longitudes):max(longitudes):(accuracy*1j)
]
grid_shape = grid_lat.shape
combined_aqi = np.full(grid_shape, default_aqi)  # Initialize with default AQI

station_coords = np.array(list(zip(latitudes, longitudes)))
station_tree = cKDTree(station_coords)

db_data = []

for i in range(grid_shape[0]):
    if i%5:
        print(i/grid_shape[0] * 100)
    for j in range(grid_shape[1]):
        grid_point = (grid_lat[i, j], grid_lon[i, j])
        
        # Find nearest stations within the radius
        distances, indices = station_tree.query(
            [grid_point], k=len(latitudes), distance_upper_bound=radius_km
        )
        
        # If any station is within the radius, assign AQI with smoothing
        for idx, dist in zip(indices[0], distances[0]):
            if idx != len(latitudes):  # Ensure valid indices
                influence = max(0, 1 - (dist / radius_km))  # Radial decay
                combined_aqi[i, j] += (aqi_values[idx] - default_aqi) * influence
        
        # Append to database list
        db_data.append((grid_lat[i, j], grid_lon[i, j], int(combined_aqi[i, j])))


print(len(db_data))
print(db_data)
# save_to_db(db_data)

# Define a custom colormap based on AQI ranges
color_list = ["green", "yellow", "orange", "red", "purple", "maroon"]
bounds = [0, 50, 100, 150, 200, 300, 500]
norm = mcolors.BoundaryNorm(bounds, len(color_list))
cmap = mcolors.ListedColormap(color_list)

# Plot using Cartopy for basemap
fig, ax = plt.subplots(figsize=(15, 8), subplot_kw={'projection': ccrs.PlateCarree()})
ax.set_extent([min(longitudes), max(longitudes), min(latitudes), max(latitudes)], crs=ccrs.PlateCarree())

# Add basemap features
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.LAND, facecolor='lightgray')
ax.add_feature(cfeature.OCEAN, facecolor='lightblue')

# Plot AQI layer semi-transparently
aqi_plot = ax.imshow(
    combined_aqi,
    extent=(min(longitudes), max(longitudes), min(latitudes), max(latitudes)),
    origin='lower',
    cmap=cmap,
    norm=norm,
    alpha=0.6,  # Set transparency
    transform=ccrs.PlateCarree()
)

# Add colorbar
cbar = plt.colorbar(aqi_plot, ax=ax, orientation='vertical', pad=0.05, shrink=0.7)
cbar.set_label('AQI', rotation=90)

# Overlay station points
ax.scatter(longitudes, latitudes, color="black", label="Station Locations", s=10, transform=ccrs.PlateCarree())

# Title and labels
plt.title("Interpolated AQI Heatmap with Circular Influence")
plt.legend()
plt.show()
