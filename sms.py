from time import sleep
from datetime import datetime
from funcs import normal_temp, normal_pulse, normal_spo2, day_greetings
from typing import Dict, List
import serial


normal_result_mapping = {
    -1: "Below Normal",
    0: "Normal",
    1: "Above Normal",
}


def _generate_health_worker_sms(to_name: str, program_store: Dict) -> str:
    name: str = program_store["user"]["name"]
    temp, pulse, spo2 = program_store["temp"], program_store["pulse"], program_store["spo2"]

    return f'''
{day_greetings()} {to_name},
{name.title()} needs your attention.

---TEMPERATURE---
{temp:.1f}C
({normal_result_mapping[normal_temp(temp)]})

---HEART RATE---
{pulse}bpm
({normal_result_mapping[normal_pulse(pulse)]})

---SpO2---
{spo2}%
({normal_result_mapping[normal_spo2(spo2)]})

This reading is genererated on {datetime.now().ctime()}
'''


def health_worker_sms(program_store: Dict):
    user: Dict = program_store["user"]
    health_workers: List[Dict] = user["healthWorkers"]
    for health_worker in health_workers:
        send_SMS(health_worker["number"], _generate_health_worker_sms(
            health_worker["name"], program_store))
        sleep(2)


def send_SMS(recipient: str, message: str):
    phone = serial.Serial("/dev/ttyS0",  9600, timeout=5)
    tries = 6
    for i in range(tries):
        try:
            sleep(0.5)
            _write(phone, 'ATZ')
            _write(phone, 'AT+CMGF=1')
            _write(phone, f'AT+CMGS="{recipient}"')
            _write(phone, message, cr=False)
            phone.write(bytes([26]))
            sleep(0.5)

            reply = phone.read_all().decode()
            if len(reply) == 0:
                if i == tries - 1:
                    print("Failed sending SMS")

                sleep(1)
                continue

            # print(reply)
            print("Successfully sent SMS")
        except:
            print("Failed sending SMS")

        break

    phone.close()


def treay():
    # send_SMS("09683879596", "wa")
    for i in range(3):
        send_SMS("09683879596", str(i))
        sleep(1)


def _write(phone: serial.Serial, s: str, cr=True):
    if cr:
        s = f"{s}\r"

    phone.write(s.encode())
    sleep(0.5)


# # TESTING ---------------------
# _program_store = {
#     "user":{"healthWorkers": [{"number": "09683879596", "name": "Dr. Pia Pia Belen"},{"name": "Tim Llanto", "number": "09683879596"}], "name": "Gord Good", "id": "HJSxutwXcDf8eMbHQ9thrUvEYBx2"},
#     "temp": 37.3673,
#     "pulse": 190,
#     "spo2": 60,
# }
#send_SMS("09683879596", "wa")
# health_worker_sms(_program_store)
# # treay()
# #------------------------------
