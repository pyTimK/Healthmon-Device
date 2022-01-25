from signal import signal, SIGTERM, SIGHUP, pause
from time import sleep
from threading import Thread

import board
import busio as io
import adafruit_mlx90614
import max30100
from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory

# Constants
temp_calibrate = 2.7
pulse_calibrate = -120
spo2_calibrate_max = 150
max_read_distance = 10 # in cm
stop_reading_time = 5

#Initialize signal interrupts
def safe_exit(signum, frame):
    exit(1)

signal(SIGTERM, safe_exit)
signal(SIGHUP, safe_exit)


# Initialize sensors
i2c = io.I2C(board.SCL, board.SDA, frequency=100000)
mlx = adafruit_mlx90614.MLX90614(i2c)
mx30 = max30100.MAX30100()
mx30.enable_spo2()
pigpio_factory = PiGPIOFactory()
distance_sensor = DistanceSensor(echo=21, trigger=20, pin_factory=pigpio_factory)

alive = True
reading = False



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

def print_results(temp: float, pulse: int, spo2: int):
    print('---')
    print(f'{temp:.1f} °C')
    print(f'Pulse: {pulse} BPM')
    print(f'SPO2: {spo2} %')

def measure():
    mx30.read_sensor()
    return readTemp(), readPulse(), readspo2()

def ave(l, rounded = False):
    return sum(l) // len(l) if rounded else sum(l) / len(l)

def start_real_measure(sec: int, interval: float):
    elapsed = 0.0
    temps = []
    pulses = []
    spo2s = []
    while alive and elapsed < sec:
        temp, pulse, spo2 = measure()
        temps.append(temp)
        pulses.append(pulse)
        spo2s.append(spo2)
        elapsed += interval

    return ave(temps), ave(pulses, rounded=True), ave(spo2s, rounded=True)

def init_measure():
    while alive and is_valid(*measure()):
        pass

    while alive:
        if is_valid(*measure()):
            final_temp, final_pulse, final_spo2 = start_real_measure(5, 0.3)
            print_results(final_temp, final_pulse, final_spo2)
            #mx30.buffer_red = []
            #mx30.buffer_ir = []
            return
        
        
        sleep(0.3)

def print_measuring():
    dots = 0
    print(f"reading: {reading}")
    while alive and reading:
        print(f"Measuring{'.' * dots}")
        dots = (dots + 1) % 3
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
                measurement = Thread(target = init_measure, daemon = True)
                measurement.start()
                print_measuring_thread = Thread(target = print_measuring, daemon = True)
                print_measuring_thread.start()
                measurement.join()
                reading = False
                print_measuring_thread.join()
                
                
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

