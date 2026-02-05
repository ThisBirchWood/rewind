#!/usr/bin/env python3
import os
import datetime
import time
import obsws_python as obs
import subprocess
import logging
import json
import shutil
import signal

from threading import Lock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rewind.paths import load_config
from rewind.core import mark, marker_exists, remove_marker
from rewind.state import add_file_to_state, create_state_file_if_needed, cleanup_state_files

running = True

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s")
logging.getLogger("obsws_python").setLevel(logging.CRITICAL)

INTERVAL = 10
SENTINEL_FILE = os.path.expanduser("~/.config/obs-studio/.sentinel")
OBS_MAX_RETRIES = 10

seen_files = set()
seen_lock = Lock()

def shutdown(signum, frame):
    global running
    logger.info(f"Received signal {signum}, shutting down cleanly")
    running = False

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

def open_obs():
    kill_command = subprocess.run(['pkill', 'obs'])
    if kill_command.returncode not in [0, 1]:
        raise SystemError("Could not kill existing OBS instance")

    if os.path.exists(SENTINEL_FILE):
        try:
            shutil.rmtree(SENTINEL_FILE)
            logger.info("Removed existing OBS .sentinel directory")
        except Exception as e:
            logger.error(f"Could not delete OBS .sentinel directory: {e}")

    # Using and not checking OBS since it needs to be non-blocking
    subprocess.Popen(["obs", "--minimize-to-tray"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def open_obs_connection(host: str, port: int, password: str) -> obs.ReqClient:
    con = None
    init_sleep = 1

    for _ in range(OBS_MAX_RETRIES):
        try:
            con = obs.ReqClient(host=host, port=port, password=password)
        except ConnectionRefusedError:
            logger.info("OBS WebSocket not ready, retrying...")

        if con:
            logger.info(f"Successfully connected to OBS at {host}:{port}")
            return con

        time.sleep(init_sleep)
        init_sleep *= 2
    
    raise RuntimeError("Could not connect to OBS. Either websocket has not been setup or OBS crashed")

def start_recording(con: obs.ReqClient) -> None:
    con.start_record()
    logger.info("Started recording")

def stop_recording(con: obs.ReqClient) -> None:
    con.stop_record()
    logger.info("Stopped recording")

def create_initial_marker() -> None:
    if marker_exists("daemon-start"):
        remove_marker("daemon-start")

    mark("daemon-start")
    logger.info("Created daemon-start marker")

def cleanup_physical_files(directory: str, max_age_seconds: int) -> None:
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_age = datetime.datetime.now().timestamp() - os.path.getmtime(file_path)
            if file_age > max_age_seconds and filename.endswith(".ts"):
                os.remove(file_path)
                logger.info(f"Removed old file: {file_path}")

def cleanup_markers(max_age_seconds: float) -> None:
    markers_file = os.path.join(os.path.dirname(__file__), "markers.json")
    if not os.path.exists(markers_file):
        return

    with open(markers_file, "r") as f:
        markers = json.load(f)

    current_time = datetime.datetime.now().timestamp()
    new_markers = [m for m in markers if current_time - m['timestamp'] <= max_age_seconds]

    with open(markers_file, "w") as f:
        json.dump(new_markers, f, indent=4)

    if new_markers != markers:
        logger.info(f"Cleaning up {len(markers)-len(new_markers)} markers")

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".ts"):
            return
        
        with seen_lock:
            if event.src_path in seen_files:
                return
            seen_files.add(event.src_path)
        
        add_file_to_state(event.src_path)
        logger.info(f"Added new file to state: {event.src_path}")

def main() -> None:
    open_obs()
    config = load_config()
    con = open_obs_connection(config["obs"]["host"], config["obs"]["port"], config["obs"]["password"])

    recording_dir = con.get_record_directory().record_directory
    start_recording(con)

    create_state_file_if_needed()
    create_initial_marker()

    try:
        event_handler = Handler()
        observer = Observer()
        observer.schedule(event_handler, path=recording_dir, recursive=False)
        observer.start()

        while running:
            cleanup_physical_files(recording_dir, config["record"]["max_record_time"])
            cleanup_state_files()
            cleanup_markers(config["record"]["max_record_time"])
            time.sleep(INTERVAL)
    finally:
        if observer:
            observer.stop()
            observer.join()

        stop_recording(con)
        con.disconnect()
        logger.info("Daemon stopped")

if __name__ == "__main__":
    main()