from .WebhookBase import WebhookBase
from influxdb_client import Point

class StationWebhook(WebhookBase):
    def __init__(self):
        super().__init__(topic="apars/station/waqi", measurement="station_aqi", logger_name="STATION-WEBHOOK")


    def send_to_influxdb(self, data):
        try:
            payload = data["data"][0]
            point = Point(self.measurement) \
                .tag("id", str(payload['id'])) \
                .field("aqi", int(payload['aqi']['value'])) \
                .time(self.toUTC(payload['dateObserved']['value'])) \
                .field("latitude", float(payload['location']['value']['coordinates'][0])) \
                .field("longitude", float(payload['location']['value']['coordinates'][1]))

            self.write_api.write(bucket='APARS', org='students', record=point)
            print(f"STATION-WEBBHOOK - Data for ID '{payload['id']}' successfully written to InfluxDB under measurement '{self.measurement}'.")
        except Exception as e:
            self.logger.error(f"Failed to write data to InfluxDB: {str(e)}")