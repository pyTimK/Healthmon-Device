from typing import Dict, List, Optional
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


def _initialize_device_database():
    if not has_internet():
        return

    device_doc = device_doc_ref.get()
    if not device_doc.exists:
        device_doc_ref.set({"name": "", "id": "", "new_name": "", "new_id": "", "confirmed": False, "request_timestamp": get_timestamp()})


    
def set_code_firestore(code: int):
    '''Sets the code online to be entered by the new pairing user'''
    device_authenticate_ref.set({"code": code})


def remove_code_firestore():
    device_authenticate_ref.set({"code": 0})


print_success_write = lambda : print("---Successfully written record to firestore---")
print_failed_write = lambda : print("---Failed to write record to firestore---")

def clear_new_user():
    if not has_internet():
        return
        
    device_doc_ref.update({"new_id": "", "new_name": "", "confirmed": False})


def write_record_firestore(user: Dict, temp: float, pulse: int, spo2: int):
    uid: str = user["id"]

    if uid == "":
        return

    if not has_internet():
        print_failed_write()
        return

    try:
        record_doc_ref = records_collection_ref.document(get_formatted_day()).collection(uid).document(get_formatted_hours())
        record_doc_ref.set({"timestamp": get_timestamp(),"temp": temp, "pulse": pulse, "spo2": spo2})
        print_success_write()
    except:
        print_failed_write()

def toUnformatted(obj: Dict[str, Dict]) -> List[Dict]:
    return list(obj.values())

def get_healthWorkers_doc_ref(id: str):
    return db.collection("users").document(id).collection("associates").document("healthWorkers")

def get_healthWorkers(id: str) -> List[Dict]:
    try:
        healthWorkers_doc_ref = get_healthWorkers_doc_ref(id)
        healthWorkers_doc = healthWorkers_doc_ref.get()
        health_workers_dict = healthWorkers_doc.to_dict()
        health_workers_dict.pop('exists', None)
        return toUnformatted(health_workers_dict)

    except:
        return []

def get_user() -> Dict:
    try:
        device_doc = device_doc_ref.get()
        user = device_doc.to_dict()
        return user

    except:
        return None

_initialize_device_database()


