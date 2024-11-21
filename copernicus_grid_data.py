# import cdsapi

# dataset = "cams-europe-air-quality-forecasts"
# request = {
#     "variable": ["dust"],
#     "model": ["ensemble"],
#     "level": ["0"],
#     "date": ["2024-11-21/2024-11-21"],
#     "type": ["forecast"],
#     "time": ["00:00"],
#     "leadtime_hour": ["0"],
#     "data_format": "grib",
#     "area": [90, -180, -90, 180]
# }

# client = cdsapi.Client()
# client.retrieve(dataset, request).download()

import json

import cdsapi

with open("request.json") as req:
    request = json.load(req)

cds = cdsapi.Client(request.get("url"), request.get("uuid") + ":" + request.get("key"))

cds.retrieve(
    request.get("variable"),
    request.get("options"),
    "/output/" + request.get("filename"),
)