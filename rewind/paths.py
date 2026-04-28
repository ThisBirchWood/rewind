#!/usr/bin/env python3
import os
import platform
from pathlib import Path

APP_NAME = "rewind"

def _create_dirs(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

"""
Returns the path to the directory where config files should be stored, creating it if it doesn't exist.
The location is determined based on the operating system:
- Linux: Uses XDG_CONFIG_HOME environment variable or defaults to ~/.config/rewind
- macOS: Uses ~/Library/Application Support/rewind
- Windows: Uses APPDATA environment variable or defaults to %APPDATA%\rewind
"""
def get_config_dir() -> Path:
    system = platform.system()
    home = Path.home()

    if system == "Linux":
        base = os.environ.get("XDG_CONFIG_HOME", home / ".config")
        path = Path(base) / APP_NAME
        _create_dirs(path)
        return path
    elif system == "Darwin":
        path = home / "Library" / "Application Support" / APP_NAME
        _create_dirs(path)
        return path
    elif system == "Windows":
        path = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming")) / APP_NAME
        _create_dirs(path)
        return path
    else:
        raise OSError("Unsupported operating system")

"""
Returns the path to the directory where state files should be stored, creating it if it doesn't exist.
The location is determined based on the operating system:
- Linux: Uses XDG_STATE_HOME environment variable or defaults to ~/.local/state/rewind
- macOS: Uses ~/Library/Application Support/rewind/state
- Windows: Uses LOCALAPPDATA environment variable or defaults to %LOCALAPPDATA%\rewind\state
"""
def get_state_dir() -> Path:
    system = platform.system()
    home = Path.home()

    if system == "Linux":
        base = os.environ.get("XDG_STATE_HOME", home / ".local" / "state")
        path = Path(base) / APP_NAME
        _create_dirs(path)
        return path
    elif system == "Darwin":
        path = home / "Library" / "Application Support" / APP_NAME / "state"
        _create_dirs(path)
        return path
    elif system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
        path = base / APP_NAME / "state"
        _create_dirs(path)
        return path
    else:
        raise OSError("Unsupported operating system")