#!/usr/bin/env python3
import os
from pathlib import Path

APP_NAME = "rewind"

def get_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    return Path(base) / APP_NAME

def get_state_dir() -> Path:
    base = os.path.expanduser("~/.local/share")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path
