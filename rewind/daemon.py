#!/usr/bin/env python3
import os
import datetime
import signal
import time
import obsws_python as obs
import subprocess
import logging
import json

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rewind.paths import load_config
from rewind.core import mark, marker_exists, remove_marker
from rewind.state import add_file_to_state, create_state_file_if_needed, cleanup_state_files

INTERVAL = 10
running = True
logging.getLogger("obsws_python").setLevel(logging.CRITICAL)

def open_obs():
    kill_command =  subprocess.Popen(["pkill", "obs"])
    kill_command.wait()

    if os.path.exists(os.path.expanduser("~/.config/obs-studio/.sentinel")):
        print("Removing existing .sentinel directory")
        subprocess.Popen(["rm", "-rf", os.path.expanduser("~/.config/obs-studio/.sentinel")])

    subprocess.Popen(["obs", "--minimize-to-tray"])

def open_obs_connection(host: str, port: int, password: str) -> obs.ReqClient | None:
    con = None
    max_attempts = 10
    init_sleep = 1

    for _ in range(max_attempts):
        try:
            con = obs.ReqClient(host=host, port=port, password=password)
        except ConnectionRefusedError:
            print("OBS WebSocket not ready, retrying...")

        if con:
            return con

        time.sleep(init_sleep)
        init_sleep *= 2
    return None

def start_recording(con: obs.ReqClient) -> None:
    con.start_record()
    print("Started recording")

def stop_recording(con: obs.ReqClient) -> None:
    con.stop_record()
    print("Stopped recording")

def create_initial_marker() -> None:
    if marker_exists("daemon-start"):
        remove_marker("daemon-start")

    mark("daemon-start")

def cleanup_physical_files(directory: str, max_age_seconds: int) -> None:
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_age = datetime.datetime.now().timestamp() - os.path.getmtime(file_path)
            if file_age > max_age_seconds and filename.endswith(".ts"):
                os.remove(file_path)
                print(f"Removed old file: {file_path}")

def cleanup_markers(max_age_seconds: float) -> None:
    markers_file = os.path.join(os.path.dirname(__file__), "markers.json")
    if not os.path.exists(markers_file):
        return

    with open(markers_file, "r") as f:
        markers = json.load(f)

    current_time = datetime.datetime.now().timestamp()
    markers = [m for m in markers if current_time - m['timestamp'] <= max_age_seconds]

    with open(markers_file, "w") as f:
        json.dump(markers, f, indent=4)

def handle_shutdown(signum, frame):
    global running
    running = False

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".ts"):
            add_file_to_state(event.src_path)
            print(f"Added new file to state: {event.src_path}")

def main() -> None:
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

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
        stop_recording(con)
        con.disconnect()
        print("Daemon stopped")

if __name__ == "__main__":
    main()