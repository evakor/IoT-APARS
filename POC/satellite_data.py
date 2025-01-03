# Data will go directly to the main database. These data won't go via the contextx broker
# TODO: In production this service will get triggerd every 1 hour.

import cdsapi
from datetime import datetime

dataset = "cams-europe-air-quality-forecasts"

request = {
    "variable": [
        "alder_pollen",
        "ammonia",
        "birch_pollen",
        "carbon_monoxide",
        "dust",
        "formaldehyde",
        "glyoxal",
        "grass_pollen",
        "mugwort_pollen",
        "nitrogen_dioxide",
        "nitrogen_monoxide",
        "non_methane_vocs",
        "olive_pollen",
        "ozone",
        "particulate_matter_2.5um",
        "particulate_matter_10um",
        "peroxyacyl_nitrates",
        "pm2.5_total_organic_matter",
        "pm10_sea_salt_dry",
        "pm10_wildfires",
        "ragweed_pollen",
        "residential_elementary_carbon",
        "secondary_inorganic_aerosol",
        "sulphur_dioxide",
        "total_elementary_carbon"
    ],
    "model": [
        "ensemble",
        "lotos"
    ],
    "level": ["0"],
    "date": ["2024-11-27/2024-11-28"],
    "type": ["analysis"],
    "time": ["00:00"],
    "leadtime_hour": ["0"],
    "data_format": "netcdf_zip",
    "area": [37.9, 23.7, 37.8, 23.8]
}

client = cdsapi.Client()
client.retrieve(dataset, request, f"satellite_data_{datetime.now().isoformat()}.zip").download()


# request = {
#     "variable": [
#         "dust",
#         "nitrogen_monoxide",
#         "non_methane_vocs",
#         "particulate_matter_2.5um",
#         "particulate_matter_10um",
#         "pm2.5_total_organic_matter",
#         "pm10_sea_salt_dry",
#         "pm10_wildfires",
#         "residential_elementary_carbon",
#         "secondary_inorganic_aerosol",
#         "sulphur_dioxide",
#         "total_elementary_carbon"
#     ],
#     "model": [
#         "lotos"
#     ],
#     "level": ["0"],
#     "date": ["2024-11-23/2024-11-24"],
#     "type": ["analysis"],
#     "time": ["00:00", "02:00"],
#     "leadtime_hour": ["0"],
#     "data_format": "netcdf_zip",
#     # "area": [90, -180, -90, 180]
# }