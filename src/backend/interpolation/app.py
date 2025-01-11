from flask import Flask, render_template_string
from ipyleaflet import Map, Heatmap
from datetime import datetime, timedelta
import pytz
import numpy as np
from influxdb_client import InfluxDBClient
import os
from dotenv import load_dotenv
from MathFunctions import Validations

# Load environment variables
load_dotenv()

# InfluxDB Configuration
token = os.getenv("GRAFANA_READ_AND_WRITE")
org = "students"
BUCKET = "APARS"
client = InfluxDBClient(url=os.getenv("INFLUX_URL"), token=token, org=org)

# Flask app setup
app = Flask(__name__)

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
                aqi = record.values.get("aqi")
                lat = record.values.get("latitude")
                lon = record.values.get("longitude")
                if Validations.isNumeric(aqi) and Validations.isNumeric(lat) and Validations.isNumeric(lon):
                    data.append({
                        "timestamp": record.get_time(),
                        "aqi": aqi,
                        "latitude": lat,
                        "longitude": lon,
                    })
                else:
                    print("Corrupted data")

        return data
    except Exception as e:
        print(f"Error querying InfluxDB: {e}")
        return []

# Create heatmap
def create_heatmap(data):
    # Prepare heatmap data as (latitude, longitude, intensity)
    heatmap_data = [
        (d["latitude"], d["longitude"], d["aqi"]) for d in data if d["aqi"] is not None
    ]

    # Normalize AQI values to 0-1 range for visualization
    normalized_data = [
        (lat, lon, min(1.0, max(0.0, (aqi / 500))))  # AQI capped at 500 for normalization
        for lat, lon, aqi in heatmap_data
    ]

    # Define the colormap for AQI categories
    colors = ["green", "yellow", "orange", "red", "maroon", "purple"]
    bounds = [0, 50, 100, 150, 200, 300, 500]

    # Create the map
    center = [37.9838, 23.7275]  # Example: Athens center
    m = Map(center=center, zoom=6)

    heatmap = Heatmap(
        locations=[[lat, lon, intensity] for lat, lon, intensity in normalized_data],
        gradient={
            0.0: "green",
            0.1: "yellow",
            0.2: "orange",
            0.3: "red",
            0.4: "maroon",
            0.5: "purple",
        },
        radius=15
    )

    m.add_layer(heatmap)
    return m

@app.route("/")
def display_map():
    # Query data from cars and stations
    car_data = query_influxdb(BUCKET, "car_metrics", ["aqi", "latitude", "longitude"], 10)
    station_data = query_influxdb(BUCKET, "station_aqi", ["aqi", "latitude", "longitude"], 10)

    # Combine data
    combined_data = car_data + station_data

    # Create the heatmap
    map_widget = create_heatmap(combined_data)

    # Generate HTML representation of the map
    map_html = map_widget._repr_html_()

    # Render map in Flask
    return render_template_string(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Heatmap</title>
        </head>
        <body>
            <h1>AQI Heatmap</h1>
            {{ map_html | safe }}
        </body>
        </html>
        """,
        map_html=map_html
    )

if __name__ == "__main__":
    app.run(debug=True)
