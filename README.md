# Overview
rewind is a lightweight, disk-backed replay recording tool for OBS that continuously records video into timestamped chunks and lets you retroactively extract meaningful moments. Instead of a short, RAM-limited replay buffer, it keeps a rolling on-disk timeline for the duration of a session, allowing you to mark events as they happen and later export clips either from the last N seconds or between named markers. A background daemon manages recording, chunk tracking, and cleanup, while a simple CLI provides fast, scriptable control over marking and clip creation—prioritizing reliability, low overhead, and post-hoc selection of what parts of a session are worth keeping.

# Steps
1) Setup OBS and make the recording output: "ts" with a 1 minute segment size
2) Enable OBS websocket and take note of the host, port and password
3) Setup config.toml with host, port, password info
4) Run the daemon as a background service (rewind-daemon)
