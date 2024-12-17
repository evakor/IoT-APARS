import numpy as np
import matplotlib.pyplot as plt
import json
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import LinearSegmentedColormap
import netCDF4 as nc
import os
from dotenv import load_dotenv

load_dotenv()

west = float(os.getenv('WEST'))
east = float(os.getenv('EAST'))
south = float(os.getenv('SOUTH'))
north = float(os.getenv('NORTH'))
resolution = 0.001  # Approx. 100m resolution in degrees
base_value = 10

# Create a grid of latitude and longitude
lats = np.arange(south, north, resolution)
lons = np.arange(west, east, resolution*2)
lon_grid, lat_grid = np.meshgrid(lons, lats)

grid = np.full(lon_grid.shape, base_value, dtype=float)

# Load AQI stations from stations.json
with open("station_aqi_data.json", "r") as file:
    stations_data = json.load(file)

# Filter stations within the grid region
stations = [
    {"lat": station["lat"], "lon": station["lon"], "value": int(station["aqi"] if station['aqi'] != '-' else 40)}
    for station in stations_data
    if south <= station["lat"] <= north and west <= station["lon"] <= east
]

influence_radius_km = 0.01  # 200m in degrees

# Helper function to calculate radial decay
def radial_decay(distance, max_distance):
    if distance > max_distance:
        return 0
    return 1 - (distance / max_distance)

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

# Apply station influences to the grid
for station in stations:
    station_lat = station["lat"]
    station_lon = station["lon"]
    station_value = station["value"]
    print(f"{stations.index(station)+1}/{len(stations)} stations  ")
    for i in range(len(lats)):
        printProgressBar(i+1, len(lats), prefix = 'Progress:', suffix = 'Complete', length = 50)
        for j in range(len(lons)):
            distance = np.sqrt((lats[i] - station_lat)**2 + (lons[j] - station_lon)**2)
            decay = radial_decay(distance, influence_radius_km)
            grid[i, j] += decay * (station_value - base_value)

# Define custom color map for smooth transitions
colors = ["green", "yellow", "orange", "red", "maroon", "purple"]
values = [0, 50, 100, 150, 200, 300, 500]
cmap = LinearSegmentedColormap.from_list("smooth_aqi", list(zip(np.linspace(0, 1, len(colors)), colors)))

# Function to save heatmap to .nc file
def save_to_nc(file_name, lats, lons, grid):
    with nc.Dataset(file_name, "w", format="NETCDF4") as dataset:
        # Create dimensions
        lat_dim = dataset.createDimension("lat", len(lats))
        lon_dim = dataset.createDimension("lon", len(lons))

        # Create variables
        latitudes = dataset.createVariable("lat", "f4", ("lat",))
        longitudes = dataset.createVariable("lon", "f4", ("lon",))
        aqi_values = dataset.createVariable("aqi", "f4", ("lat", "lon"))

        # Assign data to variables
        latitudes[:] = lats
        longitudes[:] = lons
        aqi_values[:, :] = grid

        # Add attributes
        dataset.description = "AQI Heatmap"
        latitudes.units = "degrees_north"
        longitudes.units = "degrees_east"
        aqi_values.units = "AQI"

# Save the grid to a .nc file
save_to_nc("aqi_heatmap.nc", lats, lons, grid)

from matplotlib.colors import BoundaryNorm

# Define the color boundaries and colors
colors = ["green", "yellow", "orange", "red", "maroon", "purple"]
values = [0, 50, 100, 150, 200, 300, 500]  # AQI thresholds

# Create a colormap and normalization for the given boundaries
cmap = LinearSegmentedColormap.from_list("aqi_boundaries", colors, N=len(colors))
norm = BoundaryNorm(values, ncolors=cmap.N, clip=True)

# Plot the interpolated map on top of the region map
plt.figure(figsize=(12, 10))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([west, east, south, north], crs=ccrs.PlateCarree())

# Add geographical features
ax.add_feature(cfeature.LAND, facecolor="lightgray")
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')
ax.add_feature(cfeature.LAKES, edgecolor='black')
ax.add_feature(cfeature.RIVERS)

# Plot the heatmap with sharp transitions at AQI thresholds
heatmap = ax.contourf(lon_grid, lat_grid, grid, levels=values, cmap=cmap, norm=norm, transform=ccrs.PlateCarree())

# Add color bar
cbar = plt.colorbar(heatmap, ax=ax, orientation="vertical", shrink=0.7, pad=0.05)
cbar.set_label("AQI Value")
cbar.set_ticks(values)
cbar.set_ticklabels(values)

# Add station markers
for station in stations:
    plt.plot(
        station["lon"], station["lat"],
        marker="x", color="black", markersize=8,
        label=station["value"] if "value" not in plt.gca().get_legend_handles_labels()[1] else ""
    )

plt.title("Interpolated AQI Map Over Region with AQI Thresholds")
plt.legend(title="Stations", loc="lower right")
plt.show()

