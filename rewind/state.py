import datetime
import json
import os

from rewind.paths import load_config
from pathlib import Path

APP_NAME = "rewind"
STATE_NAME = "state.json"

def state_dir() -> Path:
    base = os.path.expanduser("~/.local/share")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_state_file_path() -> Path:
    return state_dir() / STATE_NAME

def load_state() -> dict:
    if not get_state_file_path().exists():
        return {"files": []}
    with get_state_file_path().open() as f:
        return json.load(f)

def write_state(state: dict) -> None:
    tmp = get_state_file_path().with_suffix(".tmp")
    with tmp.open("w") as f:
        json.dump(state, f, indent=2)
    tmp.replace(get_state_file_path())  # atomic

def add_file_to_state(file_path: str) -> None:
    state = load_state()
    files = state.get("files", [])

    files.append({
        "path": file_path,
        "timestamp": datetime.datetime.now().timestamp(),
    })

    state["files"] = files
    write_state(state)

def cleanup_state_files() -> None:
    state = load_state()
    files = state.get("files", [])

    # Remove old files from state
    for file in files:
        if not os.path.exists(file["path"]):
            files.remove(file)
            print(f"Removed non-existent file from state: {file['path']}")

    state["files"] = files
    write_state(state)

def create_state_file_if_needed() -> None:
    if not os.path.exists(get_state_file_path()):
        state = {"files": []}
        write_state(state)
