from ultrasonic_sensor import wait_hand_detect
import concurrent.futures

# wait_hand_detect({"alive": True}, 1, 0.2)

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.submit(wait_hand_detect, {"alive": True}, 1, 0.2)
    