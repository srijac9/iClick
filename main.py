from eye_tracking.gaze_tracker import get_gaze_coordinates, release
from cursor_actions.functions import move_cursor
from shortcuts_controller import GestureController
from dotenv import load_dotenv
import time

controller = GestureController(show_debug=False, show_window=False)
load_dotenv()

try:
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
