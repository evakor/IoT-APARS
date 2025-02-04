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
import math
from sgp30 import SGP30

# MQ-Sensor data
VC = 5.0          # Circuit voltage (V)
RL_MQ2 = 10000    # Load resistance for MQ-2 (Ohms)
RL_MQ7 = 10000    # Load resistance for MQ-7 (Ohms)
RL_MQ135 = 20000  # Load resistance for MQ-135 (Ohms)
RO_MQ2 = 10000    # Sensor resistance in clean air for MQ-2 (Ohms)
RO_MQ7 = 10000    # Sensor resistance in clean air for MQ-7 (Ohms)
RO_MQ135 = 30000  # Sensor resistance in clean air for MQ-135 (Ohms)

# Sensitivity curve parameters (slope and intercept)
A_MQ2, B_MQ2 = -0.47, 0.72
A_MQ7, B_MQ7 = -0.48, 0.68
A_MQ135, B_MQ135 = -0.45, 0.77

ltr559 = LTR559()

# Initialize I2C bus and devices
bus = SMBus(1)
bme280 = BME280(i2c_dev=bus)
adc = ADS1115(bus, address=0x48)
scd30 = SCD30()
sgp30 = SGP30(i2c_dev=bus)
sgp30.init_air_quality()

def initialize_gps(serial_port):
    commands = ["AT\r", "AT+CGNSPWR=1\r"]
    for command in commands:
        serial_port.write(command.encode())
        time.sleep(1)
        response = serial_port.read_all().decode()
        print(f"Sent: {command.strip()}\nReceived: {response.strip()}\n")

def get_gps_coordinates(serial_port):
    serial_port.write("AT+CGNSINF\r".encode())
    time.sleep(2)
    response = serial_port.read_all().decode()
    if "+CGNSINF:" in response:
        data = response.split("+CGNSINF: ")[1].split(",")
        fix_status = data[1]
        if fix_status == "1":
            latitude = data[3]
            longitude = data[4]
            return float(latitude), float(longitude)
    else:
        print("Error retrieving GPS data.")
    return '', ''

# Function to convert analog value (0-1024) to PPM
def convert_analog_to_ppm(adc, channel, RL, RO, A, B):
    analog_value = AnalogIn(adc, channel).value
    v_out = (analog_value / 1023.0) * VC

    if v_out == 0:
        return 0

    rs = RL * ((VC - v_out) / v_out)

    try:
        ratio = rs / RO
        ppm = 10 ** (A * math.log10(ratio) + B)
        return ppm
    except (ValueError, ZeroDivisionError):
        return 0

def read_mq2_ppm(adc):
    return convert_analog_to_ppm(adc, channel=2, RL=RL_MQ2, RO=RO_MQ2, A=A_MQ2, B=B_MQ2)

def read_mq7_ppm(adc):
    return convert_analog_to_ppm(adc, channel=0, RL=RL_MQ7, RO=RO_MQ7, A=A_MQ7, B=B_MQ7)

def read_mq135_ppm(adc):
    return convert_analog_to_ppm(adc, channel=1, RL=RL_MQ135, RO=RO_MQ135, A=A_MQ135, B=B_MQ135)

def read_scd30():
    if scd30.get_ready_status():
        co2 = scd30.read_measurement()
        return co2[0], co2[1], co2[2]
    return 0, 0, 0

def read_sgp30():
    try:
        air_quality = sgp30.get_air_quality()
        return air_quality.equivalent_co2, air_quality.total_voc
    except Exception as e:
        print(f"Error reading SGP30: {e}")
        return 0, 0

def calculate_mean(values):
    filtered_values = [v for v in values if v > 0]
    if filtered_values:
        return statistics.mean(filtered_values)
    return 0

def collect_data(serial_port, pms5003, has_pms, adc):
    try:
        timestamp = int(time.time())
        latitude, longitude = get_gps_coordinates(serial_port) # Lat, Lon

        bme280_data = [
            bme280.get_temperature(), # Temperature
            bme280.get_pressure(), # Pressure
            bme280.get_humidity() # Humidity
        ]

        if has_pms:
            try:
                pm_data = pms5003.read()
                pms5003_data = [
                    pm_data.pm_ug_per_m3(1),  # PM1
                    pm_data.pm_ug_per_m3(2.5),  # PM2.5
                    pm_data.pm_ug_per_m3(10)  # PM10
                ]
            except Exception as e:
                print(f"Error reading PMS5003: {e}")
                pms5003_data = [0, 0, 0]
        else:
            pms5003_data = [0, 0, 0]

        mq2 = read_mq2_ppm(adc) # Gas leak
        mq135 = read_mq7_ppm(adc) # Benzene
        mq7 = read_mq135_ppm(adc) # CO

        gas_data = gas.read_all()
        oxidizing = gas_data.oxidising # Hydrogen, Ethanol, Ammmonia, Propane, Iso-butane
        reducing = gas_data.reducing # NO, NO2, H
        nh3 = gas_data.nh3 # NH3

        co2, scd30_temp, scd30_humidity = read_scd30() # CO2
        eco2, tvoc = read_sgp30() # eCO2, TVOC

        temperature = calculate_mean([bme280_data[0], scd30_temp])
        humidity = calculate_mean([bme280_data[2], scd30_humidity])

        combined_data = [
            "grhgorhs",
            timestamp,
            latitude,
            longitude,
            temperature,     # Temperature in Celcius
            humidity,        # Humidity in Percentage
            bme280_data[1],  # Pressure in atm
            *pms5003_data,   # PM1, PM2.5, PM10 in g/m^3
            mq2,             # LPG in ppm (MQ2)
            mq135,           # Benzene in ppm (MQ135)
            mq7,             # CO in ppm (MQ7)
            oxidizing,       # Oxidizing in ppm (Enviroplus)
            reducing,        # Reducing in ppm (Enviroplus)
            nh3,             # NH3 in ppm (Enviroplus)
            co2,             # CO2 in ppm (SCD30)
            eco2,            # eCO2 in ppm (SGP30)
            tvoc             # TVOC in ppb (SGP30)
        ]
        return combined_data
    except Exception as e:
        print(f"Error collecting data: {e}")
        return []

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
