import json
import os
import shutil
import subprocess
import sys
import webbrowser

from pathlib import Path
from src.logger import LOGGER


WORK_PATH = os.path.join(os.getcwd(), "ExampleApp")
PARENT_PATH = Path(__file__).parent
ASSETS_PATH = PARENT_PATH / Path(r"assets")
CONFIG_PATH = os.path.join(WORK_PATH, "settings.json")
LOG = LOGGER()


def res_path(path: str):
    return ASSETS_PATH / Path(path)


def executable_dir():
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def read_cfg(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            try:
                data = json.load(f)
                f.close()
                return data
            except Exception:
                return None
    return None


def read_cfg_item(file, item_name):
    if os.path.exists(file):
        with open(file, "r") as f:
            try:
                data = json.load(f)
                if item_name in data:
                    f.close()
                    return data[item_name]
            except Exception:
                return None
    return None


def save_cfg(file, list):
    open_mode = os.path.exists(file) and "w" or "x"
    with open(file, open_mode) as f:
        json.dump(list, f, indent=4)
        f.close()


def save_cfg_item(file, item_name, value):
    config = read_cfg(file)
    with open(file, "w") as f:
        config[item_name] = value
        json.dump(config, f, indent=4)
        f.close()


def delete_folder(folder_path, on_fail=None, *args):
    if not os.path.exists(folder_path):
        LOG.error(f"Folder path does not exist. {folder_path}")
        if on_fail:
            on_fail("Folder path does not exist.", [1.0, 0.0, 0.0])
        return

    try:
        shutil.rmtree(folder_path)
    except WindowsError:
        try:
            os.chmod(folder_path, 0o777)
            shutil.rmtree(folder_path)
        except Exception:
            LOG.error(f"Failed to delete {folder_path}")
            if on_fail:
                on_fail(*args)


def delete_file(file_path, on_fail=None, *args):
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        LOG.error(f"Path either does not exist or is not a file: {file_path}")
        if on_fail:
            on_fail("Path either does not exist or is not a file.", [1.0, 0.0, 0.0])
        return

    try:
        os.remove(file_path)
    except WindowsError:
        try:
            os.chmod(file_path, 0o777)
            os.remove(file_path)
        except Exception:
            LOG.error(f"Failed to delete {file_path}")
            if on_fail:
                on_fail(*args)


def stringFind(string: str, sub: str):
    return string.lower().find(sub.lower()) != -1


def stringContains(string: str, subs: dict):
    return any(s.lower() in string.lower() for s in subs)


def is_file_saved(name, list):
    if len(list) > 0:
        for file in list:
            if file["name"] == name:
                return True
    return False


def open_folder(path: str):
    if not os.path.exists(path):
        os.makedirs(path)
    subprocess.Popen(f"explorer {os.path.abspath(path)}")


def visit_url(url: str):
    webbrowser.open_new_tab(url)


def is_thread_active(thread) -> bool:
    return thread and not thread.done()
