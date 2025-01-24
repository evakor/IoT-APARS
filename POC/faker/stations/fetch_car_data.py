import json
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, QueryApi
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("INFLUXDB-TO-JSON")

# InfluxDB credentials and setup
token = os.getenv('GRAFANA_READ_AND_WRITE')
org = 'students'
bucket = 'APARS'
client = InfluxDBClient(url=os.getenv("INFLUX_URL"), token=token, org=org)
query_api = client.query_api()

def query_last_hour_data():
    """
    Query data from InfluxDB for the last hour and format it as required.
    """
    try:
        flux_query = '''
        from(bucket: "APARS")
        |> range(start: 0)  // No specific time range
        |> filter(fn: (r) => r["_measurement"] == "car_metrics")
        |> filter(fn: (r) => r["_field"] == "aqi" or r["_field"] == "latitude" or r["_field"] == "longitude")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> limit(n: 1000)
        '''

        result = query_api.query(flux_query)
        logger.info("Data successfully retrieved from InfluxDB.")

        data = []
        for table in result:
            for record in table.records:
                data.append({
                    "lat": record.values.get("latitude"),
                    "lon": record.values.get("longitude"),
                    "aqi": record.values.get("aqi"),
                })

        return data

    except Exception as e:
        logger.error(f"Error querying InfluxDB: {e}")
        return []

def save_to_json(data, filename="car_data.json"):
    """
    Save the retrieved data to a JSON file.
    """
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        logger.info(f"Data successfully saved to {filename}.")
    except Exception as e:
        logger.error(f"Error saving data to JSON: {e}")

if __name__ == "__main__":
    data = query_last_hour_data()
    if data:
        save_to_json(data)
    else:
        logger.error("No data retrieved. JSON file was not created.")
