# from eye_tracking.gaze_tracker import get_gaze_coordinates, release
# from cursor_actions.functions import move_cursor
# from shortcuts_controller import GestureController
# from dotenv import load_dotenv
# import time

# controller = GestureController(show_debug=False, show_window=False)
# load_dotenv()

# try:
#     while True:
#         # If any audio pipeline is active, pause gestures/gaze.
#         if controller.is_stt_active() or controller.is_eleven_active():
#             time.sleep(0.01)
#             continue

#         gesture_active = controller.step()
#         if not gesture_active:
#             coords = get_gaze_coordinates()
#             if coords:
#                 x, y = coords
#                 move_cursor(x, y)
#         time.sleep(0.01)  # ~100 FPS max, prevents CPU meltdown
# except KeyboardInterrupt:
#     pass
# finally:
#     controller.close()
#     release()



from eye_tracking.gaze_tracker import get_gaze_coordinates, release
from eye_tracking.cursor_smoother import CursorSmoother
from cursor_actions.functions import move_cursor
from shortcuts_controller import GestureController
from dotenv import load_dotenv
import time

controller = GestureController(show_debug=False, show_window=False)
load_dotenv()

# Create cursor smoother
cursor_smoother = CursorSmoother(
    buffer_size=5,      # Average over 5 frames
    min_movement=5,     # Ignore movements < 5 pixels
    max_speed=120       # Max 120 pixels per frame
)

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
                # Apply cursor-level smoothing
                smooth_x, smooth_y = cursor_smoother.smooth(x, y)
                move_cursor(smooth_x, smooth_y)
        time.sleep(0.01)  # ~100 FPS max, prevents CPU meltdown
except KeyboardInterrupt:
    pass
finally:
    controller.close()
    release()