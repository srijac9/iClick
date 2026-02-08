from eye_tracking.gaze_tracker import get_gaze_coordinates, release
from cursor_actions.functions import move_cursor
from shortcuts_controller import GestureController
from dotenv import load_dotenv
import subprocess
import sys
from pathlib import Path
import time

controller = GestureController(show_debug=False, show_window=False)
load_dotenv()
base_dir = Path(__file__).resolve().parent
config_app_path = base_dir / "desktop-pet" / "config_app.py"

calibration_steps = [
    [sys.executable, str(base_dir / "eye_tracking" / "x_dir" / "calibration.py")],
    [sys.executable, str(base_dir / "eye_tracking" / "x_dir" / "train.py")],
    [sys.executable, str(base_dir / "eye_tracking" / "y_dir" / "calibration.py")],
    [sys.executable, str(base_dir / "eye_tracking" / "y_dir" / "train.py")],
]

try:
    # Run calibration and training sequentially before anything else.
    for cmd in calibration_steps:
        if Path(cmd[1]).exists():
            subprocess.run(cmd, check=False)

    # Launch config UI once at startup (non-blocking) after calibration.
    if config_app_path.exists():
        try:
            subprocess.Popen([sys.executable, str(config_app_path)])
        except Exception:
            pass

    while True:
        # If any audio pipeline is active, pause gestures/gaze.
        if controller.is_stt_active() or controller.is_eleven_active():
            time.sleep(0.01)
            continue

        gesture_active = controller.step()
        if not gesture_active:
            coords = get_gaze_coordinates()
            if coords:
                x, y = coords
                move_cursor(x, y)
        time.sleep(0.01)  # ~100 FPS max, prevents CPU meltdown
except KeyboardInterrupt:
    pass
finally:
    controller.close()
    release()
