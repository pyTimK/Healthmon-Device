from typing import Dict, Optional
import firebase_admin
import os
from firebase_admin import credentials, firestore
from funcs import get_formatted_day, get_formatted_hours, get_timestamp, print_user
from file_helper import save_user
from check_internet import has_internet

device_id = "healthmonmikee1"
cred = credentials.Certificate(os.environ.get("FIRESTORE_CERTIFICATE"))
firebase_admin.initialize_app(cred)
db = firestore.client()



device_doc_ref = db.collection('devices').document(device_id)
device_authenticate_ref = db.collection('authenticate').document(device_id)
records_collection_ref = db.collection('records')


print_success_write = lambda : print("---Successfully written record to firestore---")
print_failed_write = lambda : print("---Failed to write record to firestore---")

def write_record_firestore(user: Dict, temp: float, pulse: int, spo2: int):
    uid: str = user["id"]
    name: str = user["name"]

    if uid == "":
        return

    print(user)
    if not has_internet():
        print_failed_write()
        return

    try:
        record_doc_ref = records_collection_ref.document(get_formatted_day()).collection(uid).document(get_formatted_hours())
        record_doc_ref.set({"timestamp": get_timestamp(), "name": name, "temp": temp, "pulse": pulse, "spo2": spo2})
        print_success_write()
    except:
        print_failed_write()

