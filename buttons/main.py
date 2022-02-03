import concurrent.futures
from setproctitle import setproctitle
from signal import pause
from gpiozero import Button, LED


from restart_healthmon import restart_healthmon_program

restart_button = Button(13)
lcd_backlight_button = Button(26)

try:
	setproctitle("buttons")
except:
	print("can't change process name of restart button")



restart_button.when_pressed = restart_healthmon_program
pause()