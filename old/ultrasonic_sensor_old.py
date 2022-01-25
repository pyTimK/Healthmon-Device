from time import sleep
from typing import Dict
from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory

pigpio_factory = PiGPIOFactory()
distance_sensor = DistanceSensor(echo=21, trigger=20, pin_factory=pigpio_factory)

# CONSTANTS
max_read_distance = 10 # in cm



def wait_hand_detect(program_status: Dict[str, bool] ,total_time: float, interval: float):
    print("\nReady to measure")
    
 
    try:
        sensing_time = 0
        print("sensing time: " + str(sensing_time))
        while program_status["alive"]:
            distance = int(distance_sensor.value * 100);  #in cm
            print(distance)
            if distance < max_read_distance:
                sensing_time += interval
                if sensing_time > total_time:
                    return
            
            else:
                sensing_time = 0

            sleep(interval)
        
        #Program is now not alive
        distance_sensor.close()

    except:
        print("Ultrasonic sensor error")
        

wait_hand_detect({"alive": True}, 1, 0.2)