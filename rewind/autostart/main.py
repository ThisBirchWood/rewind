#!/usr/bin/env python3
import platform
import shutil

import rewind.autostart.linux as linux_autostart

APP_NAME = "rewind-daemon"

def _find_executable():
    path = shutil.which(APP_NAME)
    if not path:
        raise RuntimeError(f"{APP_NAME} not found in PATH")
    return path

def enable_autostart():
    system = platform.system()
    program_path = _find_executable()

    if system == "Linux":
        linux_autostart.enable_autostart_linux(program_path)
    else:
        raise RuntimeError(f"Autostart on OS {system} not compatible or not implemented")
    
def disable_autostart():
    system = platform.system()
    program_path = _find_executable()

    if system == "Linux":
        linux_autostart.disable_autostart_linux(program_path)
    else:
        raise RuntimeError(f"Autostart on OS {system} not compatible or not implemented")
    
def start_daemon():
    system = platform.system()
    program_path = _find_executable()

    if system == "Linux":
        linux_autostart.start_daemon_linux(program_path)
    else:
        raise RuntimeError(f"Autostart on OS {system} not compatible or not implemented")
    
def stop_daemon():
    system = platform.system()
    program_path = _find_executable()

    if system == "Linux":
        linux_autostart.stop_daemon_linux(program_path)
    else:
        raise RuntimeError(f"Autostart on OS {system} not compatible or not implemented")