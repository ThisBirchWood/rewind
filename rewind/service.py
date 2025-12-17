#!/usr/bin/env python3
import os
import datetime
import time
import obsws_python as obs
import subprocess
import json

from video import get_duration

INTERVAL = 10
MAX_AGE_SECONDS = 60 * 60 * 8
STATE_FILE = "state.json"

def open_obs():
    subprocess.Popen(["obs", "--minimize-to-tray"])

def open_obs_connection() -> obs.ReqClient | None:
    try:
        con = obs.ReqClient()
        return con
    except ConnectionRefusedError:
        print("Could not connect to OBS. Is it running and is the WebSocket server enabled?")
        return None

def start_recording(con):
    con.start_record()
    print("Started recording")

def stop_recording(con):
    con.stop_record()
    print("Stopped recording")

def cleanup_old_files(directory, max_age_seconds):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_age = datetime.datetime.now().timestamp() - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                os.remove(file_path)
                print(f"Removed old file: {file_path}")

def add_file_to_state(file_path):
    state = {}
    if os.path.exists(STATE_FILE):
        state = json.load(open(STATE_FILE))
    files = state.get("files", [])

    if len(files) > 0:
        files[len(files)-1][1] = get_duration(files[len(files)-1][0])

    files.append([file_path, 0.0])
    json.dump(state, open(STATE_FILE, "w"))


def main():
    open_obs()
    time.sleep(5)

    con = open_obs_connection()
    if con is None:
        return
    
    recording_dir = con.get_record_directory().record_directory
    start_recording(con)

    # create state file
    state = {
        "files": []
    }
    json.dump(state, open(STATE_FILE, "w"))

    current_files = os.listdir(recording_dir)

    while True:
        cleanup_old_files(recording_dir, MAX_AGE_SECONDS)
        new_files = os.listdir(recording_dir)
        added_files = set(new_files) - set(current_files)
        for filename in added_files:
            file_path = os.path.join(recording_dir, filename)
            add_file_to_state(file_path)
            print(f"Added new file to state: {file_path}")

        current_files = new_files
        time.sleep(INTERVAL)

    end_recording(con)
    stop_recording(con)
    con.disconnect()

if __name__ == "__main__":
    main()