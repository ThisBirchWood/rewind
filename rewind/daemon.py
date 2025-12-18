#!/usr/bin/env python3
import os
import datetime
import signal
import time
import obsws_python as obs
import subprocess

from rewind.video import get_duration
from rewind.paths import load_state, write_state

INTERVAL = 10
MAX_AGE_SECONDS = 60 * 60 * 1
running = True

def open_obs():
    subprocess.Popen(["obs", "--minimize-to-tray"])

def open_obs_connection() -> obs.ReqClient | None:
    try:
        con = obs.ReqClient()
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

    # Update duration of last file if exists 
    if files and len(files) > 0:
        last_file = files[-1]
        last_file["duration"] = get_duration(last_file["path"])

    files.append({
        "path": file_path,
        "duration": 0.0
    })

    state["files"] = files
    write_state(state)

def handle_shutdown(signum, frame):
    global running
    running = False

def main() -> None:
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    open_obs()
    time.sleep(5)
    con = open_obs_connection()
    if con is None:
        return
    recording_dir = con.get_record_directory().record_directory
    start_recording(con)

    create_state_file()

    current_files = os.listdir(recording_dir)

    try:
        while running:
            cleanup_old_files(recording_dir, MAX_AGE_SECONDS)

            new_files = os.listdir(recording_dir)
            added_files = set(new_files) - set(current_files)

            # Add new files to state
            for filename in added_files:
                file_path = os.path.join(recording_dir, filename)
                add_file_to_state(file_path)
                print(f"Added new file to state: {file_path}")

            current_files = new_files
            time.sleep(INTERVAL)
    finally:
        stop_recording(con)
        con.disconnect()
        print("Daemon stopped")

if __name__ == "__main__":
    main()