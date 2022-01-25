import json
from typing import Dict

paired_user_loc = "/home/pi/Desktop/paired_user.txt"

def save_user(user: Dict):
    try:
        with open(paired_user_loc, 'w') as f:
            f.write(json.dumps(user, default=str))

    except Exception as e:
        print(f"Error saving user: {e}")


def get_user() -> Dict:
    try:
        with open(paired_user_loc, "r") as f:
            read_data = f.read()
            return json.loads(read_data)
    except:
        return {"name": "", "healthWorkers": [], "id": ""}