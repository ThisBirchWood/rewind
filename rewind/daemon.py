#!/usr/bin/env python3
import os
import datetime
import time
import obsws_python as obs
import logging
import signal

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rewind.paths import get_state_dir
from rewind.config import Config
from rewind.core import mark, marker_exists, remove_marker
from rewind.state import add_file_to_state, create_state_file_if_needed, cleanup_state

running = True
LOG_FILE =  get_state_dir() / "daemon.log"
INTERVAL = 10
SENTINEL_FILE = os.path.expanduser("~/.config/obs-studio/.sentinel")
OBS_MAX_RETRIES = 5

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.basicConfig(format="%(levelname)s:%(name)s:%(message)s", handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()])
logging.getLogger("obsws_python").setLevel(logging.CRITICAL)

def shutdown(signum, frame):
    global running
    logger.info(f"Received signal {signum}, shutting down cleanly")
    running = False

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

def open_obs_connection(host: str, port: int, password: str, obs_max_retries: int) -> obs.ReqClient:
    con = None
    init_sleep = 1

    for _ in range(obs_max_retries):
        try:
            con = obs.ReqClient(host=host, port=port, password=password)
        except ConnectionRefusedError:
            logger.info("OBS WebSocket not ready, retrying...")
        except obs.events.OBSSDKError:
            raise RuntimeError("Check OBS credentials")
            
        if con:
            logger.info(f"Successfully connected to OBS at {host}:{port}")
            return con

        time.sleep(init_sleep)
        init_sleep *= 2
    
    raise RuntimeError("Could not connect to OBS. Either websocket has not been setup or OBS crashed")

def start_recording(con: obs.ReqClient) -> None:
    con.start_record()
    logger.info("Started recording")

def stop_recording(con: obs.ReqClient) -> None:
    con.stop_record()
    logger.info("Stopped recording")

def create_initial_marker() -> None:
    if marker_exists("daemon-start"):
        remove_marker("daemon-start")

    mark("daemon-start")
    logger.info("Created daemon-start marker")

def cleanup_physical_files(directory: str, max_age_seconds: int) -> None:
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_age = datetime.datetime.now().timestamp() - os.path.getmtime(file_path)
            if file_age > max_age_seconds and filename.endswith(".ts"):
                os.remove(file_path)
                logger.info(f"Removed old file: {file_path}")

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".ts"):
            return

        add_file_to_state(event.src_path)

def main() -> None:
    config = Config()
    con = open_obs_connection(config.obs_host, config.obs_port, config.obs_password, OBS_MAX_RETRIES)

    recording_dir = con.get_record_directory().record_directory
    start_recording(con)

    create_state_file_if_needed()
    create_initial_marker()

    try:
        event_handler = Handler()
        observer = Observer()
        observer.schedule(event_handler, path=recording_dir, recursive=False)
        observer.start()

        while running:
            cleanup_physical_files(recording_dir, config.max_record_time)
            cleanup_state(config.max_record_time)
            time.sleep(INTERVAL)
    finally:
        if observer:
            observer.stop()
            observer.join()

        stop_recording(con)
        con.disconnect()
        logger.info("Daemon stopped")

if __name__ == "__main__":
    main()