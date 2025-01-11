from datetime import datetime, timedelta
import pytz
import numpy as np
from influxdb_client import InfluxDBClient, Point, WritePrecision
from ProgressBar import ProgressBar
from MathFunctions import Calculations
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
import geopandas as gpd
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import contextily as ctx
from Converters import Converters

load_dotenv()

# InfluxDB Configuration
token = os.getenv("GRAFANA_READ_AND_WRITE")
org = "students"
BUCKET = "APARS"
client = InfluxDBClient(url=os.getenv("INFLUX_URL"), token=token, org=org)

# Utility to convert to UTC
def to_utc(timestamp):
    try:
        if timestamp.endswith("Z"):
            utc_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
            adjusted_time = utc_time - timedelta(hours=2)
            return adjusted_time.isoformat(timespec='microseconds')
        else:
            local_time = datetime.fromisoformat(timestamp)
            utc_plus_2 = pytz.timezone('Europe/Athens')
            localized_time = utc_plus_2.localize(local_time)
            utc_time = localized_time.astimezone(pytz.utc)
            return utc_time.replace(tzinfo=None).isoformat(timespec='microseconds')
    except Exception as e:
        print(f"Error converting to UTC: {e}")
        return timestamp

# Query InfluxDB data
def query_influxdb(bucket, measurement, fields, last_n_minutes):
    try:
        query_api = client.query_api()

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=last_n_minutes)

        start_time_str = start_time.isoformat() + "Z"
        end_time_str = end_time.isoformat() + "Z"

        field_filters = " or ".join([f'r["_field"] == "{field}"' for field in fields])

        flux_query = f'''
        from(bucket: "{bucket}")
          |> range(start: {start_time_str}, stop: {end_time_str})
          |> filter(fn: (r) => r["_measurement"] == "{measurement}")
          |> filter(fn: (r) => {field_filters})
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''

        result = query_api.query(flux_query)
        data = []

        for table in result:
            for record in table.records:
                data.append({
                    "timestamp": record.get_time(),
                    "aqi": record.values.get("aqi"),
                    "latitude": record.values.get("latitude"),
                    "longitude": record.values.get("longitude"),
                })

        return data
    except Exception as e:
        print(f"Error querying InfluxDB: {e}")
        return []

# Interpolation function
def interpolate_points(points, influence_radius_km, west, east, south, north, resolution=0.001):
    pb = ProgressBar()

    lats = np.arange(south, north, resolution)
    lons = np.arange(west, east, resolution * 2)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    grid = np.full(lon_grid.shape, 10, dtype=float)  # Base AQI value

    clip_points = [
        {"lat": p["latitude"], "lon": p["longitude"], "value": p["aqi"], "radius": r}
        for point_set, r in zip(points, influence_radius_km)
        for p in point_set
        if south <= p["latitude"] <= north and west <= p["longitude"] <= east
    ]

    print(f"Clipping points to {len(clip_points)}")

    for point in clip_points:
        for i, lat in enumerate(lats):
            pb.print(i + 1, len(lats), prefix="Progress:", suffix="Complete", length=50)
            for j, lon in enumerate(lons):
                distance = np.sqrt((lat - point["lat"]) ** 2 + (lon - point["lon"]) ** 2)
                decay = Calculations.radial_decay(distance, point["radius"])
                grid[i, j] += decay * (point["value"] - 10)  # Base AQI value is 10

    return lats, lons, grid

# Save heatmap to InfluxDB
def save_heatmap_to_influx(lats, lons, grid, timestamp):
    pb = ProgressBar()
    try:
        write_api = client.write_api()
        points = []

        for i, lat in enumerate(lats):
            pb.print(i + 1, len(lats), prefix="Progress:", suffix="Complete", length=50)
            for j, lon in enumerate(lons):
                point = Point("heatmap") \
                    .field("aqi", float(grid[i, j])) \
                    .field("lat", float(lat)) \
                    .field("lon", float(lon)) \
                    .time(to_utc(timestamp))
                
                points.append(point)

                write_api.write(bucket=BUCKET, org=org, record=point)

        print("Heatmap data saved to InfluxDB.")
    except Exception as e:
        print(f"Error saving heatmap: {e}")

# Plot data
def plot_interpolated_data(lats, lons, grid, west, east, south, north):
    # Define the colormap and normalization
    cmap = LinearSegmentedColormap.from_list(
        "aqi_boundaries", 
        ["green", "yellow", "orange", "red", "maroon", "purple"], 
        N=6
    )
    norm = BoundaryNorm([0, 50, 100, 150, 200, 300, 500], ncolors=cmap.N, clip=True)
    
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot the interpolated grid with transparency (alpha)
    mesh = ax.pcolormesh(
        lons, lats, grid, cmap=cmap, norm=norm, shading="auto", alpha=0.6
    )
    
    # Add a basemap from OpenStreetMap
    ax.set_xlim(west, east)
    ax.set_ylim(south, north)
    
    # Convert geographical coordinates (lat/lon) to Web Mercator (EPSG:3857)
    ctx.add_basemap(
        ax,
        crs="EPSG:4326",  # Geographic coordinate system
        source=ctx.providers.OpenStreetMap.Mapnik
    )
    
    # Add a colorbar
    cbar = fig.colorbar(mesh, ax=ax, label="AQI")
    
    # Add titles and labels
    ax.set_title("Interpolated AQI Data")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    
    # Show the plot
    plt.show()

if __name__ == "__main__":
    car_data = query_influxdb(BUCKET, "car_metrics", ["aqi", "latitude", "longitude"], 10)
    station_data = query_influxdb(BUCKET, "station_aqi", ["aqi", "latitude", "longitude"], 10)

    west = float(os.getenv("WEST"))
    east = float(os.getenv("EAST"))
    south = float(os.getenv("SOUTH"))
    north = float(os.getenv("NORTH"))

    south, north = 34.8021, 41.7489
    west, east = 19.3646, 29.6425

    lats, lons, grid = interpolate_points([car_data, station_data], [0.01, 0.02], west, east, south, north)
    # for i in range(10):
    #     for j in range(10):
    #         print(f"{lats[i]}, {lons[j]} -> {grid[i][j]}")

    #save_heatmap_to_influx(lats, lons, grid, datetime.utcnow().isoformat() + "Z")
    #plot_interpolated_data(lats, lons, grid, west, east, south, north)
