#!/usr/bin/env python3
import os
import tomllib
from pathlib import Path
from importlib import resources

APP_NAME = "rewind"
CONFIG_NAME = "config.toml"
STATE_NAME = "state.json"

def get_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    return Path(base) / APP_NAME


def load_config() -> dict:
    config_dir = get_config_dir()
    config_file = config_dir / CONFIG_NAME

    print(f"Loading config from {config_file}")

    # Create config directory if it doesn't exist and replace with default config
    if not config_file.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        with resources.open_text("rewind", CONFIG_NAME) as default_config:
            with config_file.open("w") as f:
                f.write(default_config.read())

    with config_file.open("rb") as f:
        return tomllib.load(f)
        
