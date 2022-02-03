import subprocess
from time import sleep

def _start_healthmon():
	healthmon_process = subprocess.run(["lxterminal", "--command='python /home/pi/Desktop/main.py'", "--title='Healthmon'"])
	rc = healthmon_process.returncode

	if rc == 0:
		print("Healthmon launched")
	else:
		print("Can't start Healthmon program")

def _turn_off_healthmons():
	'''Turns off all running Healthmon programs'''
	pidof_process = subprocess.run(["pidof", "healthmon"], capture_output = True)
	pid = pidof_process.stdout.decode().strip()

	if pid != "":
		kill_process = subprocess.run(["killall", "-2", "healthmon"])
		rc = kill_process.returncode

		# Failed to turn off program
		if rc == -1:
			raise Exception("Can't turn off Healthmon program(s)")

def restart_healthmon_program():
	try:
		_turn_off_healthmons()
		sleep(2)
		_start_healthmon()
		sleep(3)

	except Exception as e:
		print (e)
		print("---Failed to restart healthmon program---")

	sleep(2)

