import subprocess

from pathlib import Path

def _run(cmd: list[str]):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result

def _create_systemd_service(program_path: str):
    systemd_dir = Path.home() / ".config/systemd/user"
    systemd_dir.mkdir(parents=True, exist_ok=True)

    obs_service = systemd_dir / "obs.service"
    daemon_service = systemd_dir / "rewind-daemon.service"

    obs_service.write_text("""[Unit]
Description=OBS Studio
After=graphical-session.target
Wants=graphical-session.target

[Service]
# Ensure OBS sentinel files are cleaned up before starting the daemon
ExecStartPre=-/usr/bin/rm -rf %h/.config/obs-studio/.sentinel
ExecStart=obs --minimize-to-tray
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
""")

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

def enable_autostart_linux(program_path: str):
    _create_systemd_service(program_path)
    _run(["systemctl", "--user", "daemon-reload"])

    _run(["systemctl", "--user", "enable", "obs.service"])
    _run(["systemctl", "--user", "enable", "rewind-daemon.service"])

    print("Installed OBS + rewind-daemon via systemd")

def disable_autostart_linux(program_path: str):
    _create_systemd_service(program_path)
    _run(["systemctl", "--user", "disable", "rewind-daemon.service"])
    _run(["systemctl", "--user", "disable", "obs.service"])

    systemd_dir = Path.home() / ".config/systemd/user"
    (systemd_dir / "rewind-daemon.service").unlink(missing_ok=True)
    (systemd_dir / "obs.service").unlink(missing_ok=True)
    _run(["systemctl", "--user", "daemon-reload"])

def start_daemon_linux(program_path: str):
    _create_systemd_service(program_path)
    _run(["systemctl", "--user", "start", "rewind-daemon.service"])

def stop_daemon_linux(program_path: str):
    _create_systemd_service(program_path)
    _run(["systemctl", "--user", "stop", "rewind-daemon.service"])
    _run(["systemctl", "--user", "stop", "obs.service"])