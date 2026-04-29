import os
import subprocess
import tempfile

from rewind.state import load_state
from tqdm import tqdm

"""
Retrieves .ts files recorded between the specified timestamps.
Returns a list of file paths and extra start and end offsets if needed.
get_duration() is used as little as possible since it is slow.
end_timestamp of a file is the start time of the next file.
"""
def get_ts_files(
        ts_files: list[dict],
        start_timestamp: float, 
        end_timestamp: float
        ) -> tuple[list[str], float, float]:
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

        if file_start < start_timestamp:
            start_offset = start_timestamp - file_start

        if file_end >= end_timestamp:
            end_offset = file_end - end_timestamp
            break
        
    return selected_files, start_offset, end_offset

def concat_ts_files(file_list: list[str], start_offset: float, end_offset: float, length: float, output_file: str) -> None:
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