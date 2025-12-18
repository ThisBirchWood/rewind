#!/usr/bin/env python3
import os
import datetime
import subprocess
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


def combine_last_x_ts_files(seconds: float, output_file: str) -> None:
    ts_files = load_state()["files"]

    files, start_offset, end_offset = get_ts_files(
        datetime.datetime.now().timestamp() - seconds,
        datetime.datetime.now().timestamp()
    )

    print(f"Combining files: {files} with start offset {start_offset} and end offset {end_offset}")

    with open("file_list.txt", "w") as f:
        for file_path in files:
            f.write(f"file '{file_path}'\n")

    subprocess.run(["ffmpeg", "-y", 
                    "-ss", str(start_offset),
                    "-f", "concat", "-safe", "0", "-i", 
                    "file_list.txt", 
                    "-c", "copy", 
                    output_file])
    
    os.remove("file_list.txt")

def clip(seconds_from_end: float) -> None:
    output_file_name = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.mp4"
    combine_last_x_ts_files(seconds_from_end, output_file_name)
    print(f"Created clip: {output_file_name}")

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