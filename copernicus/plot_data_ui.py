from shiny import App, ui, render, reactive, Inputs, Outputs
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import numpy as np
import cartopy.crs as ccrs

# Define the UI
app_ui = ui.page_fluid(
    ui.panel_title("NetCDF AQI Viewer"),
    ui.input_file("file_picker", "Choose a NetCDF (.nc) File", accept=[".nc"]),
    ui.output_plot("map_plot", width="100%", height="600px")
)

# Define the server logic
def server(input: Inputs, output: Outputs, session):
    @reactive.Calc
    def nc_data():
        file = input.file_picker()
        if file is None:
            return None
        # Load the NetCDF file
        nc_file_path = file[0]["datapath"]
        try:
            dataset = Dataset(nc_file_path, mode='r')
            return dataset
        except Exception as e:
            print(f"Error loading NetCDF file: {e}")
            return None

    def find_lat_lon(dataset):
        """Find latitude and longitude variables in the dataset."""
        lat_name, lon_name = None, None
        for var_name in dataset.variables:
            if 'lat' in var_name.lower():
                lat_name = var_name
            elif 'lon' in var_name.lower():
                lon_name = var_name
        return lat_name, lon_name

    @output
    @render.plot
    def map_plot():
        dataset = nc_data()
        if dataset is None:
            return

        # Find latitude, longitude, and data variable
        try:
            lat_name, lon_name = find_lat_lon(dataset)
            if not lat_name or not lon_name:
                raise ValueError("Latitude or longitude variables not found.")

            lat = dataset.variables[lat_name][:]
            lon = dataset.variables[lon_name][:]
            
            # Automatically detect the AQI variable (or choose the last variable in the dataset)
            data_var_name = None
            for var_name in dataset.variables:
                if var_name == "aqi":
                    data_var_name = var_name
                    break
            if not data_var_name:
                data_var_name = list(dataset.variables.keys())[-1]  # Fall back to the last variable

            data = dataset.variables[data_var_name][:]
            
            # Handle dimensions (e.g., time, level) by selecting the first index for simplicity
            if data.ndim == 4:  # Time, level, lat, lon
                data = data[0, 0, :, :]  # Select the first time and level
            elif data.ndim == 3:  # Time or level, lat, lon
                data = data[0, :, :]  # Select the first time or level
            elif data.ndim != 2:  # Anything other than lat, lon
                raise ValueError(f"Unsupported data dimensions: {data.shape}")

            # Create the plot
            fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})
            ax.coastlines()
            ax.set_global()

            lon, lat = np.meshgrid(lon, lat)
            img = ax.contourf(lon, lat, data, 60, transform=ccrs.PlateCarree(), cmap="viridis")
            plt.colorbar(img, ax=ax, orientation="horizontal", pad=0.05, label=data_var_name)

            return fig

        except Exception as e:
            print(f"Error plotting data: {e}")
            return

# Run the app
app = App(app_ui, server)