import os
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv

load_dotenv()

class InfluxDataFetcher:
    def __init__(self):
        self.client = InfluxDBClient(url=os.getenv("INFLUX_URL"), token=os.getenv('GRAFANA_READ_AND_WRITE'), org='students')
        self.query_api = self.client.query_api()
        self.bucket = 'APARS'

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
        result = self.query_api.query(org='students', query=query)
        return self.format_results(result)

    def fetch_last_n_car_data(self, n):
        query = f'''
        from(bucket: "APARS")
        |> range(start: 0)
        |> filter(fn: (r) => r["_measurement"] == "car_metrics")
        |> filter(fn: (r) => r["_field"] == "aqi" or r["_field"] == "latitude" or r["_field"] == "longitude")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> limit(n: {n})
        '''
        result = self.query_api.query(query=query)
        print(result)
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
                    print("Could not process point")

        return data


if __name__ == '__main__':
    fetcher = InfluxDataFetcher()
    latest_patras_station_data = fetcher.fetch_latest_patras_station_data()
    print(latest_patras_station_data, "\n\n")
    latest_station_data = fetcher.fetch_latest_station_data()
    print(latest_station_data, "\n\n")
    last_n_car_data = fetcher.fetch_last_n_car_data(20)  # Replace 5 with the desired number of points per car
    print(last_n_car_data, "\n\n")

    all_data = latest_station_data + last_n_car_data
    print(all_data)
