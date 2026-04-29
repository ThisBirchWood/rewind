#!/usr/bin/env python3
import platform
import shutil

from rewind.os.linux import LinuxBackend

APP_NAME = "rewind-daemon"

def _find_executable():
    path = shutil.which(APP_NAME)
    if not path:
        raise RuntimeError(f"{APP_NAME} not found in PATH")
    return path

def _get_backend():
    system = platform.system()
    program_path = _find_executable()
    if system == "Linux":
        return LinuxBackend(program_path)
    else:
        raise RuntimeError(f"Autostart on OS {system} not compatible or not implemented")

def enable_autostart():
    backend = _get_backend()
    backend.enable_autostart()
    
def disable_autostart():
    backend = _get_backend()
    backend.disable_autostart()

def start_daemon():
    backend = _get_backend()
    backend.start_daemon()
    
def stop_daemon():
    backend = _get_backend()
    backend.stop_daemon()