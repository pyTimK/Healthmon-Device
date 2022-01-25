import subprocess
from typing import Dict, Tuple
from random import randint
from time import sleep
import serial


# if valid readings surpasses 10 counts, then average last 5 valid readings
_surpass_counts = 13
_get_average_count = 7 # Must be less than _surpass_counts

def _is_valid(pulse: int, spo2: int) -> bool:
    return pulse > 40 and spo2 > 70

def read_max30100(program_status: Dict[str, bool]) -> Tuple[int, int]:
	'''Returns pulse and spo2. Returns -1 on both of them on error'''
	try:
		print("DAFUQ")
		ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=5)
		print("waw")
		ser.reset_input_buffer()
		print("waw2")
		valid_readings = []

		while program_status["alive"] and program_status["detecting_hand"] :
			if ser.in_waiting > 0:
				line = ser.readline().decode().rstrip()
				pulse, spo2 = line.split(" ")
				pulse, spo2 = int(pulse), int(spo2)

				print(f"{pulse} {spo2}")
				
				if _is_valid(pulse, spo2):
					valid_readings.append((pulse, spo2))
				
					if len(valid_readings) > _surpass_counts:
						valid_readings = valid_readings[-1*_get_average_count:]
						break
		
		pulse = sum(r[0] for r in valid_readings) // _get_average_count
		spo2 = sum(r[1] for r in valid_readings) // _get_average_count

		return pulse, spo2
	
	except:
		return -1, -1

	#TODO remove after fixing max30100
	#return __random_temporary()



def __random_temporary() -> Tuple[int, int]:
	'''Mocks a max30100 in getting measures'''
	sleep(randint(4, 8))
	pulse = randint(50, 120)
	spo2 = randint(80, 100)
	return pulse, spo2


def _print_results(pulse: int, spo2: int):
	print(f"PULSE: {pulse}\tSPO2:{spo2}")


# TESTING ---------------------
# _program_status = {
# 	"alive": True,
#     "reading": False,
#     "measure_error": False,
#     "show_results": False,
# }
# print(read_max30100(_program_status))
#------------------------------