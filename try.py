from gpiozero import LED
from time import sleep
from signal import pause



led = LED(23)


while True:
	led.on()
	sleep(1)
	led.off()
	sleep(1)
