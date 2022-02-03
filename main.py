import subprocess
from signal import SIGINT, signal, SIGTERM, SIGHUP
from time import sleep
from funcs import failed_reading, normal_measures
from file_helper import get_user
from setproctitle import setproctitle
import concurrent.futures

from ultrasonic_sensor import wait_hand_detect, detecting_hand
from read_max30100 import read_max30100
from read_temp import read_temp
from LCD import run_lcd, print_results, print_measuring
from firestore_helper import write_record_firestore
from user_authenticator import user_authenticator
from google_wavenet import speak_results
from sms import health_worker_sms
from startup_shutdown import play_startup_sound, play_shutdown_sound, shutdown_rpi


try:
    setproctitle("healthmon")
except:
    print("Falied to set process name")

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
    "hw_listener_unsub": None,
    "device_listener_unsub": None,
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
    "shutdown": False,
}

# Subscriptions

#Initialize signal interrupts
def safe_exit(signum, frame):
    program_status["alive"] = False
    hw_listener_unsub = program_store["hw_listener_unsub"]
    device_listener_unsub = program_store["device_listener_unsub"]
    
    if hw_listener_unsub is not None:
        hw_listener_unsub.unsubscribe()

    if device_listener_unsub is not None:
        device_listener_unsub.unsubscribe()

    print("\n---EXITED SAFELY---")
    exit(0)

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
            wait_hand_detect(program_status, 0.5, 0.2)

            # Return if the program exited already
            if not program_status["alive"]:
                break

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

    # print(program_status["shutdown"])
    if program_status["shutdown"]:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(play_shutdown_sound)

        sleep(1)
        print("\n---EXITED SAFELY---")
        sleep(1)
        subprocess.run(['sudo','shutdown', 'now'])

        

            


with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.submit(measure)
    executor.submit(run_lcd, program_status, program_store)
    thread_auth = executor.submit(user_authenticator, program_status, program_store)
    executor.submit(play_startup_sound)
    executor.submit(shutdown_rpi, program_status)
    

    

