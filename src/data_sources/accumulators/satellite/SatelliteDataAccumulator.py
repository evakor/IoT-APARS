import glob
import cdsapi
import numpy as np
import netCDF4 as nc
from netCDF4 import Dataset
import zipfile
import os
import json
import requests
import logging
import logging.config
from datetime import datetime

logging.config.fileConfig('../logging.conf')
logger = logging.getLogger('SATELLITE_ACCUMULATOR')


ORION_URL = "http://localhost:1026/v2/entities"

dataset = "cams-europe-air-quality-forecasts"

request = {
    "variable": [ # TODO: Determine what values we will use
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
    "level": ["0"], # For this demo only for ground level
    "date": ["2024-11-28/2024-11-29"], # TODO: Set todays data
    "type": ["analysis"],
    "time": ["00:00", "02:00"], # TODO: Fetch every hour
    "leadtime_hour": ["0"],
    "data_format": "netcdf_zip"
}

filename = "copernicus_2024_11_28_2024_11_29_0_2.zip"


def split_nc_by_parameter(input_file, output_dir):
    """
    Creates separate .nc files for each parameter in the input satellite.nc file
    without any AQI conversion.

    Args:
        input_file (str): Path to the input satellite.nc file.
        output_dir (str): Directory to save the output .nc files.
    """
    with nc.Dataset(input_file, 'r') as src_ds:
        for var_name in src_ds.variables:
            if var_name in ['longitude', 'latitude', 'time', 'level']:
                continue  # Skip coordinate variables
            
            var = src_ds.variables[var_name]
            output_file = f"{output_dir}/{var_name}.nc"
            with nc.Dataset(output_file, 'w', format='NETCDF4') as dst_ds:
                # Copy dimensions
                for dim_name, dim in src_ds.dimensions.items():
                    dst_ds.createDimension(dim_name, len(dim) if not dim.isunlimited() else None)
                
                # Copy coordinate variables
                for dim_name in ['latitude', 'longitude', 'time', 'level']:
                    if dim_name in src_ds.variables:
                        src_var = src_ds.variables[dim_name]
                        dst_var = dst_ds.createVariable(dim_name, src_var.datatype, src_var.dimensions)
                        dst_var.setncatts({k: getattr(src_var, k) for k in src_var.ncattrs()})
                        dst_var[:] = src_var[:]
                
                # Copy the variable
                dst_var = dst_ds.createVariable(var_name, var.datatype, var.dimensions)
                dst_var.setncatts({k: getattr(var, k) for k in var.ncattrs()})
                dst_var[:] = var[:]
            
            print(f"File {output_file} created successfully.")


def unzip_file(zip_file_path, output_dir):
    """
    Unzips a .zip file to the specified output directory.

    Args:
        zip_file_path (str): Path to the .zip file.
        output_dir (str): Directory to extract the files into.
    """
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # Ensure the output directory exists
            os.makedirs(output_dir, exist_ok=True)
            # Extract all files
            zip_ref.extractall(output_dir)
        print(f"Successfully unzipped {zip_file_path} to {output_dir}")
    except zipfile.BadZipFile:
        print(f"Error: {zip_file_path} is not a valid zip file.")
    except Exception as e:
        print(f"An error occurred: {e}")


def netcdf_to_json_filtered(nc_file, json_file, west, east, south, north):
    """
    Converts a netCDF4 file to JSON, filtering data based on geographical bounds.
    
    Parameters:
        nc_file (str): Path to the netCDF4 file.
        json_file (str): Path to the output JSON file.
        west (float): Western longitude limit.
        east (float): Eastern longitude limit.
        south (float): Southern latitude limit.
        north (float): Northern latitude limit.
    """
    # Open the netCDF4 file
    with Dataset(nc_file, mode="r") as nc:
        data = {}
        
        # Global attributes
        data["global_attributes"] = {attr: getattr(nc, attr) for attr in nc.ncattrs()}
        
        # Dimensions
        data["dimensions"] = {dim: len(nc.dimensions[dim]) for dim in nc.dimensions}
        
        # Find the indices for the bounding box
        lat = nc.variables["latitude"][:]
        lon = nc.variables["longitude"][:]
        
        lat_indices = (lat >= south) & (lat <= north)
        lon_indices = (lon >= west) & (lon <= east)
        
        # Variables
        data["variables"] = {}
        for var_name, variable in nc.variables.items():
            var_data = {
                "dimensions": variable.dimensions,
                "attributes": {attr: getattr(variable, attr) for attr in variable.ncattrs()}
            }
            
            # Extract and filter data based on lat/lon bounds
            if "latitude" in variable.dimensions and "longitude" in variable.dimensions:
                lat_dim = variable.dimensions.index("latitude")
                lon_dim = variable.dimensions.index("longitude")
                
                # Create slices for the variable's data
                slices = [slice(None)] * len(variable.dimensions)  # Default: take all data
                slices[lat_dim] = lat_indices
                slices[lon_dim] = lon_indices
                
                # Filter and convert to list
                var_data["data"] = variable[tuple(slices)].tolist()
            else:
                # Non-spatial data or variables
                var_data["data"] = variable[:].tolist()
            
            data["variables"][var_name] = var_data
        
        # Write filtered data to JSON
        with open(json_file, "w") as json_out:
            json.dump(data, json_out, indent=4)
    
    print(f"Filtered data from {nc_file} based on geographical bounds and saved to {json_file}")


def json_to_orion_entities(json_data, region="Greece"):
    """
    Converts JSON payload into Orion Context Broker-compatible entities.

    Args:
        json_data (dict): The JSON data to be converted.
        region (str): The region to be used in the entity IDs (default is "Greece").

    Returns:
        list: A list of entities ready to be posted to Orion Context Broker.
    """
    entities = []
    for param, param_data in json_data.get("variables", {}).items():
        # Skip coordinates and dimensions
        if param in ['longitude', 'latitude', 'time', 'level']:
            continue
        
        entity = {
            "id": f"satellite_{region}_{param}",
            "type": "satellite",
            "region": {"type": "Text", "value": region},
            "parameter": {"type": "Text", "value": param},
            "attributes": {"type": "StructuredValue", "value": param_data.get("attributes", {})},
            "dimensions": {"type": "StructuredValue", "value": param_data.get("dimensions", [])},
            "data": {"type": "StructuredValue", "value": param_data.get("data", [])}
        }
        entities.append(entity)
    
    return entities

def send_data_to_orion(payload):
    """Send data to Orion Context Broker."""
    headers = {
        "Content-Type": "application/json"
    }
    try:
        data = json.loads(payload)
        entity_id = data["id"]

        url = f"{ORION_URL}/{entity_id}/attrs"

        response = requests.patch(url, headers=headers, json={key: value for key, value in data.items() if key not in ["id", "type"]})

        if response.status_code == 204:
            logger.info(f"Data updated successfully! CAR ID: {entity_id}")
        elif response.status_code == 404:  # Entity not found, create it
            response = requests.post(ORION_URL, headers=headers, json=data)
            if response.status_code == 201:
                logger.info(f"Data created successfully! CAR ID: {entity_id}")
            else:
                logger.error(f"Failed to create entity: {response.status_code} - {response.text}")
        else:
            logger.error(f"Failed to send data: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error while sending data to Orion: {str(e)}")


if __name__=="__main__":
    ## Step1: Get data and unzip them

    client = cdsapi.Client()
    client.retrieve(dataset, request, filename).download()



    ## Step 2: Unzip and split file

    unzip_file(filename, "satellite_accumulated")

    split_nc_by_parameter(f"satellite_accumulated/{filename}", "satellite_by_parameter")



    ## Step 3: nc->json

    nc_files = glob.glob("satellite_by_parameter/*.nc")

    for file in nc_files:
        netcdf_to_json_filtered(
            file, 
            f"satellite_by_parameter/{file.split(".")[0]}.json", 
            west=19.3646,
            east=29.6425, 
            south=34.8021,
            north=41.7489
    )
        
    

    ## Step 3: post to orion
    
    json_files = glob.glob("satellite_by_parameter/*.json")

    for file in json_files:
        with open(file, 'r') as f:
            json_payload = json.load(f)
        
        entities = json_to_orion_entities(json_payload, region="Greece")

        for entity in entities:
            send_data_to_orion(entity)