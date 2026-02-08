import json
import os
import socket
import threading
import time
from typing import Dict, List

import webview

APP_TITLE = "iClick Shortcut Config"
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
CONFIG_PATH = os.path.join(CONFIG_DIR, "gesture_map.json")

LOCK_HOST = "127.0.0.1"
LOCK_PORT = 8767

DEFAULT_MAPPINGS = [
    {"gesture": "blink_twice", "action": "left_click", "args": {}},
    {"gesture": "hold", "action": "right_click", "args": {}},
    {"gesture": "open_palm", "action": "open_buddy", "args": {}},
    {"gesture": "wave", "action": "typing", "args": {}},
]


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return list(DEFAULT_MAPPINGS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return list(DEFAULT_MAPPINGS)


def save_config(mappings):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=2)


def _load_action_map() -> Dict[str, str]:
    data = load_config()
    action_map: Dict[str, str] = {}
    for item in data:
        gesture = item.get("gesture")
        action = item.get("action")
        if gesture and action:
            action_map[gesture] = action
    return action_map


class SingleInstance:
    def __init__(self, on_close):
        self.on_close = on_close
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)

    def try_lock(self):
        try:
            self.sock.bind((LOCK_HOST, LOCK_PORT))
            self.sock.listen(1)
            threading.Thread(target=self._listen, daemon=True).start()
            return True
        except OSError:
            return False

    def _listen(self):
        while True:
            try:
                client, _ = self.sock.accept()
                client.close()
                self.on_close()
            except OSError:
                break

    @staticmethod
    def signal_existing():
        try:
            with socket.create_connection((LOCK_HOST, LOCK_PORT), timeout=0.3):
                pass
            return True
        except OSError:
            return False


class ConfigAPI:
    def __init__(self):
        self.latest = _load_action_map()

    def load_mappings(self):
        self.latest = _load_action_map()
        return self.latest

    def save_mappings(self, mappings: List[Dict]):
        save_config(mappings)
        self.latest = _load_action_map()


def _ui_url():
    dev_url = os.environ.get("ICLICK_UI_DEV_URL")
    if dev_url:
        return dev_url
    dist = os.path.join(os.path.dirname(__file__), "..", "ui", "dist", "index.html")
    return os.path.abspath(dist) + f"?v={int(time.time())}"


def main():
    window_ref = {"window": None}

    def on_close_signal():
        win = window_ref["window"]
        if win:
            try:
                win.evaluate_js("window.__iclickSaveConfig && window.__iclickSaveConfig()")
            except Exception:
                pass
            win.destroy()

    locker = SingleInstance(on_close_signal)
    if not locker.try_lock():
        if SingleInstance.signal_existing():
            return

    api = ConfigAPI()

    url = _ui_url()
    window = webview.create_window(
        APP_TITLE,
        url,
        width=980,
        height=520,
        resizable=False,
        frameless=True,
        easy_drag=False,
        js_api=api,
    )
    window_ref["window"] = window

    def on_loaded():
        try:
            window.evaluate_js("window.__iclickReloadMappings && window.__iclickReloadMappings()")
        except Exception:
            pass
        try:
            screen = webview.screens[0]
            x = max(0, int((screen.width - window.width) / 2))
            y = max(0, int((screen.height - window.height) / 2))
            window.move(x, y)
        except Exception:
            pass

    window.events.loaded += on_loaded

    webview.start(gui=None, debug=False, http_server=False)


if __name__ == "__main__":
    main()
