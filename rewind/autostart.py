#!/usr/bin/env python3
import os
import platform
import shutil
import subprocess

from pathlib import Path

APP_NAME = "rewind-daemon"

def _find_executable():
    path = shutil.which(APP_NAME)
    if not path:
        raise RuntimeError(f"{APP_NAME} not found in PATH")
    return path

def _run(cmd: list[str]):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result

def _install_linux(program_path: str):
    systemd_dir = Path.home() / ".config/systemd/user"
    systemd_dir.mkdir(parents=True, exist_ok=True)

    obs_service = systemd_dir / "obs.service"
    daemon_service = systemd_dir / "rewind-daemon.service"

    if obs_service.exists():
        print("obs.service already exists, skipping creation")
    else:
        obs_service.write_text("""[Unit]
Description=OBS Studio
After=graphical-session.target
Wants=graphical-session.target

[Service]
ExecStart=obs --minimize-to-tray
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
""")

    if daemon_service.exists():
        print("rewind-daemon.service already exists, skipping creation")
    else:
        daemon_service.write_text(f"""[Unit]
Description=Rewind Daemon
After=obs.service
Requires=obs.service

[Service]
ExecStart={program_path}
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
""")

    _run(["systemctl", "--user", "daemon-reload"])

    _run(["systemctl", "--user", "enable", "obs.service"])
    _run(["systemctl", "--user", "enable", "rewind-daemon.service"])

    _run(["systemctl", "--user", "start", "obs.service"])
    _run(["systemctl", "--user", "start", "rewind-daemon.service"])

    print("Installed and started OBS + rewind-daemon via systemd")

def install():
    system = platform.system()
    program_path = _find_executable()

    if system == "Linux":
        _install_linux(program_path)
    else:
        raise RuntimeError(f"Autostart on OS {system} not compatible or not implemented")

if __name__ == "__main__":
    install()