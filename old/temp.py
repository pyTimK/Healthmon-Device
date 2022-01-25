import json
import firebase_admin
from firebase_admin import credentials, firestore

from datetime import datetime
from signal import signal, SIGTERM, SIGHUP, pause
from time import sleep
from threading import Thread
import socket
import subprocess

import board
import busio as io
import adafruit_mlx90614
import max30100
from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory


# Constants
temp_calibrate = 2.2
# pulse_calibrate = -120
# spo2_calibrate_max = 150
pulse_calibrate = 0
spo2_calibrate_max = 100

max_read_distance = 10 # in cm
stop_reading_time = 5

# Firebase Init
firestore_cred = credentials.Certificate(
    "/home/pi/c/healthmonmikee-firebase-adminsdk-c1uro-9e5dba3d2b.json")
firebase_admin.initialize_app(firestore_cred)
db = firestore.client()

def get_formatted_day():
    return datetime.today().strftime('%Y-%m-%d')

def get_formatted_hours():
    return datetime.today().strftime('%H-%M-%S')


def write_record_firestore(uid: str, name: str, temp: float, pulse: int, spo2: int):
    try:
        record_doc_ref = db.collection('records').document(get_formatted_day()).collection(uid).document(get_formatted_hours())
        record_doc_ref.set({"timestamp": datetime.now(), "name": name, "temp": temp, "pulse": pulse, "spo2": spo2})
        print("---Successfully written record to firestore---") 
    except:
        print("---Failed to write record to firestore---")

    
#Initialize signal interrupts
def safe_exit(signum, frame):
    exit(1)

signal(SIGTERM, safe_exit)
signal(SIGHUP, safe_exit)


def has_internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print("No internet connection")
        return False


# Initialize sensors
i2c = io.I2C(board.SCL, board.SDA, frequency=100000)
mlx = adafruit_mlx90614.MLX90614(i2c)
mx30 = max30100.MAX30100()
mx30.enable_spo2()
pigpio_factory = PiGPIOFactory()
distance_sensor = DistanceSensor(echo=21, trigger=20, pin_factory=pigpio_factory)

alive = True
reading = False


# hel
def readTemp():
    return mlx.object_temperature + temp_calibrate

def readPulse():
    pulse = (mx30.ir // 100) + pulse_calibrate
    return 0 if pulse < 0 else pulse

def readspo2():
    spo2 = mx30.red // spo2_calibrate_max
    return 100 if spo2 > 100 else spo2

def is_valid(temp: float, pulse: int, spo2: int):
    return pulse > 10 and spo2 > 30

def ave(l, rounded = False):
    return sum(l) // len(l) if rounded else sum(l) / len(l)

def measure():
    mx30.read_sensor()
    return readTemp(), readPulse(), readspo2()

# 'sec' is the window readings, 'interval' determines how often should we read
def get_measure(sec: int, interval: float):
    # Flush out previous valid readings
    while alive and is_valid(*measure()):
        pass

    # Wait for readings to start being valid
    while alive and not is_valid(*measure()):
        sleep(0.3)
    
    elapsed = 0.0
    temps = []; pulses = []; spo2s = []
    while alive and elapsed < sec:
        temp, pulse, spo2 = measure()
        temps.append(temp); pulses.append(pulse); spo2s.append(spo2)
        elapsed += interval
    
    return ave(temps), ave(pulses, rounded=True), ave(spo2s, rounded=True)

def print_results(temp: float, pulse: int, spo2: int):
    print('---')
    print(f'{temp:.1f} °C')
    print(f'Pulse: {pulse} BPM')
    print(f'SPO2: {spo2} %')

def print_measuring():
    dots = 0
    while alive and reading:
        print(f"Measuring{'.' * dots}")
        dots = (dots + 1) % 4
        sleep(1)

def read_distance(total_time: float, interval: float):
    global reading
    sensing_time = 0
    while alive:
        distance = int(distance_sensor.value * 100);  #in cm
        #print(f"sensing_time: {sensing_time:.1f} s")
        
        if distance < max_read_distance:
            sensing_time += interval
            if sensing_time > total_time:
                reading = True
                print_measuring_thread = Thread(target = print_measuring, daemon = True)
                print_measuring_thread.start()

                try:
                    temp, pulse, spo2 = get_measure(5, 0.3)
                
                except:
                    print("Error measuring")
                    continue
                
                finally:
                    reading = False
                
                # What to do with the data
                print_results(temp, pulse, spo2)
                
                user = None
                with open("/home/pi/paired_user.txt", "r") as f:
                    read_data = f.read()
                    user = json.loads(read_data)
                
                # user.name, user.id, user.healthWorkers[{name, number}]
                
                print(user)
                
                ################# 1. SHOW RESULTS TO LCD
                ################# 2. SEND MESSAGE IF ABNORMAL
                
                # JAN 18 (TUES) TODO
                ################# 3. SPEAK OUT GOOGLE TTS
                
                
                ################# 4. UPLOAD DATA TO FIREBASE
                if has_internet():
                    write_record_firestore(user["id"], user["name"], temp, pulse, spo2)
                
                
                
                sensing_time = 0
                sleep(stop_reading_time)
        
        else:
            sensing_time = 0
        
        sleep(interval)

try:
    read_distance(1, 0.2)
    pause()

except KeyboardInterrupt:
    pass

finally:
    reading = False
    alive = False
    distance_sensor.close()
    pass
    #sensor.close();


