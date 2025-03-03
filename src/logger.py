"""
If you don't need a console, remove the show_console() and hide_console() functions
and the console handler in the logger class then you can remove the ctypes dependency.
"""

import inspect
import logging
import logging.handlers
import os
import sys

from ctypes import windll
from datetime import datetime
from platform import system, architecture, release, version

WORK_PATH = os.path.join(os.getcwd(), "ExampleApp") # Change this to where you want to store your logs
LOG_FILE = os.path.join(WORK_PATH, "example_app.log")
LOG_BACKUP = os.path.join(WORK_PATH, "Log Backup")
USER_OS = system()
USER_OS_ARCH = architecture()[0][:2]
USER_OS_RELEASE = release()
USER_OS_VERSION = version()


def executable_dir():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

# Remove if not needed.
def log_init_str(app_name: str, app_version: str):
    return f"""

------------------ {app_name} ------------------

    - Version: {app_version if app_version else "None"}
    - Operating System: {USER_OS} {USER_OS_RELEASE} x{USER_OS_ARCH} v{USER_OS_VERSION}
    - Working Directory: {WORK_PATH}
    - Executable Directory: {executable_dir()}


"""


class CustomLogHandler(logging.FileHandler):
    def __init__(
        self,
        filename,
        archive_path=LOG_BACKUP,
        archive_name="backup_%Y%m%d_%H%M%S.log",
        max_bytes=524288, # 512KB max file size before it gets archived
        encoding="utf-8",
        **kwargs,
    ):
        self.archive_path = archive_path
        self.archive_name = archive_name
        self.max_bytes = max_bytes
        self.encoding = encoding

        self._archive_log(filename)
        super().__init__(filename, **kwargs)

    def _archive_log(self, filepath):
        if os.path.exists(filepath) and os.path.getsize(filepath) > self.max_bytes:
            os.makedirs(self.archive_path, exist_ok=True)
            timestamped_name = datetime.now().strftime(self.archive_name)
            archive_file = os.path.join(self.archive_path, timestamped_name)
            os.rename(filepath, archive_file)

    def close(self):
        super().close()
        self._archive_log(self.baseFilename)


class CustomLogFilter(logging.Filter):
    def filter(self, record):
        record.caller_name = inspect.stack()[6].function
        return True


class LOGGER:
    def __init__(self, app_name="", app_version=""):
        self.app_name = app_name
        self.app_version = app_version
        self.logger = logging.getLogger("MAIN")
        self.logger.addFilter(CustomLogFilter())
        self.logger.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] (%(caller_name)s): %(message)s",
            datefmt="%H:%M:%S",
        )

        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        self.file_handler = CustomLogHandler(LOG_FILE)
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.file_handler)
        self.console_handler = None

    # this is for packed executables with GUIs to enable/disable a debug console.
    def show_console(self):
        if not windll.kernel32.GetConsoleWindow():
            windll.kernel32.AllocConsole()
            sys.stdout = open("CONOUT$", "w", encoding="utf-8")
            sys.stderr = open("CONOUT$", "w", encoding="utf-8")
            windll.kernel32.SetConsoleTitleW(self.app_name or "Debug Console")
        if not self.console_handler:
            self.console_handler = logging.StreamHandler(sys.stdout)
            self.console_handler.setLevel(logging.DEBUG)
            self.console_handler.setFormatter(self.formatter)
            self.logger.addHandler(self.console_handler)
            print(log_init_str(self.app_version))

    def hide_console(self):
        if windll.kernel32.GetConsoleWindow():
            windll.kernel32.FreeConsole()
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        if self.console_handler:
            self.logger.removeHandler(self.console_handler)
            self.console_handler = None

    def debug(self, msg: str):
        self.logger.debug(msg)

    def info(self, msg: str):
        self.logger.info(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)

    def critical(self, msg: str):
        self.logger.critical(msg)

    # Call this on init in your app to write a simple log banner.
    def on_init(self):
        with open(LOG_FILE, "a") as f:
            f.write(log_init_str(self.app_name, self.app_version))
            f.flush()
            f.close()
