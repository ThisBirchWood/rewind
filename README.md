A minimal Python script to control OBS Studio recording via OBS WebSocket and to combine segmented .ts recordings into a single .mp4 clip using FFmpeg.

This project is meant to be (and will evolve into) a long-duration, disk-backed replay buffer.

# Steps
1) Setup OBS and make the recording output: "ts" with a 1 minute segment size
2) Enable OBS websocket and take note of the host, port and password
3) Setup config.toml with host, port, password info
4) Run the daemon as a background service (rewind-daemon)