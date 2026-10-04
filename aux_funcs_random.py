import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
continue_file_path = os.path.join(BASE_DIR, '___CONTINUE.txt')
locked_files_path = os.path.join(BASE_DIR, '___RED_LIGHT.txt')


def get_current_time_str():
    import datetime
    now = datetime.now()
    formatted_time = now.strftime("%H:%M:%S")
    return formatted_time


def get_current_time_str_print():
    t = str(get_current_time_str())
    return t + " - "


def checkFileExistance(path):
    import os
    if os.path.isfile(path):
        return True
    else:
        return False


def getPickleData(path):

    if not checkFileExistance(path):
        return None
    else:
        import pickle
        with open(path, 'rb') as file:
            received_data = pickle.load(file)

        return received_data


def savePickleData(path, data_to_save):
    import pickle
    with open(path, 'wb') as file:
        pickle.dump(data_to_save, file)
    return


def get_current_time_str():
    from datetime import datetime
    current_time = datetime.now().strftime('%H:%M:%S')
    return current_time


def check_locked_files_file(locked_files_path=locked_files_path):
    return checkFileExistance(locked_files_path)


def check_continue_file(continue_path=continue_file_path):
    return checkFileExistance(continue_path)


def create_continue_file(continue_path=continue_file_path):
    if not check_continue_file():
        continue_file = open(continue_path, 'w')
        continue_file.close()
    return


def create_locked_files_file(locked_files_path=locked_files_path):
    if not check_locked_files_file():
        red_light_file = open(locked_files_path, 'w')
        red_light_file.close()
    return


def delete_locked_files_file(locked_files_path=locked_files_path):
    import os
    if not check_locked_files_file():
        return
    else:
        os.remove(locked_files_path)


def wait_for_green_light(locked_files_path=locked_files_path):
    import random

    while check_locked_files_file(locked_files_path):
        time.sleep(2*random.random())

    return

def timeout(timeout):
    from threading import Thread
    import functools

    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (func.__name__, timeout))]
            def newFunc():
                try:
                    res[0] = func(*args, **kwargs)
                except Exception as e:
                    res[0] = e
            t = Thread(target=newFunc)
            t.daemon = True
            try:
                t.start()
                t.join(timeout)
            except Exception as je:
                print ('error starting thread')
                raise je
            ret = res[0]
            if isinstance(ret, BaseException):
                raise ret
            return ret
        return wrapper
    return deco


def terminate_process_by_name(process_name, DEBUG=False):
    import psutil
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            pid = process.info['pid']
            try:
                p = psutil.Process(pid)
                p.terminate()  # You can use p.kill() for forceful termination
                if DEBUG:
                    print(f"Process {process_name} (PID {pid}) terminated.")
            except psutil.NoSuchProcess:
                if DEBUG:
                    print(f"Process {process_name} (PID {pid}) not found.")
            except psutil.AccessDenied:
                if DEBUG:
                    print(f"Access denied to terminate process {process_name} (PID {pid}).")

