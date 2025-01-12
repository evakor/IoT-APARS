import serial
import time
import json
from subprocess import PIPE, Popen
import paho.mqtt.client as mqtt
from bme280 import BME280
from pms5003 import PMS5003, ReadTimeoutError, SerialTimeoutError
from enviroplus import gas
from ltr559 import LTR559
from smbus2 import SMBus
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
from scd30_i2c import SCD30
import statistics

# Initialize sensors
ltr559 = LTR559()

# Initialize I2C bus and devices
bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)
adc = ADS1115(bus, address=0x48)
scd30 = SCD30()

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

def read_mq_sensors(adc):
    """Read MQ sensors connected to ADS1115."""
    mq_data = {
        "mq2": AnalogIn(adc, 0).value,
        "mq135": AnalogIn(adc, 1).value,
        "mq7": AnalogIn(adc, 2).value,
    }
    return mq_data

def read_scd30():
    """Read data from the SCD30 sensor."""
    if scd30.get_ready_status():
        co2 = scd30.read_measurement()
        return {
            "co2": co2[0],
            "temperature": co2[1],
            "humidity": co2[2]
        }
    return {"co2": 0, "temperature": 0, "humidity": 0}

def calculate_mean(values):
    """Calculate the mean of a list of values, ignoring zeros."""
    filtered_values = [v for v in values if v > 0]
    if filtered_values:
        return statistics.mean(filtered_values)
    return 0

def collect_data(serial_port, pms5003, has_pms, adc):
    try:
        timestamp = int(time.time())
        latitude, longitude = get_gps_coordinates(serial_port)

        bme280_data = {
            "temperature": bme280.get_temperature(),
            "pressure": bme280.get_pressure(),
            "humidity": bme280.get_humidity()
        }

        if has_pms:
            try:
                pm_data = pms5003.read()
                pms5003_data = {
                    "pm1": pm_data.pm_ug_per_m3(1),
                    "pm25": pm_data.pm_ug_per_m3(2.5),
                    "pm10": pm_data.pm_ug_per_m3(10)
                }
            except Exception as e:
                print(f"Error reading PMS5003: {e}")
                pms5003_data = {"pm1": 0, "pm25": 0, "pm10": 0}
        else:
            pms5003_data = {"pm1": 0, "pm25": 0, "pm10": 0}

        mq_data = read_mq_sensors(adc)

        tvoc_eco2_data = {
            "tvoc": gas.read_all().oxidising,
            "eco2": gas.read_all().reducing
        }

        scd30_data = read_scd30()

        # Combine data for mean calculation where applicable
        temperature_values = [bme280_data["temperature"], scd30_data["temperature"]]
        humidity_values = [bme280_data["humidity"], scd30_data["humidity"]]

        combined_data = {
            "timestamp": timestamp,
            "latitude": latitude,
            "longitude": longitude,
            "temperature": calculate_mean(temperature_values),
            "humidity": calculate_mean(humidity_values),
            "pressure": bme280_data["pressure"],
            "pm1": pms5003_data["pm1"],
            "pm25": pms5003_data["pm25"],
            "pm10": pms5003_data["pm10"],
            "mq_sensors": mq_data,
            "tvoc": tvoc_eco2_data["tvoc"],
            "eco2": tvoc_eco2_data["eco2"],
            "co2": scd30_data["co2"]
        }

        combined_data = [timestamp, latitude, longitude, calculate_mean(temperature_values), calculate_mean(humidity_values), 
                         bme280_data["pressure"], pms5003_data["pm1"], pms5003_data["pm25"], pms5003_data["pm10"], mq_data, 
                         tvoc_eco2_data["tvoc"], tvoc_eco2_data["eco2"], scd30_data["co2"]]

        return combined_data
    except Exception as e:
        print(f"Error collecting data: {e}")
        return {}

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

    try:
        pms5003 = PMS5003()
        _ = pms5003.read()
        has_pms = True
    except SerialTimeoutError:
        print("No PMS5003 sensor connected.")
        has_pms = False

    try:
        serial_port = serial.Serial(port="/dev/ttyUSB5", baudrate=9600, timeout=1) # Find the correct USB port
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
            data = collect_data(serial_port, pms5003, has_pms, adc)
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
