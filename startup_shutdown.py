from typing import Dict
from gpiozero import Button
import subprocess




_shutdown_button = Button(19)


_startup_sound_loc = "/home/pi/Desktop/startup.mp3"
_shutdown_sound_loc = "/home/pi/Desktop/shutdown.mp3"



def play_startup_sound():
    subprocess.run(["mpg123", _startup_sound_loc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def play_shutdown_sound():
    subprocess.run(["mpg123", _shutdown_sound_loc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _shutdown(program_status: Dict[str, bool] = {}):
        print("\n---SHUTDOWN BUTTON PRESSED---")
        program_status["shutdown"] = True
        program_status["alive"] = False

def shutdown_rpi(program_status: Dict[str, bool]):

    _shutdown_button.when_pressed = lambda : _shutdown(program_status = program_status)


    