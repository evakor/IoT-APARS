from scipy.interpolate import griddata
import netCDF4 as nc
import numpy as np

def interpolate_nc_files(input_files, output_file):
    """
    Interpolates all .nc files and generates a new interpolated.nc file.
    
    Args:
        input_files (list of str): List of paths to the input .nc files.
        output_file (str): Path to the output interpolated .nc file.
    """
    all_lats, all_lons, all_aqis = [], [], []

    # Read data from all input files
    for input_file in input_files:
        with nc.Dataset(input_file, 'r') as ds:
            lats = ds.variables['latitude'][:]
            lons = ds.variables['longitude'][:]
            aqi = ds.variables[list(ds.variables.keys())[-1]][:]  # Assume last variable is AQI
            lats, lons = np.meshgrid(lats, lons)
            all_lats.append(lats.flatten())
            all_lons.append(lons.flatten())
            all_aqis.append(aqi.flatten())

    # Flatten and combine
    all_lats = np.concatenate(all_lats)
    all_lons = np.concatenate(all_lons)
    all_aqis = np.concatenate(all_aqis)

    # Define grid for interpolation
    grid_lat = np.linspace(np.min(all_lats), np.max(all_lats), 500)
    grid_lon = np.linspace(np.min(all_lons), np.max(all_lons), 500)
    grid_lat, grid_lon = np.meshgrid(grid_lat, grid_lon)

    # Perform interpolation
    grid_aqi = griddata((all_lats, all_lons), all_aqis, (grid_lat, grid_lon), method='linear')

    # Create NetCDF file for interpolated data
    with nc.Dataset(output_file, 'w', format='NETCDF4') as ds:
        # Define dimensions
        ds.createDimension('latitude', grid_lat.shape[0])
        ds.createDimension('longitude', grid_lat.shape[1])
        
        # Define variables
        lat_var = ds.createVariable('latitude', 'f4', ('latitude',))
        lon_var = ds.createVariable('longitude', 'f4', ('longitude',))
        aqi_var = ds.createVariable('aqi', 'f4', ('latitude', 'longitude'))
        
        # Assign data to variables
        lat_var[:] = grid_lat[:, 0]
        lon_var[:] = grid_lon[0, :]
        aqi_var[:, :] = grid_aqi
        
        # Add metadata
        ds.title = "Interpolated AQI data"
        lat_var.units = 'degrees_north'
        lon_var.units = 'degrees_east'
        aqi_var.units = 'µg/m3'

    print(f"File {output_file} created successfully.")


if __name__ == "__main__":
    input_files = ['station_api.nc', 'copernicus/output_nc_files/dust_aqi.nc', 'output_dir/pm10_aqi.nc']
    interpolate_nc_files(input_files, 'interpolated.nc')