
from signal import SIGINT, signal, SIGTERM, SIGHUP
from time import sleep
from funcs import failed_reading, normal_measures
from file_helper import get_user

import concurrent.futures

from ultrasonic_sensor import wait_hand_detect, detecting_hand
from read_max30100 import read_max30100
from read_temp import read_temp
from LCD import run_lcd, print_results, print_measuring
from firestore_helper import write_record_firestore
from user_authenticator import user_authenticator
from google_wavenet import speak_results
from sms import health_worker_sms

# Constants
stop_reading_time = 5 # in seconds  


# Store
program_store = {
    "user": get_user(), #user.name, user.id, user.healthWorkers[{name, number}]
    "temp": 0.0,
    "pulse": 0,
    "spo2": 0,
    "confirm_code": 0,
    "confirm_code_sec": 20,
}


# Vars
program_status = {
    "alive": True,
    "reading": False,
    "detecting_hand": False,
    "measure_error": False,
    "show_results": False,
    "is_pairing": False,
    "paired_new_user": False,
}

#Initialize signal interrupts
def safe_exit(signum, frame):
    program_status["alive"] = False
    print("\n---EXITED SAFELY---")
    exit(1)

signal(SIGTERM, safe_exit)
signal(SIGHUP, safe_exit)
signal(SIGINT, safe_exit)




def on_measure_success(temp: float, pulse: int, spo2: int):
    '''determines What to do with the data'''
    print_results(temp, pulse, spo2)
    program_store["temp"] = temp
    program_store["pulse"] = pulse
    program_store["spo2"] = spo2
    

    with concurrent.futures.ThreadPoolExecutor() as executor:
        ################# SEND MESSAGE IF NOT NORMAL READINGS
        if not normal_measures(temp, pulse, spo2):
            executor.submit(health_worker_sms, program_store)

        ################# SPEAK OUT GOOGLE TTS
        executor.submit(speak_results, temp, pulse, spo2, program_store["user"])
        
        ################# UPLOAD DATA TO FIREBASE
        executor.submit(write_record_firestore, program_store["user"], temp, pulse, spo2)




def measure():
    while program_status["alive"]:
        with concurrent.futures.ThreadPoolExecutor() as executor:

            # Ultrasonic sensor waits for hand detection before continuing
            #thread_wait_hand_detect = executor.submit(wait_hand_detect, program_status, 1, 0.2)
            #thread_wait_hand_detect.result()

            wait_hand_detect(program_status, 0.5, 0.2)

            # Return if the program exited already
            if not program_status["alive"]:
                return

            # Start reading from temperature and heart rate sensors
            program_status["reading"] = True

            # Execute concurrently
            executor.submit(print_measuring, program_status)
            thread_temp = executor.submit(read_temp)
            thread_max30100 = executor.submit(read_max30100, program_status)
            executor.submit(detecting_hand, program_status)

            # Waits for temperature, pulse, and SpO2 before continuing
            temp = thread_temp.result(60)
            pulse, spo2 = thread_max30100.result(60)

            

            # End reading from temperature and heart rate sensors and start showing results to LCD
            program_status["reading"] = False
            
            if not program_status["detecting_hand"]:
                print("No Hand Detected")
                continue

            program_status["show_results"] = True

            # Stop measuring on failed readings
            if (failed_reading(temp, pulse, spo2)):
                program_status["measure_error"] = True
                return

            # Determines what to do with the measured data
            on_measure_success(temp, pulse, spo2)

            program_status["show_results"] = False
            # Sleep for some time before starting to measure again
            # sleep(stop_reading_time)

            

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.submit(measure)
    executor.submit(run_lcd, program_status, program_store)
    executor.submit(user_authenticator, program_status, program_store)

