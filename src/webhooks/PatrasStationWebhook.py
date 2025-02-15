from .WebhookBase import WebhookBase
from influxdb_client import Point

class PatrasStationWebhook(WebhookBase):
    def __init__(self):
        super().__init__(topic="apars/station/patras", measurement="patras_station_aqi", logger_name="STATION-PATRAS-WEBHOOK")


    def send_to_influxdb(self, data):
        try:
            payload = data["data"][0]
            point = Point(self.measurement) \
                .tag("id", str(payload['id'])) \
                .field("aqi", self.converter.getAQI('pm25', payload['pm25']['value'])) \
                .field("pm25", int(payload['pm25']['value'])) \
                .time(self.toUTC(payload['dateObserved']['value'])) \
                .field("latitude", float(payload['location']['value']['coordinates'][0])) \
                .field("longitude", float(payload['location']['value']['coordinates'][1]))

            self.write_api.write(bucket='APARS', org='students', record=point)
            print(f"PATRAS-STATION-WEBBHOOK - Data for ID '{payload['id']}' successfully written to InfluxDB under measurement '{self.measurement}'.")
        except Exception as e:
            self.logger.error(f"Failed to write data to InfluxDB: {str(e)}")