import os
from influxdb_client import InfluxDBClient
import logging
import logging.config
from dotenv import load_dotenv

load_dotenv()

class InfluxDataFetcher:
    def __init__(self):
        self.client = InfluxDBClient(url=os.getenv("INFLUX_URL"), token=os.getenv('GRAFANA_READ_AND_WRITE'), org='students')
        self.query_api = self.client.query_api()
        self.bucket = 'APARS'

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_config_path = os.path.join(base_dir, 'logging.conf')

        if os.path.exists(log_config_path):
            logging.config.fileConfig(log_config_path)
        else:
            logging.basicConfig(level=logging.INFO)

        self.logger = logging.getLogger("HEATMAP")

    def fetch_latest_patras_station_data(self):
        query = f'''
        from(bucket: "APARS")
        |> range(start: -1d)
        |> filter(fn: (r) => r["_measurement"] == "patras_station_aqi")
        |> filter(fn: (r) => r["_field"] == "aqi" or r["_field"] == "latitude" or r["_field"] == "longitude")
        |> group(columns: ["id", "_field"])        // Group by ID (tag) and field
        |> last()                                  // Get the latest entry for each ID-field
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value") 
        |> keep(columns: ["id", "_time", "aqi", "latitude", "longitude"])  // Ensure id is included
        '''
        print("HEATMAP - Fetching data from patras_station_aqi")
        result = self.query_api.query(org='students', query=query)
        return self.format_results(result)

    def fetch_latest_station_data(self):
        query = f'''
        from(bucket: "APARS")
        |> range(start: -30d)
        |> filter(fn: (r) => r["_measurement"] == "station_aqi")
        |> filter(fn: (r) => r["_field"] == "aqi" or r["_field"] == "latitude" or r["_field"] == "longitude")
        |> group(columns: ["id", "_field"])        // Group by ID (tag) and field
        |> last()                                  // Get the latest entry for each ID-field
        |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value") 
        |> keep(columns: ["id", "_time", "aqi", "latitude", "longitude"])  // Ensure id is included
        '''
        print("HEATMAP - Fetching data from station_aqi")
        result = self.query_api.query(org='students', query=query)
        return self.format_results(result)

    def fetch_last_n_car_data(self, n):
        query = f'''
        from(bucket: "APARS")
        |> range(start: -1d)
        |> filter(fn: (r) => r["_measurement"] == "car_metrics")
        |> filter(fn: (r) => r["_field"] == "aqi" or r["_field"] == "latitude" or r["_field"] == "longitude")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> limit(n: {n})
        '''
        print("HEATMAP - Fetching data from car_metrics")
        result = self.query_api.query(query=query)
        return self.format_results(result)

    def format_results(self, tables):
        data = []
        for table in tables:
            for record in table.records:
                try:
                    data.append({
                        "lat": float(record.values.get("latitude")),
                        "lon": float(record.values.get("longitude")),
                        "aqi": int(record.values.get("aqi")),
                    })
                except Exception as e:
                    self.logger.warning("Could not process point")

        return data


if __name__ == '__main__':
    fetcher = InfluxDataFetcher()
    latest_patras_station_data = fetcher.fetch_latest_patras_station_data()
    print(latest_patras_station_data, "\n\n")
    latest_station_data = fetcher.fetch_latest_station_data()
    print(latest_station_data, "\n\n")
    last_n_car_data = fetcher.fetch_last_n_car_data(50)
    print(last_n_car_data, "\n\n")

    all_data = latest_station_data + last_n_car_data
    print(all_data)
