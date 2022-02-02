import concurrent.futures
from threading import Thread
from time import sleep
from typing import Dict
from firestore_helper import device_doc_ref, device_authenticate_ref, clear_new_user, get_healthWorkers, get_healthWorkers_doc_ref, toUnformatted, get_user
from funcs import generate_code
from file_helper import save_user

_time_expiration = 30 # in seconds

print_success_authenticate = lambda : print("---New user authenticated---")
print_failed_authenticate = lambda : print("---New user authentication failed---")


def _start_countdown(program_status: Dict[str, bool], program_store: Dict):
    '''allows the pairing user to get the code within {_time_expiration} seconds'''
    program_store["confirm_code_sec"] = _time_expiration
    while program_status["alive"] and program_status["is_pairing"] and program_store["confirm_code_sec"] > 0:
        program_store["confirm_code_sec"] -= 1
        sleep(1)
    

def _show_paired(program_status: Dict[str, bool]):
    '''briefly shows in the LCD that a new user has just been paired'''
    device_doc_ref.update({"confirmed": False})
    program_status["paired_new_user"] = True
    sleep(3)
    program_status["paired_new_user"] = False





def _start_pairing(new_doc, program_status: Dict[str, bool], program_store: Dict):
    '''Sets the device to pairing mode. During this mode, normal operations of the device are interrupted'''
    code = generate_code()
    program_store["confirm_code"] = code
    program_status["is_pairing"] = True
    device_authenticate_ref.set({"code": code})
    _start_countdown(program_status, program_store)
        
    if program_store["confirm_code_sec"] == 0 and not program_status["paired_new_user"]:
        program_status["is_pairing"] = False
        clear_new_user()



def healthWorkersListener(program_store: Dict):
    def healthWorkers_doc_on_snapshot(doc_snapshot, changes, read_time):
        print("healthWorkers snap!")
        '''The callback function that executes whenever there is a new update in any of the health workers connected with the device'''
        for doc in doc_snapshot:
            health_workers_dict = doc.to_dict()
            health_workers_dict.pop('exists', None)
            health_workers = toUnformatted(health_workers_dict)

            if program_store["user"] is not None:
                program_store["user"]["healthWorkers"] = health_workers
                save_user(program_store["user"])
        
    healthWorkers_doc_watch = get_healthWorkers_doc_ref(program_store["user"]["id"]).on_snapshot(healthWorkers_doc_on_snapshot)
    return healthWorkers_doc_watch

def deviceListener(program_status: Dict[str, bool], program_store: Dict):

    def confirm_paired(new_doc):
        '''briefly shows that a new user has been paired and continues to its normal operation'''
        program_status["is_pairing"] = False
        program_store["user"] = new_doc
        
        # Requires restart of device to enable realtime listener to health workers of new paired user
        # program_store["user"]["healthWorkers"] = get_healthWorkers(program_store["user"]["id"])
        # save_user(program_store["user"])

        # Does not require restart to enable realtime listener
        if program_store["hw_listener_unsub"] is not None:
            program_store["hw_listener_unsub"].unsubscribe()
        
        program_store["hw_listener_unsub"] = healthWorkersListener(program_store)

        _show_paired(program_status)



    def device_doc_on_snapshot(doc_snapshot, changes, read_time):
        print("device snap!")
        '''The callback function that executes whenever there is a new update to the firestore document associated with this device'''
        for doc in doc_snapshot:
            new_doc = doc.to_dict()

            if new_doc["confirmed"]:    # The user who wants to pair entered the right code
                confirm_paired(new_doc)
                return
            
            if new_doc["id"] == "" and new_doc["new_id"] == "": # The user unpaired this device
                new_doc["healthWorkers"] = []
                save_user(new_doc)
                program_store["user"] = new_doc
                return
            
            

            if new_doc["new_id"] == "": # Paired user updated their personal details
                new_doc["healthWorkers"] = program_store["user"]["healthWorkers"]
                program_store["user"] = new_doc
                save_user(new_doc)
                return
            
            # A new pair request to this device is made
            pairing_thread = Thread(target=_start_pairing, args=(new_doc, program_status, program_store))
            pairing_thread.start()
            

    device_doc_watch = device_doc_ref.on_snapshot(device_doc_on_snapshot)
    return device_doc_watch



def user_authenticator(program_status: Dict[str, bool], program_store: Dict):
    '''thread that listens to new updates regarding the user connected to this device and if a new user wants to pair with this device
    Returns '''

    # Clear new_fields on device document in firestore
    clear_new_user()


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
    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     thread_healthWorkers = executor.submit(healthWorkersListener, program_store)
    #     thread_devices = executor.submit(deviceListener, program_status, program_store)

    #     program_store["hw_listener_unsub"] = thread_healthWorkers.result(60)
    #     program_store["device_listener_unsub"] = thread_devices.result(60)

    program_store["hw_listener_unsub"] = healthWorkersListener(program_store)
    program_store["device_listener_unsub"] = deviceListener(program_status, program_store)
    