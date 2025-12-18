#!/usr/bin/env python3
import os
import datetime
import subprocess
import json
from rewind.paths import load_state

"""
Retrieves .ts files recorded between the specified timestamps.
Returns a list of file paths and extra start and end offsets if needed.
get_duration() is used as little as possible since it is slow.
end_timestamp of a file is the start time of the next file.
"""
def get_ts_files(start_timestamp: float, end_timestamp: float) -> tuple[list[str], float, float]:
    ts_files = load_state()["files"]
    selected_files = []
    start_offset = 0.0
    end_offset = 0.0

    for i, file_info in enumerate(ts_files):
        file_start = file_info["timestamp"]
        file_end = ts_files[i + 1]["timestamp"] if i + 1 < len(ts_files) else get_duration(file_info["path"]) + file_start

        if file_end <= start_timestamp:
            continue
        if file_start >= end_timestamp:
            break

        selected_files.append(file_info["path"])

        if file_start <= start_timestamp < file_end:
            start_offset = start_timestamp - file_start
        if file_start < end_timestamp <= file_end:
            end_offset = file_end - end_timestamp

    return selected_files, start_offset, end_offset

def concat_ts_files(file_list: list[str], start_offset: float, end_offset: float, output_file: str) -> None:
    with open("file_list.txt", "w") as f:
        for file_path in file_list:
            f.write(f"file '{file_path}'\n")

    cmd = ["ffmpeg", "-y"]
    if start_offset > 0:
        cmd += ["-ss", str(start_offset)]
    cmd += ["-f", "concat", "-safe", "0", "-i", "file_list.txt", "-c", "copy"]
    if end_offset > 0:
        cmd += ["-t", str(get_duration(file_list[-1]) - end_offset - (start_offset if len(file_list) == 1 else 0))]
    cmd.append(output_file)

    subprocess.run(cmd)
    os.remove("file_list.txt")

def clip(seconds_from_end: float) -> None:
    output_file_name = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.mp4"
    
    files, start_offset, end_offset = get_ts_files(
        start_timestamp=datetime.datetime.now().timestamp() - seconds_from_end,
        end_timestamp=datetime.datetime.now().timestamp()
    )
    print(f"files: {files}, start_offset: {start_offset}, end_offset: {end_offset}")
    concat_ts_files(files, start_offset, end_offset, output_file_name)

    print(f"Created clip: {output_file_name}")

def mark(name: str) -> None:
    if not name:
        raise ValueError("Marker name cannot be empty")
    
    # writes marker to json file (not state)
    markers_file = os.path.join(os.path.dirname(__file__), "markers.json")
    if os.path.exists(markers_file):
        with open(markers_file, "r") as f:
            markers = json.load(f)
    else:
        markers = []

    markers.append({
        "name": name,
        "timestamp": datetime.datetime.now().timestamp()
    })

    with open(markers_file, "w") as f:
        json.dump(markers, f, indent=4)
    print(f"Added marker: {name}")

def print_markers() -> None:
    markers_file = os.path.join(os.path.dirname(__file__), "markers.json")
    if not os.path.exists(markers_file):
        print("No markers found.")
        return

    with open(markers_file, "r") as f:
        markers = json.load(f)

    for marker in markers:
        format_time = datetime.datetime.fromtimestamp(marker['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{format_time} -> {marker['name']}")

def clean_old_markers() -> None:
    markers_file = os.path.join(os.path.dirname(__file__), "markers.json")
    if not os.path.exists(markers_file):
        return

    with open(markers_file, "r") as f:
        markers = json.load(f)

    current_time = datetime.datetime.now().timestamp()
    markers = [m for m in markers if current_time - m['timestamp'] <= 60]

    with open(markers_file, "w") as f:
        json.dump(markers, f, indent=4)

def get_duration(file_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    # error checking
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for file {file_path}")

    return float(result.stdout)