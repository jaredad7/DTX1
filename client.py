# import any additional libraries
import time, sys, requests, hashlib, getpass, random, threading, Adafruit_ADS1x15
import boto3, json
from datetime import datetime
import time
from yoctopuce.yocto_api import *
from yoctopuce.yocto_voltage import *
from yoctopuce.yocto_temperature import *

# Initialize globals
global read_speed
read_speed = 2.0
global volt
volt = 0
global temp
temp = 0
global wind
wind = 0


# Reads sensor voltage and writes to volt
def voltage():
    global volt
    global read_speed
#    errmsg = YRefParam()
#    YAPI.RegisterHub("usb", errmsg)
#    print(errmsg.value)
    sensor = YVoltage.FirstVoltage()
    if sensor is not None:
        serial = sensor.get_module().get_serialNumber()
        sensorDC = YVoltage.FindVoltage(serial + '.voltage1')
        while sensor is not None:
            volt = abs(sensorDC.get_currentValue())
            time.sleep(read_speed / 2.0)
    print("volt received")
    volt = "err"


# Reads sensor temperature and writes to temp
def temperature():
    global temp
    global read_speed
    sensor = YTemperature.FirstTemperature()
    if sensor is not None:
        serial = sensor.get_module().get_serialNumber()
        sensorTemp = YTemperature.FindTemperature(serial + '.temperature2')
        while sensor is not None:
            temp = sensorTemp.get_currentValue()
            time.sleep(read_speed / 2.0)
    print("temp received")
    temp = "err"


# Translates voltage into windspeed
# Formula: speed = (20.2 * v) - 8.1
# We are receiving a digital_value from our A-to-D converter which is directly proportional to the voltage
# Formula: v = (.00071 * digital_value) - 1.55556
def windspeed_translation(digital_value):
    v = (.0000625019 * digital_value) # volts
    speed = (20.2 * v) - 8.1  # m/s
    return speed


# Reads and returns sensor windspeed
def windspeed():
    global wind
    global read_speed
    wind = abs(windspeed_translation(adc.read_adc(PIN, GAIN)))
    wind = str(wind)
    time.sleep(read_speed / 2.0)
#    print("wind received")


# Will restart dead threads
def threadmonitor(threads):
    if not threads["readvolt"].isAlive():
        YAPI.RegisterHub("usb")
        threads["readvolt"] = threading.Thread(target = voltage)
        threads["readvolt"].setDaemon(True)
        threads["readvolt"].start()
    if not threads["readtemp"].isAlive():
        YAPI.RegisterHub("usb")
        threads["readtemp"] = threading.Thread(target = temperature)
        threads["readtemp"].setDaemon(True)
        threads["readtemp"].start()
    if not threads["readwind"].isAlive():
        threads["readwind"] = threading.Thread(target = windspeed)
        threads["readwind"].setDaemon(True)
        threads["readwind"].start()
    if not threads["write"].isAlive():
        threads["write"] = threading.Thread(target = single_turbine)
        threads["write"].setDaemon(True)
        threads["write"].start()
    if not threads["entire"].isAlive():
        threads["entire"] = threading.Thread(target = all_turbines)
        threads["entire"].setDaemon(True)
        threads["entire"].start()


# MAIN

# Define kinesis stream
my_stream_name = 'dataline15'
my_stream_name2 = 'allStream10'
kinesis_client = boto3.client('kinesis', region_name='us-east-1')
kinesis_client2 = boto3.client('kinesis', region_name='us-east-1')

# Initialize API to interact with Yoctopuce products
YAPI.RegisterHub("usb")

# Initialize API to interact with A-to-D converter
adc = Adafruit_ADS1x15.ADS1115()
GAIN = 2
PIN = 0

# write to kinesis
def single_turbine():
    #print("sending single data")
    while True:
    #    ts = time.time()
        print("Writing one")
        global read_speed
        ts = str(time.time())
        global wind
        wind = str(wind)
        global volt
        volt = str(volt)
        global temp
        temp = str(temp)
        status = "ONLINE"
        if (volt == "err" or temp == "err"):
            print("Error found: turbine offline")
            status = "OFFLINE"

        payload = {
            'turbineId': int(1),
            'windSpeed': wind,
            'voltage': volt,
            'temp': temp,
            'status': status,
            'recordTime': ts+"a"
        }

        kinesis_client.put_record(
            StreamName=my_stream_name,
            Data=json.dumps(payload),
            PartitionKey=ts)

        time.sleep(read_speed)

def all_turbines():
    #print("sending all data")
    while True:
        print("Writing all")
        global read_speed
        ts = str(time.time())
        global wind
        wind = str(wind)
        global volt
        volt = str(volt)
        global temp
        temp = str(temp)
        status = "ONLINE"
        if (volt == "err" or temp == "err"):
            print("Error found: turbine offline")
            status = "OFFLINE"
        
        payload2 = {
            'turbineId': int(1),
            'entire': "entire",
            'windSpeed': wind,
            'voltage': volt,
            'temp': temp,
            'status': status,
            'recordTime': ts+"a"
        }

        kinesis_client2.put_record(
            StreamName=my_stream_name2,
            Data=json.dumps(payload2),
            PartitionKey="entire")

#         print("{}: {}".format("id", 3))
#         print("{}: {}".format("time", ts))
#         print("{}: {}".format("volt", volt))
#         print("{}: {}".format("temp", temp))
#         print("{}: {}".format("wind", wind))
#         print("{}: {}".format("status", status))
#         print

        time.sleep(read_speed)

# This dictionary allows us to restart individual threads in case they die
threads = dict()

# Define threads
threads["readvolt"] = threading.Thread(target = voltage)
threads["readtemp"] = threading.Thread(target = temperature)
threads["readwind"] = threading.Thread(target = windspeed)
threads["write"] = threading.Thread(target = single_turbine)
threads["entire"] = threading.Thread(target = all_turbines)

# Set Daemon to True to catch ^C signal
threads["readvolt"].setDaemon(True)
threads["readtemp"].setDaemon(True)
threads["readwind"].setDaemon(True)
threads["write"].setDaemon(True)
threads["entire"].setDaemon(True)

# Start Threads
threads["readvolt"].start()
threads["readtemp"].start()
threads["readwind"].start()
threads["write"].start()
threads["entire"].start()

# Main loop
while True:
#    time.sleep(read_speed)
    threadmonitor(threads)
