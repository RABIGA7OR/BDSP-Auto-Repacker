from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
import logging
import os
import time
import shutil
import json
import threading
import datetime
import subprocess
import time

REPACK_TIMEOUT = 10
folders = ["AssetFolder", "scripts"] # Folders to scan for changes
sources = [
    "bin/ev_script",
    "EditedAssets/battle",
    "EditedAssets/battle_masterdatas",
    "EditedAssets/common_msbt",
    "EditedAssets/contest_masterdatas",
    "EditedAssets/english",
    "EditedAssets/gamesettings",
    "EditedAssets/masterdatas",
    "EditedAssets/personal_masterdatas",
    "EditedAssets/shaders",
    "EditedAssets/ugdata",
    "EditedAssets/uimasterdatas"
]
destinations = [
    "romfs/Data/StreamingAssets/AssetAssistant/Dpr/ev_script",
    "romfs/Data/StreamingAssets/AssetAssistant/Dpr/scenes/battle",
    "romfs/Data/StreamingAssets/AssetAssistant/Battle/battle_masterdatas",
    "romfs/Data/StreamingAssets/AssetAssistant/Message/common_msbt",
    "romfs/Data/StreamingAssets/AssetAssistant/Contest/md/contest_masterdatas",
    "romfs/Data/StreamingAssets/AssetAssistant/Message/english",
    "romfs/Data/StreamingAssets/AssetAssistant/Dpr/scriptableobjects/gamesettings",
    "romfs/Data/StreamingAssets/AssetAssistant/Dpr/masterdatas",
    "romfs/Data/StreamingAssets/AssetAssistant/Pml/personal_masterdatas",
    "romfs/Data/StreamingAssets/AssetAssistant/Dpr/shaders",
    "romfs/Data/StreamingAssets/AssetAssistant/UnderGround/data/ugdata",
    "romfs/Data/StreamingAssets/AssetAssistant/UIs/masterdatas/uimasterdatas"
]
config_filename = "auto_repacker_config.json"
observers = []
config = None
queue_trigger_datetime = None # When to trigger the next thread, if not running already
repacking_active = False # If the thread is currently repacking

def load_config():
    global config_filename, config
    try:
        with open(os.path.join(os.getcwd(), config_filename), "r") as file:
            config = json.load(file)
        logging.info("Config file loaded")
        logging.info(config)
    except FileNotFoundError:
        config_setup()
        load_config()

def config_setup():
    global config_filename
    config = {}
    print("Looks like there's no config file.")
    current_dir = os.getcwd()
    
    user_input = ""
    while not os.path.exists(user_input):
        user_input = input(f"Please enter the project directory (Enter for '{current_dir}') >>> ")
        if user_input == "":
            user_input = current_dir
    config["project_directory"] = os.path.abspath(user_input)
    
    user_input = ""
    while not os.path.exists(user_input):
        user_input = input(f"Please enter the mod directory (Enter for '{current_dir}') >>> ")
        if user_input == "":
            user_input = current_dir
    config["mod_directory"] = os.path.abspath(user_input)
    
    with open(os.path.join(os.getcwd(), config_filename), "w") as file:
        json.dump(config, file, indent=4)
    
    logging.info("Config file created")

def file_change(event):
    global queue_trigger_datetime, repacking_active, REPACK_TIMEOUT
    
    last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(event.src_path))
    modified_recently = datetime.datetime.now() - datetime.timedelta(0, 10)
    # Check if the file was actually modified. This event seems to trigger if just some metadata changes too
    if last_modified < modified_recently:
        return
    
    # Ignore filechanges to english asset files if repacking is active - these might be modified by macros
    if repacking_active and os.path.basename(event.src_path).startswith("english"):
        return
    
    queue_trigger_datetime = datetime.datetime.now() + datetime.timedelta(0, REPACK_TIMEOUT)
    logging.info(f"Next repack scheduled for {queue_trigger_datetime.strftime('%H:%M:%S')}")

def file_change_generic(event):
    global queue_trigger_datetime
    
    queue_trigger_datetime = datetime.datetime.now() + datetime.timedelta(0, REPACK_TIMEOUT)
    logging.info(f"Next repack scheduled for {queue_trigger_datetime.strftime('%H:%M:%S')}")

def idle():
    global queue_trigger_datetime, repacking_active
    
    if queue_trigger_datetime is not None and queue_trigger_datetime <= datetime.datetime.now() and not repacking_active:
        repacking_active = True
        queue_trigger_datetime = None
        thread = threading.Thread(target=repack)
        thread.start()
        logging.info("Repacking has started")

def repack():
    global subprocess, repacking_active, queue_trigger_datetime
    
    # Repack scripts first in case macros edit some Asset files
    if os.path.exists("src/ev_as.py"):
        subprocess.call("python src/ev_as.py", stdout=subprocess.DEVNULL)
    elif os.path.exists("src/ev_as.exe"):
        subprocess.call("src/ev_as.exe", stdout=subprocess.DEVNULL)
    else:
        raise FileNotFoundError("No ev_as.py or ev_as.exe found!")

    if queue_trigger_datetime is not None:
        logging.info("Finish repack early")
        repacking_active = False
        return
    
    if os.path.exists("Repack.py"):
        sp = subprocess.Popen("python Repack.py", stdin=subprocess.PIPE, text=True, stdout=subprocess.DEVNULL)
        sp.communicate("\n")
    elif os.path.exists("Repack.exe"):
        sp = subprocess.Popen("Repack.exe", stdin=subprocess.PIPE, text=True, stdout=subprocess.DEVNULL)
        sp.communicate("\n")
    else:
        raise FileNotFoundError("No Repack.py or Repack.exe found!")
    
    logging.info("Repacking has finished")
    
    if queue_trigger_datetime is not None:
        logging.info("Skip updating the mod folder")
        repacking_active = False
        return
    
    update_mod_folder()
    repacking_active = False

def update_mod_folder():
    global config

    for src, dst in zip(sources, destinations):
        src = os.path.join(config["project_directory"], src)
        dst = os.path.join(config["mod_directory"], dst)
        if os.path.exists(src):
            shutil.copy2(src, dst)
    
    logging.info("Mod folder has been updated")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    load_config()
    
    os.chdir(config["project_directory"])
    
    event_handler = LoggingEventHandler()
    event_handler.on_modified = file_change
    event_handler.on_created = file_change_generic
    event_handler.on_moved = file_change_generic
    event_handler.on_deleted = file_change_generic
    
    for folder in folders:
        observer = Observer()
        observer.schedule(event_handler, folder, recursive=True)
        try:
            observer.start()
        except FileNotFoundError:
            print("At least one of these folders are missing:", folders)
            exit()
        observers.append(observer)

    try:
        while True:
            idle()
            time.sleep(1)
    except KeyboardInterrupt:
        map(lambda o: o.stop(), observers)
    map(lambda o: o.join(), observers)
