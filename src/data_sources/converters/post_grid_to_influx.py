import netCDF4 as nc
import requests
import pandas as pd


def parse_nc_file(file_name):
    dataset = nc.Dataset(file_name, "r")
    lats = dataset.variables["lat"][:]
    lons = dataset.variables["lon"][:]
    aqi_data = dataset.variables["aqi"][:]
    return lats, lons, aqi_data


def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()


def write_to_influxdb(lats, lons, aqi_data):
    INFLUXDB_URL = "http://labserver.sense-campus.gr:8086/api/v2/write"
    ORG = "students"
    BUCKET = "OMADA 13- APARS"
    TOKEN = "Jr1yuGJCjKbFPip_9wnl9ZY98nUQ9AhR4WEu5ITQf155GyTDuH6WSfyBQn1PuTjY1kNmW_9d2dnJ3_AJEval3A=="
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "text/plain"
    }
    params = {
        "org": ORG,
        "bucket": BUCKET,
        "precision": "s"
    }


    timestamp = int(pd.Timestamp.now().timestamp())

    # Prepare the line protocol data
    lines = []
    for i, lat in enumerate(lats):
        printProgressBar(i+1, len(lats), prefix = 'Progress:', suffix = 'Complete', length = 50)
        for j, lon in enumerate(lons):
            aqi_value = aqi_data[i][j]
            line = f"aqi,lat={lat},lon={lon} aqi_value={aqi_value} {timestamp}"
            lines.append(line)

    # Send the data to InfluxDB
    data = "\n".join(lines)
    response = requests.post(INFLUXDB_URL, headers=headers, params=params, data=data, timeout=15)

    if response.status_code == 204:
        print("Data written successfully to InfluxDB!")
    else:
        print(f"Failed to write data to InfluxDB: {response.status_code}, {response.text}")


if __name__ == "__main__":
    file_name = "aqi_heatmap.nc"

    lats, lons, aqi_data = parse_nc_file(file_name)

    write_to_influxdb(lats, lons, aqi_data)
