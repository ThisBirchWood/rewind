#!/usr/bin/env python3
import tomllib

from pathlib import Path
from importlib import resources

APP_NAME = "rewind"
USER_CONFIG = Path.home() / ".rewind.toml"
STATE_NAME = "state.json"

def load_config() -> dict:
    if USER_CONFIG.exists():
        with USER_CONFIG.open("rb") as f:
            return tomllib.load(f)

    # fallback to packaged default
    with resources.files("rewind").joinpath("config.toml").open("rb") as f:
        return tomllib.load(f)