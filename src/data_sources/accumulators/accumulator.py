from car import CarDataAccumulator
from station import StationDataAccumulator, PatrasStationAccumulator

if __name__ == "__main__":
    station = StationDataAccumulator.StationDataCollector()
    station_patras = PatrasStationAccumulator.StationPatrasCollector()
    car = CarDataAccumulator.CarMQTTListener()

    station.accumulate()
    station_patras.accumulate()
    car.listen()
