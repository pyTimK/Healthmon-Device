import os, sys
from datetime import datetime
from typing import Dict
import random

get_formatted_day = lambda : datetime.today().strftime('%Y-%m-%d')
get_formatted_hours = lambda : datetime.today().strftime('%H-%M-%S')
get_timestamp = lambda : datetime.now()



def failed_reading(temp: float, pulse: int, spo2: int) -> bool:
    #TODO print lcd error + "Try restarting"
    if temp == -1:
        print("Temperature module error")
        return True

    if -1 in [pulse, spo2]:
        print("Heart Rate module error")
        return True
    
    return False


def print_user(user: Dict):
    print('---')
    print(f"Name: {user['name']}")
    print(f"UID: {user['id']}")
    print(f"[Health Workers]")
    for health_worker in user['healthWorkers']:
        print(f"Name: {health_worker['name']}")
        print(f"Phone: {health_worker['number']}")
    print('---')



def normal_temp(temp: float) -> int:
    round(temp, 1)
    '''returns -1 if below normal, 0 if normal, and 1 if above normal'''
    if temp < 36.1:
        return -1
    if temp > 37.2:
        return 1
    return 0

def normal_pulse(pulse: int) -> int:
    '''returns -1 if below normal, 0 if normal, and 1 if above normal'''
    if pulse < 60:
        return -1
    if pulse > 100:
        return 1
    return 0

def normal_spo2(spo2: int) -> int:
    '''returns -1 if below normal and 0 if normal'''
    if spo2 < 95:
        return -1
    return 0


normal_measures = lambda temp, pulse, spo2: normal_temp(temp)==0 and normal_pulse(pulse)==0 and normal_spo2(spo2)==0
def is_normal_from_program_store(program_store: Dict) -> bool:
    return normal_measures(program_store["temp"],program_store["pulse"],program_store["spo2"])

def day_greetings():
    '''returns Good morning/afternoon/evening based on time of day'''
    hr = datetime.now().hour

    if hr < 12:
        return "Magandang umaga, "
    if hr < 18:
        return "Magandang hapon"
    return "Magandang gabi"


def generate_code() -> int:
    return random.randint(100000, 999999)


class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout
