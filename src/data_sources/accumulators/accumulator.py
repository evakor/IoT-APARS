import threading
import time
from car import CarDataAccumulator
from station import StationDataAccumulator, PatrasStationAccumulator

def accumulate_station_data():
    station = StationDataAccumulator.StationDataCollector()
    station_patras = PatrasStationAccumulator.PatrasSensorDataCollector()

    while True:
        station.accumulate()
        station_patras.accumulate()
        time.sleep(120) # Every two minutes

def listen_car_data():
    car = CarDataAccumulator.CarMQTTListener()
    car.listen()

if __name__ == "__main__":
    station_thread = threading.Thread(target=accumulate_station_data)
    car_thread = threading.Thread(target=listen_car_data)

    station_thread.start()
    car_thread.start()

    station_thread.join()
    car_thread.join()
