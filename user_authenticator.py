from threading import Thread
from time import sleep
from typing import Dict
from firestore_helper import device_doc_ref, device_authenticate_ref
from funcs import generate_code
from file_helper import save_user

_time_expiration = 20 

print_success_authenticate = lambda : print("---New user authenticated---")
print_failed_authenticate = lambda : print("---New user authentication failed---")


def _start_countdown(program_status: Dict[str, bool], program_store: Dict):
    program_store["confirm_code_sec"] = _time_expiration
    while program_status["alive"] and program_status["is_pairing"] and program_store["confirm_code_sec"] > 0:
        program_store["confirm_code_sec"] -= 1
        sleep(1)
    

def _show_paired(program_status: Dict[str, bool]):
    device_doc_ref.update({"confirmed": False})
    program_status["paired_new_user"] = True
    sleep(3)
    program_status["paired_new_user"] = False


def _clear_new_user():
    device_doc_ref.update({"new_id": "", "new_name": "", "new_healthWorkers": [], "confirmed": False})


def _start_pairing(new_doc, program_status: Dict[str, bool], program_store: Dict):
        code = generate_code()
        program_store["confirm_code"] = code
        program_store["confirm_code_sec"] = 20
        program_status["is_pairing"] = True
        device_authenticate_ref.set({"code": code})
        _start_countdown(program_status, program_store)
        
        if program_store["confirm_code_sec"] == 0 and not program_status["paired_new_user"]:
            program_status["is_pairing"] = False
            _clear_new_user()

def user_authenticator(program_status: Dict[str, bool], program_store: Dict):

    def confirm_paired(new_doc):
        program_status["is_pairing"] = False
        save_user(new_doc)
        if new_doc is not None:
            program_store["user"] = new_doc
        _show_paired(program_status)


    # Create a callback on_snapshot function to capture changes
    def device_doc_on_snapshot(doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            new_doc = doc.to_dict()
            # print(new_doc)
            if new_doc["confirmed"]:
                confirm_paired(new_doc)
                return
            
            if new_doc["id"] == "":
                save_user(new_doc)
                program_store["user"] = new_doc

            if new_doc["new_id"] == "":
                return
                
            pairing_thread = Thread(target=_start_pairing, args=(new_doc, program_status, program_store))
            pairing_thread.start()
            

    # Watch the document
    doc_watch = device_doc_ref.on_snapshot(device_doc_on_snapshot)





