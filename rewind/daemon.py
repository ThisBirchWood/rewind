#!/usr/bin/env python3
import os
import datetime
import signal
import time
import obsws_python as obs
import subprocess

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rewind.paths import load_state, write_state, load_config

INTERVAL = 10
running = True

def open_obs():
    subprocess.Popen(["obs", "--minimize-to-tray"])

def open_obs_connection(host: str, port: int, password: str) -> obs.ReqClient | None:
    try:
        con = obs.ReqClient(host=host, port=port, password=password)
        return con
    except ConnectionRefusedError:
        print("Could not connect to OBS. Is it running and is the WebSocket server enabled?")
        return None

def start_recording(con: obs.ReqClient) -> None:
    con.start_record()
    print("Started recording")

def stop_recording(con: obs.ReqClient) -> None:
    con.stop_record()
    print("Stopped recording")

def cleanup_old_files(directory: str, max_age_seconds: int) -> None:
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_age = datetime.datetime.now().timestamp() - os.path.getmtime(file_path)
            if file_age > max_age_seconds and filename.endswith(".ts"):
                os.remove(file_path)
                print(f"Removed old file: {file_path}")

def create_state_file() -> None:
    state = {"files": []}
    write_state(state)

def add_file_to_state(file_path: str) -> None:
    state = load_state()
    files = state.get("files", [])

    if files and len(files) > 0:
        last_file = files[-1]
        last_file["e_timestamp"] = datetime.datetime.now().timestamp()

    files.append({
        "path": file_path,
        "timestamp": datetime.datetime.now().timestamp(),
    })

    state["files"] = files
    write_state(state)

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
    time.sleep(5)

    config = load_config()

    con = None
    for _ in range(10):
        con = open_obs_connection(config["obs"]["host"], config["obs"]["port"], config["obs"]["password"])
        if con is not None:
            break
        time.sleep(2)

    recording_dir = con.get_record_directory().record_directory
    start_recording(con)
    create_state_file()

    try:
        event_handler = Handler()
        observer = Observer()
        observer.schedule(event_handler, path=recording_dir, recursive=False)
        observer.start()

        while running:
            cleanup_old_files(recording_dir, config["record"]["max_record_time"])
            time.sleep(INTERVAL)
    finally:
        stop_recording(con)
        con.disconnect()
        print("Daemon stopped")

if __name__ == "__main__":
    main()