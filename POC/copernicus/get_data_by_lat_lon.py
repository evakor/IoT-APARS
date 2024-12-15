import netCDF4 as nc
import numpy as np

def print_nc_structure(file_path):
    """
    Prints the structure of a .nc file, including dimensions, variables, and global attributes.

    Parameters:
        file_path (str): Path to the .nc file.
    """
    try:
        # Open the NetCDF file
        dataset = nc.Dataset(file_path, 'r')
        
        print("\n--- Global Attributes ---")
        for attr_name in dataset.ncattrs():
            print(f"{attr_name}: {dataset.getncattr(attr_name)}")
        
        print("\n--- Dimensions ---")
        for dim_name, dimension in dataset.dimensions.items():
            print(f"{dim_name}: {len(dimension)} (Unlimited: {dimension.isunlimited()})")
        
        print("\n--- Variables ---")
        for var_name, variable in dataset.variables.items():
            print(f"{var_name}:")
            print(f"    Dimensions: {variable.dimensions}")
            print(f"    Shape: {variable.shape}")
            print(f"    Data Type: {variable.dtype}")
            
            # Print variable attributes
            print("    Attributes:")
            for attr_name in variable.ncattrs():
                print(f"        {attr_name}: {variable.getncattr(attr_name)}")
        
        # Close the dataset
        dataset.close()

    except Exception as e:
        print(f"Error: {e}")

def get_variable_value(file_path, lat, lon, variable, time_index=0, level_index=0):
    """
    Load a .nc file and retrieve the value of a specific variable at given coordinates.

    Parameters:
        file_path (str): Path to the .nc file.
        lat (float): Latitude of the desired location.
        lon (float): Longitude of the desired location.
        variable (str): Variable to extract.
        time_index (int): Time index to extract (default is 0).
        level_index (int): Level index to extract (default is 0).

    Returns:
        float: Value of the variable at the given coordinates.
    """
    try:
        # Open the NetCDF file
        dataset = nc.Dataset(file_path, 'r')
        
        # Check if the variable exists in the dataset
        if variable not in dataset.variables:
            raise ValueError(f"Variable '{variable}' not found in the dataset.")
        
        # Extract latitude and longitude arrays
        latitudes = dataset.variables['latitude'][:]
        longitudes = dataset.variables['longitude'][:]

        # Find the closest indices for the given latitude and longitude
        lat_idx = np.abs(latitudes - lat).argmin()
        lon_idx = np.abs(longitudes - lon).argmin()

        # Extract the variable data
        var_data = dataset.variables[variable][:]

        # Handle 4D variables with time, level, latitude, and longitude
        if var_data.ndim == 4:  # Assuming dimensions are [time, level, lat, lon]
            value = var_data[time_index, level_index, lat_idx, lon_idx]
        else:
            raise ValueError(f"Unsupported variable dimensions: {var_data.ndim}")

        # Handle fill values (e.g., -999.0)
        fill_value = dataset.variables[variable].getncattr("_FillValue")
        if value == fill_value:
            value = None  # Return None for invalid data points

        # Close the dataset
        dataset.close()

        return value

    except Exception as e:
        return f"Error: {e}"

# Example usage
if __name__ == "__main__":
    # File path to your .nc file
    nc_file_path = "LOTOS_ANALYSIS.nc"
    
    # Coordinates and variable of interest
    latitude = 35.0  # Example latitude
    longitude = 25.0  # Example longitude
    variable_name = "dust"  # Replace with the desired variable
    time_idx = 0  # Time index (e.g., first timestep)
    level_idx = 0  # Level index (e.g., surface level)

    result = get_variable_value(nc_file_path, latitude, longitude, variable_name, time_idx, level_idx)
    if result is not None:
        print(f"The value of '{variable_name}' at ({latitude}, {longitude}) is: {result} µg/m³")
    else:
        print(f"No valid data found for '{variable_name}' at ({latitude}, {longitude}).")