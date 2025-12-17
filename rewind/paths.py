from pathlib import Path
import os, json

APP_NAME = "rewind"

def state_dir() -> Path:
    base = os.path.expanduser("~/.local/share")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_state_file_path() -> Path:
    return state_dir() / "state.json"

def get_state_file() -> dict:
    path = get_state_file_path()
    if not path.exists():
        return {"files": []}
    with path.open() as f:
        return json.load(f)