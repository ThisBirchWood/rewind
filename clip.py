from datetime import datetime
from video import clip

import obsws_python as obs
import sys, os

command = sys.argv[1] if len(sys.argv) > 1 else None

con = obs.ReqClient()
response = con.get_version()
print(f"OBS WebSocket Version: {response.obs_web_socket_version}")

if command == "start":
    con.start_record()
    print(f"Started recording")
elif command == "stop":
    con.stop_record()
    print("Stopped recording")
elif command == "clip":
    record_dir = con.get_record_directory()
    output_file_name = f"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.mp4"
    clip(record_dir.record_directory, output_file_name)
    
    print(f"Created clip: {output_file_name}")
else:
    print("Unknown command. Use 'start', 'stop', or 'clip'.")

con.disconnect()
