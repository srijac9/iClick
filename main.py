from eye_tracking.gaze_tracker import get_gaze_coordinates, release
from cursor_actions.functions import move_cursor, left_click, right_click
from shortcuts_controller import GestureController
import time 

controller = GestureController(show_debug=False, show_window=False)

try:
    while True:
        gesture_active = controller.step()
        if not gesture_active:
            coords = get_gaze_coordinates()
            if coords:
                x, y = coords
                move_cursor(x, y)
                time.sleep(0.01)  # ~100 FPS max, prevents CPU meltdown
        else:
            time.sleep(0.01)
except KeyboardInterrupt:
    pass
finally:
    controller.close()
    release()
