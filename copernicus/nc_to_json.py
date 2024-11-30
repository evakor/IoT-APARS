import json
from netCDF4 import Dataset

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

# Example usage
netcdf_to_json_filtered(
    "output_nc_files/dust_aqi.nc", 
    "filtered_output.json", 
    west=19.3646, east=29.6425, 
    south=34.8021, north=41.7489
)
# lat_min, lat_max = 34.8021, 41.7489
# lon_min, lon_max = 19.3646, 29.6425