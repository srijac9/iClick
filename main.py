from eye_tracking.gaze_tracker import get_gaze_coordinates, release
from cursor_actions.functions import move_cursor, left_click, right_click
import time 

try:
    while True:
        coords = get_gaze_coordinates()
        if coords:
            x, y = coords
            move_cursor(x, y)
            time.sleep(0.01)  # ~100 FPS max, prevents CPU meltdown
except KeyboardInterrupt:
    pass
finally:
    release()