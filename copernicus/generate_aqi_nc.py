import netCDF4 as nc
import numpy as np

def parameter_to_aqi(value_array, parameter_name):
    """
    Converts an array of parameter values to AQI using U.S. EPA AQI breakpoints.

    Args:
        value_array (numpy.ndarray): Array of parameter values to convert.
        parameter_name (str): The name of the parameter.
    
    Returns:
        numpy.ndarray: Array of corresponding AQI values.
    """
    # AQI breakpoints for various parameters
    aqi_breakpoints = {
        'pm2p5_conc': [
            (0, 12, 0, 50),
            (12.1, 35.4, 51, 100),
            (35.5, 55.4, 101, 150),
            (55.5, 150.4, 151, 200),
            (150.5, 250.4, 201, 300),
            (250.5, 350.4, 301, 400),
            (350.5, 500.4, 401, 500),
        ],
        'pm10_conc': [
            (0, 54, 0, 50),
            (55, 154, 51, 100),
            (155, 254, 101, 150),
            (255, 354, 151, 200),
            (355, 424, 201, 300),
            (425, 504, 301, 400),
            (505, 604, 401, 500),
        ],
        'so2_conc': [
            (0, 35, 0, 50),
            (36, 75, 51, 100),
            (76, 185, 101, 150),
            (186, 304, 151, 200),
            (305, 604, 201, 300),
            (605, 804, 301, 400),
            (805, 1004, 401, 500),
        ],
        'no_conc': [
            (0, 53, 0, 50),
            (54, 100, 51, 100),
            (101, 360, 101, 150),
            (361, 649, 151, 200),
            (650, 1249, 201, 300),
            (1250, 1649, 301, 400),
            (1650, 2049, 401, 500),
        ],
        'dust': [
            (0, 50, 0, 50),
            (51, 150, 51, 100),
            (151, 250, 101, 150),
            (251, 350, 151, 200),
            (351, 450, 201, 300),
            (451, 550, 301, 400),
            (551, 650, 401, 500),
        ],
    }

    breakpoints = aqi_breakpoints.get(parameter_name, None)
    if not breakpoints:
        return value_array  # Default: Return the values directly if no AQI conversion is defined

    # Initialize AQI array with a default max value for out-of-range inputs
    aqi_array = np.full_like(value_array, 500, dtype=np.float32)

    # Apply AQI conversion for each range
    for low, high, aqi_low, aqi_high in breakpoints:
        mask = (value_array >= low) & (value_array <= high)
        aqi_array[mask] = ((value_array[mask] - low) / (high - low)) * (aqi_high - aqi_low) + aqi_low

    return aqi_array



def split_nc_by_parameter_with_aqi(input_file, output_dir):
    """
    Creates separate .nc files for each parameter in the input satellite.nc file,
    converting parameter values to AQI values.

    Args:
        input_file (str): Path to the input satellite.nc file.
        output_dir (str): Directory to save the output .nc files.
    """
    with nc.Dataset(input_file, 'r') as src_ds:
        for var_name in src_ds.variables:
            if var_name in ['longitude', 'latitude', 'time', 'level']:
                continue  # Skip non-AQI variables
            
            var = src_ds.variables[var_name]
            if 'value' in var.ncattrs() and var.value == 'hourly values':
                output_file = f"{output_dir}/{var_name}_aqi.nc"
                with nc.Dataset(output_file, 'w', format='NETCDF4') as dst_ds:
                    # Copy dimensions
                    for dim_name, dim in src_ds.dimensions.items():
                        dst_ds.createDimension(dim_name, len(dim) if not dim.isunlimited() else None)
                    
                    # Copy coordinate variables
                    for dim_name in ['latitude', 'longitude', 'time', 'level']:
                        src_var = src_ds.variables[dim_name]
                        dst_var = dst_ds.createVariable(dim_name, src_var.datatype, src_var.dimensions)
                        dst_var.setncatts({k: getattr(src_var, k) for k in src_var.ncattrs()})
                        dst_var[:] = src_var[:]
                    
                    # Add AQI variable
                    dst_var = dst_ds.createVariable('aqi', 'f4', var.dimensions)
                    dst_var.units = 'AQI'
                    dst_var.long_name = f"AQI values derived from {var_name}"
                    
                    # Convert parameter values to AQI
                    param_values = var[:]
                    aqi_values = np.where(param_values != var._FillValue,
                                          parameter_to_aqi(param_values, var_name),
                                          var._FillValue)
                    dst_var[:] = aqi_values
                    
                print(f"File {output_file} created successfully.")


if __name__=="__main__":
    # Path to the input satellite.nc file
    input_file = 'LOTOS_ANALYSIS.nc'

    # Directory to save the generated {parameter}_aqi.nc files
    output_dir = 'output_nc_files'

    # Create separate .nc files with AQI values
    split_nc_by_parameter_with_aqi(input_file, output_dir)
