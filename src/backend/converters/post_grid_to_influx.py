import netCDF4 as nc
import requests
import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime


def parse_nc_file(file_name):
    dataset = nc.Dataset(file_name, "r")
    lats = dataset.variables["lat"][:]
    lons = dataset.variables["lon"][:]
    aqi_data = dataset.variables["aqi"][:]
    return lats, lons, aqi_data


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


# def write_to_influxdb(lats, lons, aqi_data):
#     INFLUXDB_URL = "http://labserver.sense-campus.gr:8086/"
#     org = "students"
#     bucket = "OMADA 13- APARS"
#     token = "3C4tpppV6mLJ85ArlFx4Cazj55KnM2xWJcuTnCCZLfsSalCym88_C1tSERzuLUzZ6IWth9Y4_x_tx_FWiq8jNA=="
#     client = InfluxDBClient(url="http://labserver.sense-campus.gr:8086", token=token, org=org)
#     write_api = client.write_api(write_options=SYNCHRONOUS)


#     timestamp = int(pd.Timestamp.now().timestamp())

#     # Prepare the line protocol data
#     lines = []
#     for i, lat in enumerate(lats):
#         printProgressBar(i+1, len(lats), prefix = 'Progress:', suffix = 'Complete', length = 50)
#         for j, lon in enumerate(lons):
#             aqi_value = aqi_data[i][j]
#             line = f"aqi,lat={lat},lon={lon} aqi_value={aqi_value} {timestamp}"
#             lines.append(line)

#     # Send the data to InfluxDB
#     data = "\n".join(lines)
#     print(len(lines))
#     for line in lines:
#         response = requests.post(INFLUXDB_URL, data=line, timeout=15)

#         if response.status_code == 204:
#             print("Data written successfully to InfluxDB!")
#         else:
#             print(f"Failed to write data to InfluxDB: {response.status_code}, {response.text}")
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision

from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
import numpy as np

def write_to_influxdb(lats, lons, aqi_data):
    # InfluxDB configurations
    INFLUXDB_URL = "http://labserver.sense-campus.gr:8086/"
    org = "students"
    bucket = "OMADA 13- APARS"
    token = "3C4tpppV6mLJ85ArlFx4Cazj55KnM2xWJcuTnCCZLfsSalCym88_C1tSERzuLUzZ6IWth9Y4_x_tx_FWiq8jNA=="
    
    # Initialize InfluxDB client and write API
    client = InfluxDBClient(url=INFLUXDB_URL, token=token, org=org)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    # Current timestamp in nanoseconds
    timestamp = datetime.utcnow()
    
    # Batch size
    batch_size = 5000
    points = []

    # Iterate over latitudes and longitudes to write AQI data
    total_points = len(lats) * len(lons)
    processed_points = 0

    for i, lat in enumerate(lats):
        for j, lon in enumerate(lons):
            aqi_value = aqi_data[i][j]
            
            # Create a Point object for each data point
            point = Point("aqi") \
                .field("lat", lat) \
                .field("lon", lon) \
                .field("aqi_value", float(aqi_value)) \
                .time(timestamp, WritePrecision.NS)
            
            points.append(point)
            processed_points += 1

            # Write in batches
            if len(points) >= batch_size:
                try:
                    write_api.write(bucket=bucket, org=org, record=points)
                    points = []  # Clear the batch
                except Exception as e:
                    print(f"Error writing batch to InfluxDB: {e}")

                # Update progress bar
                printProgressBar(processed_points, total_points, prefix='Progress:', suffix='Complete', length=50)

    # Write any remaining points
    if points:
        try:
            write_api.write(bucket=bucket, org=org, record=points)
        except Exception as e:
            print(f"Error writing final batch to InfluxDB: {e}")

    print("All data written successfully to InfluxDB!")

if __name__ == "__main__":
    file_name = "aqi_heatmap.nc"

    lats, lons, aqi_data = parse_nc_file(file_name)

    write_to_influxdb(lats, lons, aqi_data)
