import serial
import time
import argparse
import ssl
import json
from subprocess import PIPE, Popen, check_output
import paho.mqtt.client as mqtt
from bme280 import BME280
from pms5003 import PMS5003, ReadTimeoutError, SerialTimeoutError
from enviroplus import gas
from ltr559 import LTR559
from smbus2 import SMBus
from PIL import Image, ImageDraw, ImageFont
from fonts.ttf import RobotoMedium as UserFont
import st7735

# Initialize sensors
ltr559 = LTR559()


def initialize_gps(serial_port):
    """Initialize the GPS module by sending necessary AT commands."""
    commands = [
        "AT\r",
        "AT+CGNSPWR=1\r"
    ]

    for command in commands:
        serial_port.write(command.encode())
        time.sleep(1)
        response = serial_port.read_all().decode()
        print(f"Sent: {command.strip()}\nReceived: {response.strip()}\n")


def get_gps_coordinates(serial_port):
    """Fetch GPS coordinates from the SIM7070G GNSS."""
    serial_port.write("AT+CGNSINF\r".encode())
    time.sleep(2)
    response = serial_port.read_all().decode()

    if "+CGNSINF:" in response:
        data = response.split("+CGNSINF: ")[1].split(",")
        fix_status = data[1]  # 1 indicates valid fix

        if fix_status == "1":
            latitude = data[3]
            longitude = data[4]
            return float(latitude), float(longitude)
    else:
        print("Error retrieving GPS data.")

    return '', ''


def read_bme280(bme280):
    comp_factor = 2.25
    values = {}
    try:
        cpu_temp = get_cpu_temperature()
        raw_temp = bme280.get_temperature()
        comp_temp = raw_temp - ((cpu_temp - raw_temp) / comp_factor)
        values["temperature"] = int(comp_temp)
        values["pressure"] = round(int(bme280.get_pressure() * 100), -1)
        values["humidity"] = int(bme280.get_humidity())
        data = gas.read_all()
        values["oxidised"] = int(data.oxidising / 1000)
        values["reduced"] = int(data.reducing / 1000)
        values["nh3"] = int(data.nh3 / 1000)
    except Exception as e:
        print(f"Error reading BME280 data: {e}")
        values = {"temperature": 0, "pressure": 0, "humidity": 0, "oxidised": 0, "reduced": 0, "nh3": 0}
    return values


def read_pms5003(pms5003):
    values = {}
    try:
        pm_values = pms5003.read()
        values["pm1"] = pm_values.pm_ug_per_m3(1)
        values["pm25"] = pm_values.pm_ug_per_m3(2.5)
        values["pm10"] = pm_values.pm_ug_per_m3(10)
    except ReadTimeoutError:
        try:
            pms5003.reset()
            pm_values = pms5003.read()
            values["pm1"] = pm_values.pm_ug_per_m3(1)
            values["pm25"] = pm_values.pm_ug_per_m3(2.5)
            values["pm10"] = pm_values.pm_ug_per_m3(10)
        except Exception as e:
            print(f"Error reading PMS5003 data: {e}")
            values = {"pm1": 0, "pm25": 0, "pm10": 0}
    return values


def get_cpu_temperature():
    process = Popen(["vcgencmd", "measure_temp"], stdout=PIPE, universal_newlines=True)
    output, _error = process.communicate()
    return float(output[output.index("=") + 1:output.rindex("'")])


def collect_data(serial_port, bme280, pms5003, has_pms):
    try:
        timestamp = int(time.time())
        latitude, longitude = get_gps_coordinates(serial_port)
        bme280_data = read_bme280(bme280)
        if has_pms:
            pms_data = read_pms5003(pms5003)
        else:
            pms_data = {"pm1": 0, "pm25": 0, "pm10": 0}

        data_list = [
            f"car_{{}}", timestamp, latitude, longitude,
            pms_data.get("pm1", 0), pms_data.get("pm25", 0), pms_data.get("pm10", 0),
            bme280_data.get("oxidised", 0), bme280_data.get("reduced", 0), bme280_data.get("nh3", 0)
        ]
        return data_list
    except Exception as e:
        print(f"Error collecting data: {e}")
        return ["car_{}", 0, '', '', 0, 0, 0, 0, 0, 0]


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
    else:
        print(f"Failed to connect, return code {rc}")


def on_publish(client, userdata, mid):
    print(f"Message {mid} published.")


def main():
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_publish = on_publish

    try:
        mqtt_client.connect("150.140.186.118", 1883)
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")
        return

    bus = SMBus(1)
    bme280 = BME280(i2c_dev=bus)

    try:
        pms5003 = PMS5003()
        _ = pms5003.read()
        has_pms = True
    except SerialTimeoutError:
        print("No PMS5003 sensor connected.")
        has_pms = False

    try:
        serial_port = serial.Serial(port="/dev/ttyUSB0", baudrate=9600, timeout=1)
        if serial_port.isOpen():
            print("Serial port opened successfully.")
            initialize_gps(serial_port)
        else:
            print("Failed to open serial port.")
            return
    except Exception as e:
        print(f"Error initializing GPS: {e}")
        return

    mqtt_client.loop_start()

    try:
        while True:
            data = collect_data(serial_port, bme280, pms5003, has_pms)
            print(f"Collected data: {data}")
            mqtt_client.publish("apars_cars", json.dumps(data), retain=True)
            time.sleep(3)
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'serial_port' in locals() and serial_port.isOpen():
            serial_port.close()
            print("Serial port closed.")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

if __name__ == "__main__":
    main()




