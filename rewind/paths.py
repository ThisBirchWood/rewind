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

def load_state() -> dict:
    if not get_state_file_path().exists():
        return {"files": []}
    with get_state_file_path().open() as f:
        return json.load(f)

def write_state(state: dict):
    tmp = get_state_file_path().with_suffix(".tmp")
    with tmp.open("w") as f:
        json.dump(state, f, indent=2)
    tmp.replace(get_state_file_path())  # atomic
