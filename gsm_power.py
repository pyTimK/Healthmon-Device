from time import sleep
from signal import  pause
from gpiozero import LED
from gpiozero.pins.pigpio import PiGPIOFactory

f = PiGPIOFactory()
gsm_power_pin = 13
gsm_power = LED(13, pin_factory = f)

def turn_on_gsm():
	while True:
		gsm_power.off()
		sleep(2)
		gsm_power.on()
		sleep(2)
		gsm_power.off()



def turn_off_gsm():
	gsm_power.on()
	sleep(3)
	gsm_power.off()


turn_on_gsm()
