import concurrent.futures
import contextlib
from threading import Thread
from time import sleep
from typing import Dict
from firestore_helper import device_doc_ref, device_authenticate_ref, clear_new_user, remove_code_firestore, set_code_firestore, get_healthWorkers, get_healthWorkers_doc_ref, toUnformatted, get_user
from funcs import generate_code, HiddenPrints
from file_helper import save_user
from check_internet import has_internet
from copy import deepcopy

_time_expiration = 30 # in seconds

print_success_authenticate = lambda : print("---New user authenticated---")
print_failed_authenticate = lambda : print("---New user authentication failed---")


def _start_countdown(program_status: Dict[str, bool], program_store: Dict):
    '''allows the pairing user to get the code within {_time_expiration} seconds'''
    program_store["confirm_code_sec"] = _time_expiration
    while program_status["alive"] and program_status["is_pairing"] and program_store["confirm_code_sec"] > 0:
        program_store["confirm_code_sec"] -= 1
        sleep(1)


def _start_pairing(new_doc, program_status: Dict[str, bool], program_store: Dict):
    '''Sets the device to pairing mode. During this mode, normal operations of the device are interrupted'''
    if program_status["is_pairing"]:
        return

    code = generate_code()
    set_code_firestore(code)
    program_store["confirm_code"] = code
    program_status["is_pairing"] = True
    _start_countdown(program_status, program_store)
        
    if program_store["confirm_code_sec"] == 0 and not program_status["paired_new_user"]:
        program_status["is_pairing"] = False
        clear_new_user()
    
    remove_code_firestore()



def _show_paired(program_status: Dict[str, bool]):
        '''briefly shows in the LCD that a new user has just been paired'''
        device_doc_ref.update({"confirmed": False})
        program_status["paired_new_user"] = True
        sleep(3)
        program_status["paired_new_user"] = False


def _confirm_paired(new_doc, program_status: Dict[str, bool], program_store: Dict):
    if not has_internet():
        return

    '''briefly shows that a new user has been paired and continues to its normal operation'''
    program_status["is_pairing"] = False
    program_store["user"] = new_doc
    
    # Requires restart of device to enable realtime listener to health workers of new paired user
    # program_store["user"]["healthWorkers"] = get_healthWorkers(program_store["user"]["id"])
    # save_user(program_store["user"])

    # Does not require restart to enable realtime listener
    _refresh_hw_listener(program_status, program_store)

    _show_paired(program_status)


def healthWorkersListener(program_status: Dict[str, bool], program_store: Dict):
    if not has_internet():
        return

    user = program_store["user"]
    
    if user is None or user["id"] is None or user["id"] == "":
        return
        
    def healthWorkers_doc_on_snapshot(doc_snapshot, changes, read_time):
        '''The callback function that executes whenever there is a new update in any of the health workers connected with the device'''
        print("healthWorkers snap!")
        try:
            health_workers_dict = doc_snapshot[0].to_dict()
            health_workers_dict.pop('exists', None)
            health_workers = toUnformatted(health_workers_dict)
            if user is not None:
                user["healthWorkers"] = health_workers
                save_user(user)
        
        except:
            print("Failed to get associated health workers")
    
    try:
        healthWorkers_doc_watch = get_healthWorkers_doc_ref(user["id"]).on_snapshot(healthWorkers_doc_on_snapshot)
    except:
        print("No health workers connected with this device")

    return healthWorkers_doc_watch

def deviceListener(program_status: Dict[str, bool], program_store: Dict):
    def device_doc_on_snapshot(doc_snapshot, changes, read_time):
        '''The callback function that executes whenever there is a new update to the firestore document associated with this device'''
        print("device snap!")
        try:
            new_doc = doc_snapshot[0].to_dict()
            if new_doc["confirmed"]:    # The user who wants to pair entered the right code
                _confirm_paired(new_doc, program_status, program_store)
                return
            
            if new_doc["id"] == "" and new_doc["new_id"] == "": # The user unpaired this device
                new_doc["healthWorkers"] = []
                save_user(new_doc)
                program_store["user"] = new_doc
                return
            
            if new_doc["new_id"] == "": # Paired user updated their personal details
                updated_user = deepcopy(new_doc)
                if "healthWorkers" in program_store["user"]:
                    updated_user["healthWorkers"] = deepcopy(program_store["user"]["healthWorkers"])

                program_store["user"] = updated_user
                save_user(updated_user)
                return
            
            # A new pair request to this device is made
            pairing_thread = Thread(target=_start_pairing, args=(new_doc, program_status, program_store))
            pairing_thread.start()
        
        except Exception as e:
            print("Failed to get user info from firestore:")
            print(f"WHAT: {str(e)}")

    try:
        device_doc_watch = device_doc_ref.on_snapshot(device_doc_on_snapshot)
    except:
        print("This device is not connected to firestore yet")

    return device_doc_watch

def _refresh_device_listener(program_status: Dict[str, bool], program_store: Dict):
    try:
        clear_new_user()
    except Exception as e:
        print("WARNING: Failed to clear new_user in device doc in firestore")
        print(e)
    
    try:
        if program_store["device_listener_unsub"] is not None:
            #TODO remove when google core api has been updated and 'Background did not exit' does not print in stderr anymore
            with contextlib.redirect_stderr(None):
                program_store["device_listener_unsub"].unsubscribe()

    except Exception as e:
        print("WARNING: Problem encountered while unsubscribing device:")
        print(e)

    try:
        program_store["device_listener_unsub"] =  deviceListener(program_status, program_store)
    except Exception as e:
        print("WARNING: Problem listening to device")
        print(e)



def _refresh_hw_listener(program_status: Dict[str, bool], program_store: Dict):
    try:
        if program_store["hw_listener_unsub"] is not None:
            #TODO remove when google core api has been updated and 'Background did not exit' does not print in stderr anymore
            with contextlib.redirect_stderr(None):
                program_store["hw_listener_unsub"].unsubscribe()

    except Exception as e:
        print("WARNING: Problem encountered while unsubscribing to healthWorkers:")
        print(e)
    
    try:
        program_store["hw_listener_unsub"] =  healthWorkersListener(program_status, program_store)
    except Exception as e:
        print("WARNING: Problem listening to healthWorkers")
        print(e)



def user_authenticator(program_status: Dict[str, bool], program_store: Dict):
    '''thread that listens to new updates regarding the user connected to this device and if a new user wants to pair with this device
    Returns '''

    # Clear new_fields on device document in firestore


    # NO NEED SINCE SNAPSHOT LISTENERS ALREADY UPDATES ON STARTUP ---------
    # # Get paired user info on program startup
    # firestore_user = get_user()
    # if firestore_user:
    #     program_store["user"] = firestore_user
    
    # # Get health workers' info on program startup
    # if program_store["user"] and program_store["user"]["id"]:
    #     program_store["user"]["healthWorkers"] = get_healthWorkers(program_store["user"]["id"])
    #     save_user(program_store["user"])
    # ---------------------------------------------------------------------


    _refresh_device_listener(program_status, program_store)
    _refresh_hw_listener(program_status, program_store)
    