'''
This Code prints SpO2 and Heart Rate data on console.
Sensor used is MAX30100
HW Raspberry Pi 2B

Sensor Connection to Raspberry Pi
Sensor Vcc - Raspberry Pi 3.3V (pin 1)
Sensor GND - Raspberry Pi GND (pin 9)
Sensor SCL - Raspberry Pi SCL(pin 5)
Sensor SDA - Raspberry Pi SDA(pin 3)

'''
import time
import os
import max30100

mx30 = max30100.MAX30100()
mx30.enable_spo2()

# Generates Moving Average - This will filter data and improve stability of readings
def moving_average(numbers):
    window_size = 4
    i = 0
    # moving_averages = []
    while i < len(numbers) - window_size + 1:
        this_window = numbers[i : i + window_size]
        window_average = sum(this_window) / window_size
        # moving_averages.append(window_average)
        i += 1
    try:
        return int((window_average/100))
    except:
        pass

# If HeartRate is <10 function assumes Fingure Not present and will not show incorrect data
# Also If SpO2 readings goes beyond 100. It will be shown as 100.
def display_filter(moving_average_bpm,moving_average_sp02):
    return moving_average_bpm, moving_average_sp02

    try:
        if(moving_average_bpm<10):
            moving_average_bpm ='NA'
            moving_average_sp02 = 'NA'
        else:
            if(moving_average_sp02>100):
                moving_average_sp02 = 100
        return moving_average_bpm, moving_average_sp02
    except:
        return moving_average_bpm, moving_average_sp02

while 1:
    mx30.read_sensor()
    hb = int(mx30.ir / 100)
    spo2 = int(mx30.red / 100)
    if mx30.ir != mx30.buffer_ir :
        moving_average_bpm = (moving_average(mx30.buffer_ir))
        # print(" MAX30.ir " + str(mx30.ir)) 
        # print(" mx30.buffer_ir " + str(mx30.buffer_ir)) 
        # print("|||||| Avg Pulse :" + str(moving_average_bpm)) 
        # print("|||||| Pulse     :" + str(hb));
    if mx30.red != mx30.buffer_red:
        moving_average_sp02 = (moving_average(mx30.buffer_red))
        # print(" MAX30.red " + str(mx30.red)) 
        # print(" mx30.buffer_red " + str(mx30.buffer_red)) 
        # print("###### Avg SpO2  :" + str(moving_average_sp02)) 
        # print(" ##### SPO2     :" + str(spo2));
    bpm,spo2 = display_filter(moving_average_bpm,moving_average_sp02)
    print(" *******************")
    print(" bpm : "+ str(bpm))
    print(" SpO2: "+ str(spo2))
    print(" -------------------")
    time.sleep(1)
