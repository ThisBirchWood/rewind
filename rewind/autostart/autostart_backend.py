class AutostartBackend:
    def __init__(self, program_path: str):
        self.program_path = program_path

    def enable_autostart(self):
        raise NotImplementedError("enable_autostart not implemented for this platform")

    def disable_autostart(self):
        raise NotImplementedError("disable_autostart not implemented for this platform")

    def start_daemon(self):
        raise NotImplementedError("start_daemon not implemented for this platform")

    def stop_daemon(self):
        raise NotImplementedError("stop_daemon not implemented for this platform")