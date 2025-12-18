#!/usr/bin/env python3
import os
import datetime
import subprocess
from rewind.paths import load_state

def combine_last_x_ts_files(seconds: float, output_file: str) -> None:
    ts_files = load_state().get("files", [])
    ts_files[-1]["duration"] = get_duration(ts_files[-1]["path"])

    total_duration = 0.0
    files_to_include = []
    
    while ts_files and total_duration < seconds:
        ts_file = ts_files.pop()
        files_to_include.append(ts_file["path"])
        total_duration += ts_file["duration"]

    files_to_include.reverse()
    with open("file_list.txt", "w") as f:
        for file_path in files_to_include:
            f.write(f"file '{file_path}'\n")

    subprocess.run(["ffmpeg", "-y", 
                    "-ss", str(max(0, total_duration - seconds)),
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
    return float(result.stdout)