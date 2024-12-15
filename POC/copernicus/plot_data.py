import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import panel as pn

# Enable Panel extensions
pn.extension()

# Step 1: Load the .nc file
file_path = 'LOTOS_ANALYSIS.nc'  # Replace with your .nc file path
data = xr.open_dataset(file_path)

# Step 2: Sort coordinates for consistent plotting
data = data.sortby('latitude').sortby('longitude')

# Step 3: Define a function to create the plot
def plot_variable(variable_name, time_index=0):
    # Extract the variable
    variable_data = data[variable_name]

    # Set up the plot
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.coastlines()
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    ax.add_feature(cfeature.LAND, edgecolor='black')
    ax.add_feature(cfeature.OCEAN)

    # Plot the data
    data_plot = variable_data.isel(time=time_index, level=0)  # Adjust for level and time
    im = data_plot.plot(
        ax=ax,
        transform=ccrs.PlateCarree(),
        cmap='viridis',
        cbar_kwargs={'label': variable_name}
    )

    # Add title
    plt.title(f'{variable_name} at Time Index {time_index}')
    plt.show()

# Step 4: Create Panel widgets for interaction
variable_selector = pn.widgets.Select(
    name='Variable',
    options=list(data.data_vars.keys())
)
time_selector = pn.widgets.IntSlider(
    name='Time Index',
    start=0,
    end=len(data['time']) - 1,
    value=0
)

# Step 5: Create a Panel interactive app
@pn.depends(variable_selector, time_selector)
def update_plot(variable_name, time_index):
    plot_variable(variable_name, time_index)

# Combine widgets and plot into a layout
interactive_app = pn.Column(
    pn.Row(variable_selector, time_selector),
    pn.panel(update_plot)
)

# Serve the app
interactive_app.servable()
interactive_app.show()
