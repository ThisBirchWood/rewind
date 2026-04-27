#!/usr/bin/env python3
import os
import datetime
import subprocess
import tempfile

from rewind.state import load_state, add_marker_to_state, remove_marker_from_state
from rewind.config import Config
from tqdm import tqdm

config = Config()

def clip(seconds_from_end: float) -> None:
    if seconds_from_end <= 0 or seconds_from_end > 600:
        raise ValueError("Clip length must be positive and less than or equal to 10 minutes")

    clip_output = Config().get_clip_output()
    os.makedirs(clip_output, exist_ok=True)

    output_file_name = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.mp4"
    output_path = os.path.join(clip_output, output_file_name)

    start_timestamp = datetime.datetime.now().timestamp() - seconds_from_end
    end_timestamp = datetime.datetime.now().timestamp()
    length = end_timestamp - start_timestamp
    
    files, start_offset, end_offset = _get_ts_files(
        start_timestamp,
        end_timestamp
    )

    _concat_ts_files(files, start_offset, end_offset, length, output_path)
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

    files, start_offset, end_offset = _get_ts_files(
        first_timestamp,
        second_timestamp
    )

    _concat_ts_files(files, start_offset, end_offset, second_timestamp - first_timestamp, output_path)
    print(f"Created video file: {output_path}")

def mark(name: str) -> None:
    if not name:
        raise ValueError("Marker name cannot be empty")
    
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

"""
Retrieves .ts files recorded between the specified timestamps.
Returns a list of file paths and extra start and end offsets if needed.
get_duration() is used as little as possible since it is slow.
end_timestamp of a file is the start time of the next file.
"""
def _get_ts_files(start_timestamp: float, end_timestamp: float) -> tuple[list[str], float, float]:
    ts_files = [f for f in load_state()["files"] if os.path.exists(f["path"])]
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

def _concat_ts_files(file_list: list[str], start_offset: float, end_offset: float, length: float, output_file: str) -> None:
    tmp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    try:
        for file_path in file_list:
            tmp_file.write(f"file '{file_path}'\n")
        tmp_file.close()

        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostats", "-progress", "pipe:1"]
        if start_offset > 0:
            cmd += ["-ss", str(start_offset)]
        if end_offset > 0:
            cmd += ["-t", str(length)]
        cmd += ["-f", "concat", "-safe", "0", "-i", tmp_file.name, "-c", "copy"]
        cmd.append(output_file)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        init_ms_val = 0
        init_ms_val_set = False

        with tqdm(
            total=length,
            unit="s",
            unit_scale=True,
            unit_divisor=60,
            desc="Processing",
            leave=True,
        ) as pbar:
            for line in process.stdout:  # type: ignore[union-attr]
                line = line.strip()

                if line.startswith("out_time_ms="):
                    out_time_ms = int(line.split("=")[1])

                    if not init_ms_val_set:
                        init_ms_val = out_time_ms
                        init_ms_val_set = True
                    out_time_ms -= init_ms_val

                    seconds = abs(out_time_ms / 1_000_000)
                    pbar.n = min(seconds, length)
                    pbar.refresh()

                elif line == "progress=end":
                    break

        ret = process.wait()
        if ret != 0:
            raise RuntimeError("ffmpeg failed")
    finally:
        os.unlink(tmp_file.name)

def get_duration(file_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for file {file_path}")

    return float(result.stdout.strip())