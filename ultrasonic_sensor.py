from time import sleep
from typing import Dict
from gpiozero import DistanceSensor
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    distance_sensor = DistanceSensor(echo=21, trigger=20)

# CONSTANTS
max_read_distance = 10 # in cm


def wait_hand_detect(program_status: Dict[str, bool] ,total_time: float, interval: float):
    print("\nReady to measure")
    
 
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sensing_time = 0
            while program_status["alive"]:
                if program_status["is_pairing"] or program_status["paired_new_user"]:
                    sleep(1)
                    continue
                
                distance = int(distance_sensor.value * 100);  #in cm
                #print(distance)
                if distance < max_read_distance:
                    sensing_time += interval
                    if sensing_time > total_time:
                        program_status["detecting_hand"] = True
                        return
                
                else:
                    sensing_time = 0

                sleep(interval)
            
            #Program is now not alive
            distance_sensor.close()

    except:
        print("Ultrasonic sensor error")
        

_without_hand_reset_time = 6 # in seconds
_interval = 1

def detecting_hand(program_status: Dict[str, bool]):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            not_sensing_time = 0
            while program_status["alive"]:
                distance = int(distance_sensor.value * 100);  #in cm
                #print(distance)
                if distance > max_read_distance:
                    not_sensing_time += _interval
                    if not_sensing_time > _without_hand_reset_time:
                        program_status["detecting_hand"] = False
                        return
                
                else:
                    not_sensing_time = 0

                sleep(_interval)
            
            #Program is now not alive
            distance_sensor.close()

    except:
        print("Ultrasonic sensor error")




# Testing -----------------------
#wait_hand_detect({"alive": True}, 1, 0.2)
#--------------------------------
