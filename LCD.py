from RPLCD import i2c
from datetime import datetime
from time import sleep
from typing import Dict
from funcs import day_greetings
from gpiozero import Button

_lcd_col = 20
_lcd_row = 4
_lcd = i2c.CharLCD('PCF8574', 0x27, charmap='A00')




_lcd_backlight_button = Button(26)

def _toggle_backlight():
    _lcd.backlight_enabled = not _lcd.backlight_enabled
    sleep(0.4)

def run_lcd(program_status: Dict[str, bool], program_store: Dict):
    _lcd.backlight_enabled = True
    dots = 0
    _lcd_backlight_button.when_pressed = _toggle_backlight

    while program_status["alive"]:
        user = program_store["user"]

        # print(program_status)
        # print(datetime.now().ctime())
        if program_status["paired_new_user"]:
            _show_device_paired()
        
        elif program_status["is_pairing"]:
            _show_confirm_code(program_store["confirm_code"], program_store["confirm_code_sec"])
        
        elif program_status["measure_error"]:
            _show_error()

        elif program_status["show_results"]:
            _show_results_vertical(program_store)

        elif program_status["reading"]:
            _show_measuring(dots)
            dots = (dots + 1) % 8

        else:
            dots = 0
            _show_idle(user["name"])
            #_hide_idle()
        
        sleep(0.9)
    
    

    # Close lcd on program exit
    _lcd.backlight_enabled = False
    _lcd.close(clear=True)



def print_results(temp: float, pulse: int, spo2: int):
    print('\n---')
    print(f'Temperature: {temp:.1f} °C')
    print(f'Heart Rate: {pulse} BPM')
    print(f'SpO2: {spo2} %')
    print('---\n')




def print_measuring(program_status: Dict[str, bool]):
    dots = 0
    while program_status["alive"] and program_status["reading"]:
        print(f"Measuring{'.' * dots}")
        dots = (dots + 1) % 4
        sleep(1)


def _show_device_paired():
    _write_lcd(
        "",
        "--Device Linked--".center(20),
        "",
        "",
    )

def _show_confirm_code(code: int, sec_left: int):
    _write_lcd(
        str(code).center(20),
        "",
        "code expires in".center(20),
        str(sec_left).center(20),
    )

def _show_results_horizontal(program_store: dict):
    name = program_store["user"]["name"]
    temp, pulse, spo2 = program_store["temp"], program_store["pulse"], program_store["spo2"]
    _write_lcd(
        f"Temp : {temp:.1f}°C",
        f"Pulse: {pulse}bpm",
        f"SpO2 : {spo2}%",
        name.rjust(_lcd_col),
    )

def _show_results_vertical(program_store: dict):
    name = program_store["user"]["name"]
    temp, pulse, spo2 = program_store["temp"], program_store["pulse"], program_store["spo2"]
    temp_str = f"{temp:.1f}".center(6)
    pulse_str = str(pulse).center(6)
    spo2_str = f"{spo2}%".center(6)
    _write_lcd(
        # " TEMP |  HR  | SpO2 ",
        f"{temp_str}|{pulse_str}|{spo2_str}",
        f"{'°C'.center(6)}|{'bpm'.center(6)}|{'SpO2'.center(6)}",
        f"      |      |      ",
        name.rjust(_lcd_col),
    )


def _show_idle(name: str):
    now = datetime.now()
    _write_lcd(
        day_greetings(),
        name,
        now.strftime("%b %d - %a").rjust(_lcd_col),
        now.strftime("%I:%M:%S %p").rjust(_lcd_col),
    )
    
def _hide_idle():
    _lcd.backlight_enabled = False
    _lcd.close(clear=True)

def _show_measuring(dots: int):
    _lcd.clear()
    _write_lcd(f"Measuring{'.' * dots}", " ", " ", " ")
    


def _show_error():
    _write_lcd("WARNING", "Measurement Failed", "", "Please restart")


def _write_lcd(l1: str, l2: str, l3: str, l4: str):
    l1, l2, l3, l4 = l1[:20], l2[:20], l3[:20], l4[:20]
    
    for i in range(100):
        try:
            _lcd.cursor_mode = "hide"
            _lcd.cursor_pos = (0, 0)
            _lcd.write_string(l1.ljust(_lcd_col))
            _lcd.crlf()
            _lcd.write_string(l2.ljust(_lcd_col))
            _lcd.crlf()
            _lcd.write_string(l3.ljust(_lcd_col))
            _lcd.crlf()
            _lcd.write_string(l4.ljust(_lcd_col))
            break        
        except:
            print("Encountered I/O Error to LCD!")
            _lcd.clear()


# TESTING ---------------------
def __testing():
    program_store1 = {
        "user": {"name": "Fuck"}, #user.name, user.id, user.healthWorkers[{name, number}]
        "temp": 36.7,
        "pulse": 102,
        "spo2": 98,
    }

    program_status1 = {
        "alive": True,
        "reading": False,
        "measure_error": False,
        "show_results": True,
    }
    run_lcd(program_status1, program_store1)

# __testing()
#------------------------------


