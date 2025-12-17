import os, subprocess, datetime, json

from rewind.paths import load_state

def save(seconds, output_file):
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

def clean_old_ts_files(record_dir, max_age_seconds=60*60*3):
    current_time = datetime.datetime.now().timestamp()
    for filename in os.listdir(record_dir):
        if filename.endswith(".ts"):
            file_path = os.path.join(record_dir, filename)
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                os.remove(file_path)
                print(f"Deleted old file: {file_path}")

def get_duration(file_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)