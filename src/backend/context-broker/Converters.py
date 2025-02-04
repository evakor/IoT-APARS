import numpy as np
from ProgressBar import ProgressBar
import netCDF4 as nc
from MathFunctions import Calculations, Validations
from datetime import datetime

class Converters:
    def __init__(self):
        pass

    def getAQI(self, parameter: str, value: any) -> int:
        """
        Calculate the AQI for a given parameter and its value based on the breakpoints.

        Args:
            parameter (str): The name of the parameter (e.g., 'PM2.5', 'CO2').
            value (float): The measured value of the parameter.

        Returns:
            int: The calculated AQI value.

        Sources:
        This code provides a detailed categorization of air quality for various pollutants, including PM1, PM2.5, PM10, NH3 (ammonia), oxidized gases, reduced gases, CO2 (carbon dioxide), and dust. The AQI parameters are defined with specific breakpoints, reflecting pollutant concentration ranges and their associated health effects.

        The AQI parameters and breakpoints are derived from the following authoritative sources:

        1. Prana Air Blog: This source explains the concept of AQI, its calculation, and general pollutant categories.
        [What is Air Quality Index (AQI) and its Calculation](https://www.pranaair.com/in/blog/what-is-air-quality-index-aqi-and-its-calculation/)  

        

        2. U.S. Environmental Protection Agency (EPA): The EPA document outlines AQI breakpoints and their health implications for particulate matter (PM).
        [PM National Ambient Air Quality Standards (NAAQS) Air Quality Index Fact Sheet](https://www.epa.gov/system/files/documents/2024-02/pm-naaqs-air-quality-index-fact-sheet.pdf)  

        
        3. Central Pollution Control Board (CPCB), India: The CPCB source provides AQI standards specific to India, which are comparable to global AQI systems.
        [About AQI](http://app.cpcbccr.com/ccr_docs/About_AQI.pdf)  

        

        4. ResearchGate Publication: This paper offers insights into the integration of various air quality indices and their computational models.
        [Information Fusion for Computational Assessment of Air Quality and Health Effects](https://www.researchgate.net/publication/231814203_Information_Fusion_for_Computational_Assessment_of_Air_Quality_and_Health_Effects/link/5a3cdb95aca272dd65e5ec6e/download?_tp=eyJjb250ZXh0Ijp7ImZpcnN0UGFnZSI6Il9kaXJlY3QiLCJwYWdlIjoicHVibGljYXRpb24ifX0=)  

        
        The parameters and their corresponding AQI breakpoints were consolidated based on these sources. In cases where specific breakpoints were not defined (e.g., for dust or reduced gases), similar parameters like PM2.5 or oxidized gases were used to approximate the breakpoints.
        The compiled data can be used for environmental monitoring, public awareness, and policymaking. It is especially useful for projects requiring a detailed understanding of pollutant behavior and their health impacts, such as the development of live AQI monitoring systems.
        """

        aqi_ranges = [
            (0, 50),
            (51, 100),
            (101, 150),
            (151, 200),
            (201, 300),
            (301, 500),
        ]

        breakpoints = {
            "oxidised": [(0.05, 1), (1.1, 2.5), (2.6, 4), (4.1, 6), (6.1, 8), (8.1, 10)],
            "pm1": [(0, 9), (9.1, 35.4), (35.5, 55.4), (55.5, 125.4), (125.5, 225.4), (225.5, 500)],
            "pm25": [(0, 12), (12.1, 35.4), (35.5, 55.4), (55.5, 150.4), (150.5, 250.4), (250.5, 500)],
            "pm10": [(0, 54), (55, 154), (155, 254), (255, 354), (355, 424), (425, 604)],
            "reduced": [(1, 50), (51, 150), (151, 300), (301, 500), (501, 750), (751, 1000)],
            "nh3": [(1, 25), (26, 75), (76, 150), (151, 200), (201, 250), (251, 300)],
            "lpg": [(200, 500), (501, 1500), (1501, 3000), (3001, 5000), (5001, 7500), (7501, 10000)],
            "benzene": [(10, 50), (51, 150), (151, 300), (301, 500), (501, 750), (751, 1000)],
            "co": [(20, 50), (51, 200), (201, 400), (401, 800), (801, 1500), (1501, 2000)],
            "co2": [(400, 600), (601, 1000), (1001, 2000), (2001, 4000), (4001, 7000), (7001, 10000)],
            "eco2": [(400, 2000), (2001, 5000), (5001, 10000), (10001, 25000), (25001, 40000), (40001, 60000)],
            "tvoc": [(0, 500), (501, 3000), (3001, 10000), (10001, 20000), (20001, 40000), (40001, 60000)],
        }

        if parameter not in breakpoints:
            raise ValueError(f"Unknown parameter: {parameter}")

        for (low_bp, high_bp), (low_aqi, high_aqi) in zip(breakpoints[parameter], aqi_ranges):
            if low_bp <= value <= high_bp:
                aqi = ((high_aqi - low_aqi) / (high_bp - low_bp)) * (value - low_bp) + low_aqi
                return int(round(aqi))

        return None


    def points_to_grid(self, points: list, west: float, east: float, south: float, north: float, resolution: float=0.001, influence_radius_km: float=0.01, base_value: int=10):
        '''
        For the points parameter you need to map each point to the following SmartDataModel:

        {  
            "id": "id",  
            "type": "AirQualityObserved",  
            "dateObserved": {  
                "type": "DateTime",  
                "value": "2016-03-15T11:00:00"  
            },   
            "aqi": {  
                "type": "Integer",  
                "value": 0
            }, 
            "location": {  
                "type": "geo:json",  
                "value": {  
                    "type": "Point",  
                    "coordinates": [  
                        0.000000,
                        0.000000  
                    ]  
                }  
            }
        }  

        '''

        pb = ProgressBar()

        lats = np.arange(south, north, resolution)
        lons = np.arange(west, east, resolution*2)

        lon_grid, lat_grid = np.meshgrid(lons, lats)

        grid = np.full(lon_grid.shape, base_value, dtype=float)

        clip_points = [
            {"lat": point["location"]["value"]["coordinates"][0], "lon": point["location"]["value"]["coordinates"][1], "value": int(point["aqi"]["value"] if Validations.isInt(point["aqi"]["value"]) == False else 40)}
            for point in points
            if south <= point["location"]["value"]["coordinates"][0] <= north and west <= point["location"]["value"]["coordinates"][1] <= east
        ]

        for point in clip_points:
            point_lat = point["lat"]
            point_lon = point["lon"]
            point_value = point["value"]
            print(f"{clip_points.index(point)+1}/{len(clip_points)} stations  ")
            for i in range(len(lats)):
                pb.print(i+1, len(lats), prefix = 'Progress:', suffix = 'Complete', length = 50)
                for j in range(len(lons)):
                    distance = np.sqrt((lats[i] - point_lat)**2 + (lons[j] - point_lon)**2)
                    decay = Calculations.radial_decay(distance, influence_radius_km)
                    grid[i, j] += decay * (point_value - base_value)
        
        return lats, lons, grid


    def grid_to_nc(self, file_name: str, lats: np.arange, lons: np.arange, grid: np.full) -> None:
        with nc.Dataset(file_name, "w", format="NETCDF4") as dataset:
            # Create dimensions
            lat_dim = dataset.createDimension("lat", len(lats))
            lon_dim = dataset.createDimension("lon", len(lons))

            # Create variables
            latitudes = dataset.createVariable("lat", "f4", ("lat",))
            longitudes = dataset.createVariable("lon", "f4", ("lon",))
            aqi_values = dataset.createVariable("aqi", "f4", ("lat", "lon"))

            # Assign data to variables
            latitudes[:] = lats
            longitudes[:] = lons
            aqi_values[:, :] = grid

            # Add attributes
            dataset.description = "AQI Heatmap"
            latitudes.units = "degrees_north"
            longitudes.units = "degrees_east"
            aqi_values.units = "AQI"
    
    def grid_to_sdm(self, name: str, lats: np.arange, lons: np.arange, grid: np.full) -> list:
        smart_data_models = []
        current_time = datetime.now().isoformat()

        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                smart_data_models.append({
                    "id": f"{name}_point_{i}_{j}",
                    "type": "GridAirQualityObserved",
                    "dateObserved": {
                        "type": "DateTime",
                        "value": current_time
                    },
                    "aqi": {
                        "type": "Float",
                        "value": grid[i, j]
                    },
                    "location": {
                        "type": "geo:json",
                        "value": {
                            "type": "Point",
                            "coordinates": [lat, lon]
                        }
                    }
                })

        return smart_data_models