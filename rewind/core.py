#!/usr/bin/env python3
import os
import datetime

from rewind.config import Config
from rewind.media import get_ts_files, concat_ts_files
from rewind.state import load_state, add_marker_to_state, remove_marker_from_state

config = Config()

def clip(seconds_from_end: float) -> None:
    if seconds_from_end <= 0 or seconds_from_end > 600:
        raise ValueError("Clip length must be positive and less than or equal to 10 minutes")

    clip_output = config.get_clip_output()
    os.makedirs(clip_output, exist_ok=True)

    output_file_name = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.mp4"
    output_path = os.path.join(clip_output, output_file_name)

    start_timestamp = datetime.datetime.now().timestamp() - seconds_from_end
    end_timestamp = datetime.datetime.now().timestamp()
    length = end_timestamp - start_timestamp
    
    ts_files = [f for f in load_state()["files"] if os.path.exists(f["path"])]
    files, start_offset, end_offset = get_ts_files(
        ts_files,
        start_timestamp,
        end_timestamp
    )

    concat_ts_files(files, start_offset, end_offset, length, output_path)
    print(f"Created clip: {output_path}")

def save(first_marker: str, second_marker: str):
    vod_dir = config.get_vod_output()
    os.makedirs(vod_dir, exist_ok=True)

    first_timestamp = get_marker_timestamp(first_marker)
    second_timestamp = get_marker_timestamp(second_marker)

    if first_timestamp >= second_timestamp:
        raise ValueError("First marker must be before second marker")

    output_file_name = f"{datetime.datetime.fromtimestamp(first_timestamp).strftime('%Y-%m-%d_%H:%M:%S')}-[{first_marker}-{second_marker}].mp4"
    output_path = os.path.join(vod_dir, output_file_name)

    ts_files = [f for f in load_state()["files"] if os.path.exists(f["path"])]

    files, start_offset, end_offset = get_ts_files(
        ts_files,
        first_timestamp,
        second_timestamp
    )

    concat_ts_files(files, start_offset, end_offset, second_timestamp - first_timestamp, output_path)
    print(f"Created video file: {output_path}")

def mark(name: str) -> None:
    if not name:
        name = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    add_marker_to_state(name)
    print(f"Added marker: {name}")

def get_marker_timestamp(name: str) -> float:
    markers = load_state().get("markers", [])

    for marker in markers:
        if marker["name"] == name:
            return marker["timestamp"]
    
    raise ValueError("Marker name does not exist")

def print_markers() -> None:
    markers = load_state().get("markers", [])

    if markers == []:
        print("No markers exist.")

    for marker in markers:
        format_time = datetime.datetime.fromtimestamp(marker['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{format_time} -> {marker['name']}")
        
def remove_marker(name: str) -> None:
    remove_marker_from_state(name)
    print(f"Removed marker: {name}")

def marker_exists(name: str) -> bool:
    markers = load_state().get("markers", [])

    for marker in markers:
        if marker["name"] == name:
            return True
    
    return False