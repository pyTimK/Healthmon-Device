import board
import busio as io
import adafruit_mlx90614
from time import sleep

#Note that mlx90614 has an error rate of ±5°C

i2c = io.I2C(board.SCL, board.SDA, frequency=10000)
mlx = adafruit_mlx90614.MLX90614(i2c)

temp_calibrate = 2.0 # Adjusted for wrist measurements



samples_len = 30
samples = [0] * samples_len

def read_temp() -> float:
    '''Returns temperature read on MLX90614 module'''
    for i in range(samples_len):
        samples[i] = mlx.object_temperature + temp_calibrate
        sleep(0.1)

    temp = sum(samples) / samples_len
    #print(f"TEMP: {temp}")
    return temp


#read_temp()