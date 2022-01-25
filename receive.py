import serial
import time
import sys


class HuaweiModem(object):
    def __init__(self):
        self.open()

    def open(self):
        self.ser = serial.Serial('/dev/ttyS0', 9600, timeout=5)
        self.SendCommand(b'ATZ\r')
        self.SendCommand(b'AT+CMGF=1\r')


    def SendCommand(self,command, getline=True):
        self.ser.write(command)
        data = ''
        if getline:
            data=self.ReadLine()
        return data

    def ReadLine(self):
        data = self.ser.readline()
        print(data)
        return data



    def GetAllSMS(self):
        self.ser.flushInput()
        self.ser.flushOutput()
        command = b'AT+CMGL="REC UNREAD"\r\n'#gets incoming sms that has no>
        print(self.SendCommand(command,getline=True))
        data = self.ser.readall()
        print(data)


h = HuaweiModem()
h.GetAllSMS()
