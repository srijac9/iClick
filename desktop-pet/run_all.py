import subprocess
import sys
import time
import socket
from pathlib import Path

# ======== EDIT THESE PATHS ========
BASE_DIR = Path(r"C:\Users\srich\iClick\desktop-pet")

WS_RELAY = BASE_DIR / "ws_relay.py"
APP_CONTROLLER = BASE_DIR / "app_controller.py"

PET_EXE = BASE_DIR / "desktop_pet.exe"
# =================================

HOST = "127.0.0.1"
PORT = 8765


def wait_for_port(host: str, port: int, timeout_s: float = 8.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def popen_py(script_path: Path, cwd: Path) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, str(script_path)],
        cwd=str(cwd),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )


def popen_exe(exe_path: Path, cwd: Path) -> subprocess.Popen:
    return subprocess.Popen(
        [str(exe_path)],
        cwd=str(cwd),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )


def main():
    subprocess.run(
        ["taskkill", "/IM", "desktop_pet.exe", "/F"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        st = PET_EXE.stat()
        print(f"[launcher] desktop_pet.exe mtime: {time.ctime(st.st_mtime)} size: {st.st_size}")
    except Exception as e:
        print(f"[launcher] desktop_pet.exe stat failed: {e}")

    print("[launcher] starting ws_relay.py")
    relay = popen_py(WS_RELAY, BASE_DIR)

    if not wait_for_port(HOST, PORT, 10):
        raise RuntimeError("Relay failed to start")

    print("[launcher] starting desktop_pet.exe")
    pet = popen_exe(PET_EXE, PET_EXE.parent)

    time.sleep(1.0)

    print("[launcher] starting app_controller.py")
    ctrl = popen_py(APP_CONTROLLER, BASE_DIR)

    print("[launcher] running — Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[launcher] shutting down")
        relay.terminate()
        pet.terminate()
        ctrl.terminate()


if __name__ == "__main__":
    main()
