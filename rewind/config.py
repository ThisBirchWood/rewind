#!/usr/bin/env python3
import os
import tomllib
import tomli_w
from pathlib import Path

from rewind.paths import get_config_dir

_CONFIG_NAME = "config.toml"
_EXAMPLE_CONFIG = Path(__file__).parent / "example.config.toml"


class Config:
    def __init__(self):
        self._config_dir = get_config_dir()
        self._config_file = self._config_dir / _CONFIG_NAME
        self._data = self._load()

    def _load(self) -> dict:
        if not self._config_file.exists():
            self._config_dir.mkdir(parents=True, exist_ok=True)
            self._config_file.write_text(_EXAMPLE_CONFIG.read_text())

        with self._config_file.open("rb") as f:
            return tomllib.load(f)

    def _save(self) -> None:
        with self._config_file.open("wb") as f:
            tomli_w.dump(self._data, f)

    @property
    def obs_host(self) -> str:
        return self._data["obs"]["host"]

    @obs_host.setter
    def obs_host(self, value: str) -> None:
        self._data["obs"]["host"] = value
        self._save()

    @property
    def obs_port(self) -> int:
        return self._data["obs"]["port"]

    @obs_port.setter
    def obs_port(self, value: int) -> None:
        self._data["obs"]["port"] = value
        self._save()

    @property
    def obs_password(self) -> str:
        return self._data["obs"]["password"]

    @obs_password.setter
    def obs_password(self, value: str) -> None:
        self._data["obs"]["password"] = value
        self._save()

    @property
    def max_record_time(self) -> int:
        return self._data["record"]["max_record_time"]

    @max_record_time.setter
    def max_record_time(self, value: int) -> None:
        self._data["record"]["max_record_time"] = value
        self._save()

    @property
    def clip_output(self) -> str:
        return os.path.expanduser(self._data["record"]["clip_output"])

    @clip_output.setter
    def clip_output(self, value: str) -> None:
        self._data["record"]["clip_output"] = value
        self._save()

    @property
    def vod_output(self) -> str:
        return os.path.expanduser(self._data["record"]["vod_output"])

    @vod_output.setter
    def vod_output(self, value: str) -> None:
        self._data["record"]["vod_output"] = value
        self._save()

    def get(self, key: str) -> str:
        section, _, field = key.partition(".")
        try:
            return str(self._data[section][field])
        except KeyError:
            raise KeyError(f"Unknown config key: {key!r}")

    def set(self, key: str, value: str) -> None:
        section, _, field = key.partition(".")
        try:
            current = self._data[section][field]
        except KeyError:
            raise KeyError(f"Unknown config key: {key!r}")
        self._data[section][field] = type(current)(value)
        self._save()

    def show(self) -> None:
        for section, values in self._data.items():
            for field, value in values.items():
                print(f"{section}.{field} = {value!r}")
