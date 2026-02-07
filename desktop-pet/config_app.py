import json
import os
import socket
import threading
import tkinter as tk
import ctypes
from tkinter import ttk, messagebox

APP_TITLE = "iClick Shortcut Config"
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")
CONFIG_PATH = os.path.join(CONFIG_DIR, "gesture_map.json")

LOCK_HOST = "127.0.0.1"
LOCK_PORT = 8767
MUTEX_NAME = "Global\\iClickShortcutConfigMutex"

DEFAULT_MAPPINGS = [
    {"gesture": "blink_twice", "action": "left_click", "args": {}},
    {"gesture": "hold", "action": "right_click", "args": {}},
    {"gesture": "open_palm", "action": "open_buddy", "args": {}},
    {"gesture": "wave", "action": "typing", "args": {}},
]

GESTURE_ROWS = ["blink_twice", "hold", "open_palm", "wave"]
ACTION_COLUMNS = ["open_buddy", "left_click", "right_click", "typing"]


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


def _load_action_map():
    data = load_config()
    action_map = {}
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
        # Prevent multiple binds on Windows.
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


class MappingDialog(tk.Toplevel):
    def __init__(self, parent, title, initial=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None

        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Gesture").grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))
        self.gesture_var = tk.StringVar(value=(initial or {}).get("gesture", ""))
        self.gesture_cb = ttk.Combobox(self, textvariable=self.gesture_var, values=KNOWN_GESTURES)
        self.gesture_cb.grid(row=0, column=1, sticky="ew", padx=12, pady=(12, 6))

        ttk.Label(self, text="Action").grid(row=1, column=0, sticky="w", padx=12, pady=6)
        self.action_var = tk.StringVar(value=(initial or {}).get("action", ""))
        self.action_cb = ttk.Combobox(self, textvariable=self.action_var, values=KNOWN_ACTIONS)
        self.action_cb.grid(row=1, column=1, sticky="ew", padx=12, pady=6)

        ttk.Label(self, text="Args (JSON)").grid(row=2, column=0, sticky="w", padx=12, pady=6)
        args = (initial or {}).get("args", {})
        self.args_var = tk.StringVar(value=json.dumps(args) if args else "")
        self.args_entry = ttk.Entry(self, textvariable=self.args_var)
        self.args_entry.grid(row=2, column=1, sticky="ew", padx=12, pady=6)

        btns = ttk.Frame(self)
        btns.grid(row=3, column=0, columnspan=2, sticky="e", padx=12, pady=12)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(btns, text="Save", command=self._on_save).pack(side="right", padx=(0, 8))

        self.bind("<Return>", lambda _e: self._on_save())
        self.bind("<Escape>", lambda _e: self.destroy())
        self.gesture_cb.focus_set()

    def _on_save(self):
        gesture = self.gesture_var.get().strip()
        action = self.action_var.get().strip()
        if not gesture or not action:
            messagebox.showwarning("Missing fields", "Gesture and Action are required.")
            return
        args_text = self.args_var.get().strip()
        args = {}
        if args_text:
            try:
                args = json.loads(args_text)
                if not isinstance(args, dict):
                    raise ValueError("Args must be a JSON object.")
            except Exception as exc:
                messagebox.showerror("Invalid Args", f"Args must be valid JSON object.\n{exc}")
                return
        self.result = {"gesture": gesture, "action": action, "args": args}
        self.destroy()


class ConfigApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        # Borderless window (no minimize/maximize/close).
        self.overrideredirect(True)
        self.geometry("720x420")
        self.minsize(680, 360)
        self._position_near_pet()

        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=12)
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Map gestures to actions", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Pick an action per gesture (optional).",
            foreground="#5f6368",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        grid = ttk.Frame(self)
        grid.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        for c in range(len(GESTURE_ROWS) + 1):
            grid.columnconfigure(c, weight=1)
        for r in range(1, len(ACTION_COLUMNS) + 1):
            grid.rowconfigure(r, weight=1)

        ttk.Label(grid, text="Gesture (defined)", font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w", padx=4, pady=(0, 8)
        )
        for col, gesture in enumerate(GESTURE_ROWS, start=1):
            label = gesture.replace("_", " ").title()
            ttk.Label(grid, text=label, font=("Segoe UI", 10, "bold")).grid(
                row=0, column=col, sticky="n", padx=4, pady=(0, 8)
            )

        current = _load_action_map()
        self.row_selection = {}
        self.cell_buttons = {}
        for row, action in enumerate(ACTION_COLUMNS, start=1):
            g_label = action.replace("_", " ").title()
            ttk.Label(grid, text=g_label, font=("Segoe UI", 10)).grid(
                row=row, column=0, sticky="w", padx=4, pady=6
            )
            self.cell_buttons[action] = {}
            selected = None
            for g, a in current.items():
                if a == action:
                    selected = g
                    break
            self.row_selection[action] = selected
            for col, gesture in enumerate(GESTURE_ROWS, start=1):
                btn = tk.Button(
                    grid,
                    text="Select",
                    width=10,
                    font=("Segoe UI", 10, "bold"),
                    relief="ridge",
                    borderwidth=2,
                    command=lambda a=action, g=gesture: self._select_action(a, g),
                )
                btn.grid(row=row, column=col, padx=4, pady=6, sticky="nsew")
                self.cell_buttons[action][gesture] = btn

        self._refresh_grid_styles()

        # No explicit save button; auto-save on close.

    def _save(self):
        try:
            mappings = []
            for action in ACTION_COLUMNS:
                gesture = self.row_selection.get(action)
                if gesture:
                    mappings.append({"gesture": gesture, "action": action, "args": {}})
            save_config(mappings)
            return True
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            return False

    def focus_app(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self._position_near_pet()

    def close_and_save(self):
        if self._save():
            self.destroy()

    def _position_near_pet(self):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = self.winfo_width()
        win_h = self.winfo_height()
        margin = 16
        x = max(margin, screen_w - win_w - margin)
        y = max(margin, screen_h - win_h - 220)
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")

    def _select_action(self, action, gesture):
        prev = self.row_selection.get(action)
        if prev == gesture:
            # Toggle off to unbind.
            self.row_selection[action] = None
            self._refresh_grid_styles()
            return

        # Enforce one selection per column (action).
        other_action = None
        for a, g in self.row_selection.items():
            if a != action and g == gesture:
                other_action = a
                break

        self.row_selection[action] = gesture

        if other_action:
            # Unbind previous owner so each action is unique.
            self.row_selection[other_action] = None

        self._refresh_grid_styles()

    def _refresh_grid_styles(self):
        for action in ACTION_COLUMNS:
            selected = self.row_selection.get(action)
            for gesture in GESTURE_ROWS:
                btn = self.cell_buttons[action][gesture]
                if gesture == selected:
                    btn.configure(
                        bg="#2d7dff",
                        fg="white",
                        activebackground="#1f66e0",
                        activeforeground="white",
                    )
                else:
                    btn.configure(
                        bg="#e7e7e7",
                        fg="black",
                        activebackground="#d9d9d9",
                        activeforeground="black",
                    )


def main():
    mutex = None
    if os.name == "nt":
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
        if ctypes.windll.kernel32.GetLastError() == 183:
            SingleInstance.signal_existing()
            return

    app = ConfigApp()

    def on_close():
        app.after(0, app.close_and_save)

    locker = SingleInstance(on_close)
    if not locker.try_lock():
        if SingleInstance.signal_existing():
            return

    app.mainloop()

    if mutex is not None:
        ctypes.windll.kernel32.ReleaseMutex(mutex)


if __name__ == "__main__":
    main()
