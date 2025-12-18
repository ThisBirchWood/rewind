from pathlib import Path
import os, json, tomllib
from importlib import resources

APP_NAME = "rewind"
USER_CONFIG = Path.home() / ".rewind.toml"

def load_config() -> dict:
    if USER_CONFIG.exists():
        with USER_CONFIG.open("rb") as f:
            return tomllib.load(f)

    # fallback to packaged default
    with resources.files("rewind").joinpath("config.toml").open("rb") as f:
        return tomllib.load(f)

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

def write_state(state: dict) -> None:
    tmp = get_state_file_path().with_suffix(".tmp")
    with tmp.open("w") as f:
        json.dump(state, f, indent=2)
    tmp.replace(get_state_file_path())  # atomic
