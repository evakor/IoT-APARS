import threading
import time
from accumulators.CarDataAccumulator import CarMQTTListener
from accumulators.PatrasStationAccumulator import PatrasSensorDataCollector
from accumulators.StationDataAccumulator import StationDataCollector
from webhooks.CarWebhook import CarWebhook
from webhooks.PatrasStationWebhook import PatrasStationWebhook
from webhooks.StationWebhook import StationWebhook
from heatmap.Heatmap import generate_and_publish
import os

def start_webhook(webhook_instance):
    webhook_instance.listen()

def accumulate_station_data():
    """Accumulate data from station sensors at regular intervals."""
    station = StationDataCollector()
    station_patras = PatrasSensorDataCollector()

    while True:
        station.accumulate()
        station_patras.accumulate()
        time.sleep(600)  # Every 10 minutes

def listen_car_data():
    """Listen to car data via MQTT."""
    car = CarMQTTListener()
    car.listen()

def heatmap_loop():
    """Generate and publish heatmaps every 3 minutes."""
    while True:
        generate_and_publish(
            lat_min=float(os.getenv('SOUTH')),
            lat_max=float(os.getenv('NORTH')),
            lon_min=float(os.getenv('WEST')),
            lon_max=float(os.getenv('EAST')),
            accuracy_m=5,
            radical_decay=60
        )
        time.sleep(180)  # Every 3 minutes

if __name__ == "__main__":
    # Start Webhooks
    car_webhook = CarWebhook()
    station_webhook = StationWebhook()
    patras_webhook = PatrasStationWebhook()

    car_webhook_thread = threading.Thread(target=start_webhook, args=(car_webhook,))
    station_webhook_thread = threading.Thread(target=start_webhook, args=(station_webhook,))
    patras_webhook_thread = threading.Thread(target=start_webhook, args=(patras_webhook,))

    # Start Station and Car Data Accumulation Threads
    station_accumulation_thread = threading.Thread(target=accumulate_station_data)
    car_data_listener_thread = threading.Thread(target=listen_car_data)

    # Start Heatmap Generation Thread
    heatmap_thread = threading.Thread(target=heatmap_loop)

    # Start all threads
    car_webhook_thread.start()
    station_webhook_thread.start()
    patras_webhook_thread.start()
    station_accumulation_thread.start()
    car_data_listener_thread.start()
    heatmap_thread.start()

    # Wait for all threads to complete
    car_webhook_thread.join()
    station_webhook_thread.join()
    patras_webhook_thread.join()
    station_accumulation_thread.join()
    car_data_listener_thread.join()
    heatmap_thread.join()
