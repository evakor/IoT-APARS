import cdsapi

# dataset = "cams-europe-air-quality-forecasts"
# request = {
#     "variable": ["pm10_wildfires"],
#     "model": [
#         "ensemble",
#         "lotos"
#     ],
#     "level": ["0"],
#     "date": ["2024-11-24/2024-11-25"],
#     "type": ["analysis"],
#     "time": ["00:00", "02:00"],
#     "leadtime_hour": ["0"],
#     "data_format": "netcdf_zip"
# }

dataset = "cams-europe-air-quality-forecasts"
request = {
    "variable": [
        "dust",
        "nitrogen_monoxide",
        "non_methane_vocs",
        "particulate_matter_2.5um",
        "particulate_matter_10um",
        "pm2.5_total_organic_matter",
        "pm10_sea_salt_dry",
        "pm10_wildfires",
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
    "date": ["2024-11-23/2024-11-24"],
    "type": ["analysis"],
    "time": ["00:00", "02:00"],
    "leadtime_hour": ["0"],
    "data_format": "netcdf_zip",
    # "area": [90, -180, -90, 180]
}

client = cdsapi.Client()
client.retrieve(dataset, request).download()


