#!/usr/bin/env python3
import datetime
import json
import os

from pathlib import Path
from rewind.paths import get_state_dir

STATE_NAME = "state.json"
EMPTY_STATE = {
    "files": [],
    "markers": []
}

def get_state_file_path() -> Path:
    return get_state_dir() / STATE_NAME

def load_state() -> dict:
    with get_state_file_path().open() as f:
        return json.load(f)

def write_state(state: dict) -> None:
    if "files" not in state or "markers" not in state:
        raise ValueError("Invalid state configuration. State must contain 'files' and 'markers' keys.")

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

def add_marker_to_state(marker_name: str) -> None:
    state = load_state()
    markers = state.get("markers", [])

    existing_markers = {m["name"] for m in markers}
    if marker_name in existing_markers:
        raise ValueError("Marker already exists")
    
    markers.append({
        "name": marker_name,
        "timestamp": datetime.datetime.now().timestamp()
    })

    state["markers"] = markers
    write_state(state)

def remove_marker_from_state(marker_name: str) -> None:
    state = load_state()
    markers = state.get("markers", [])
    markers = [marker for marker in markers if marker["name"] != marker_name]

    state["markers"] = markers
    write_state(state)

def cleanup_state(max_age_seconds: float) -> None:
    state = load_state()
    files = state.get("files", [])
    markers = state.get("markers", [])
    now = datetime.datetime.now().timestamp()

    # Remove files that do not exist
    state["files"] = [
        file for file in files 
        if os.path.exists(file["path"])
    ]

    # Remove files and markers beyond max age
    state["files"] = [
        file for file in files 
        if now - file["timestamp"] <= max_age_seconds
    ]


    state["markers"] = [
        marker for marker in markers
        if now - marker["timestamp"] <= max_age_seconds
    ]

    write_state(state)

def create_state_file_if_needed() -> None:
    if not get_state_file_path().exists():
        write_state(EMPTY_STATE)
