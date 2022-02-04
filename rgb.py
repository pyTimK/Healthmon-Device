from typing import Dict
from gpiozero import RGBLED
from time import sleep
from signal import pause
from funcs import is_normal_from_program_store

led = RGBLED(red=10, green=9, blue=11)
brightness = 0.5

colors = {
    "white": (1,1,1),
    "pink": (1,0.1,0.4),
    "green": (0,1,0),
    "red": (1,0,0),
    "bluegreen": (0,1,1),
    "orange": (1,0.1,0),
    "magenta": (1,0,1),
    "blue": (0,0,1),
    "none": (0,0,0),
    "dim": (0.05,0.05,0.05),
}

for color in colors:
    colors[color] = tuple([i * brightness for i in colors[color]])



def run_rgb(program_status: Dict[str, bool], program_store: Dict):
    prev_status = 0
    while program_status["alive"]:

        # print(program_status)
        # print(datetime.now().ctime())
        if program_status["paired_new_user"]:
            if prev_status != 1:
                led.blink(on_time=0.4, off_time=0.4, on_color=colors["green"])
                prev_status = 1

        elif program_status["is_pairing"]:
            if prev_status != 2:
                led.color = colors["green"]
                prev_status = 2
            
        elif program_status["measure_error"]:
            if prev_status != 3:
                led.color = colors["red"]
                prev_status = 3

        elif program_status["show_results"]:
            if prev_status != 4:
                led.color = colors["bluegreen"] if is_normal_from_program_store(program_store) else colors["orange"]
                prev_status = 4

        elif program_status["reading"]:
            if prev_status != 5:
                led.pulse(on_color=colors["dim"],off_color=colors["pink"])
                prev_status = 5

        else:
            if prev_status != 6:
                led.color = colors["pink"]
                prev_status = 6
        
        sleep(0.9)
    
    
    led.close()

# TESTING--------------------------------
# _program_store = {
#     "temp": 0.0,
#     "pulse": 0,
#     "spo2": 0,
#     "confirm_code": 0,
#     "confirm_code_sec": 20,
#     "hw_listener_unsub": None,
#     "device_listener_unsub": None,
# }
# # Vars
# _program_status = {
#     "alive": True,
#     "reading": True,
#     "detecting_hand": False,
#     "measure_error": False,
#     "show_results": False,
#     "is_pairing": False,
#     "paired_new_user": False,
#     "shutdown": False,
# }
# run_rgb(_program_status, _program_store)
# ---------------------------------------
