import os, subprocess, datetime

def combine_ts_to_mp4(ts_files, output_file):
    # FFMPEG requires a text file with the list of files to concatenate
    with open("file_list.txt", "w") as f:
        for ts in ts_files:
            f.write(f"file '{ts}'\n")

    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "file_list.txt", "-c", "copy", output_file])
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

def save(record_dir, output_file_name):
    # Gather all ts files and combine them into a single mp4
    ts_files = [f for f in os.listdir(record_dir) if f.endswith(".ts")]
    ts_files.sort(key=lambda x: os.path.getmtime(os.path.join(record_dir, x)))

    combine_ts_to_mp4([os.path.join(record_dir, f) for f in ts_files], output_file_name)
    clean_old_ts_files(record_dir)