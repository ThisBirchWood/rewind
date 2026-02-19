#!/usr/bin/env python3
import datetime
import json
import os

from pathlib import Path
from rewind.paths import get_state_dir

STATE_NAME = "state.json"

def get_state_file_path() -> Path:
    return get_state_dir() / STATE_NAME

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

    # Idempotency guard
    existing_paths = {f["path"] for f in files}
    if file_path in existing_paths:
        return

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
    state["files"] = [file for file in files if os.path.exists(file["path"])]
    write_state(state)

def create_state_file_if_needed() -> None:
    if not os.path.exists(get_state_file_path()):
        state = {"files": []}
        write_state(state)
