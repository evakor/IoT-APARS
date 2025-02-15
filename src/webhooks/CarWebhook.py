from .WebhookBase import WebhookBase
from influxdb_client import Point

class CarWebhook(WebhookBase):
    def __init__(self):
        super().__init__(topic="apars/car", measurement="car_metrics", logger_name="CAR-WEBHOOK")


    def send_to_influxdb(self, data):
        try:
            payload = data["data"][0]
            max_aqi = 0
            for param in ['pm1', 'pm25', 'pm10', 'benzene', 'co', 'nh3', 'co2']: # ['pm1', 'pm25', 'pm10', 'lpg', 'benzene', 'co', 'oxidised', 'reduced', 'nh3', 'co2']
                payload[param]['value'] = self.converter.getAQI(param, payload[param]['value'])
                if payload[param]['value'] is None:
                    payload[param]['value'] = 10
                if payload[param]['value'] >= max_aqi:
                    max_aqi = payload[param]['value']

            point = Point(self.measurement) \
                .tag("id", str(payload['id'])) \
                .field("temperature", float(payload['temperature']['value'])) \
                .field("humidity", float(payload['humidity']['value'])) \
                .field("pressure", float(payload['pressure']['value'])) \
                .field("pm1", float(payload['pm1']['value'])) \
                .field("pm25", float(payload['pm25']['value'])) \
                .field("pm10", float(payload['pm10']['value'])) \
                .field("lpg", float(payload['lpg']['value'])) \
                .field("benzene", float(payload['benzene']['value'])) \
                .field("co", float(payload['co']['value'])) \
                .field("oxidised", float(payload['oxidised']['value'])) \
                .field("reduced", float(payload['reduced']['value'])) \
                .field("nh3", float(payload['nh3']['value'])) \
                .field("co2", float(payload['co2']['value'])) \
                .field("eco2", float(payload['eco2']['value'])) \
                .field("tvoc", float(payload['tvoc']['value'])) \
                .field("aqi", int(max_aqi)) \
                .time(self.toUTC(payload['dateObserved']['value'])) \
                .field("latitude", float(payload['location']['value']['coordinates'][0])) \
                .field("longitude", float(payload['location']['value']['coordinates'][1]))

            self.write_api.write(bucket='APARS', org='students', record=point)
            print(f"CAR-WEBBHOOK - Data for ID '{payload['id']}' successfully written to InfluxDB under measurement '{self.measurement}'.")
        except Exception as e:
            self.logger.error(f"Failed to write data to InfluxDB: {str(e)}")
