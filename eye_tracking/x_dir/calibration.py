# import cv2
# import mediapipe as mp
# import numpy as np
# import pandas as pd
# import time
# import pyautogui

# # -------------------------------
# # Mediapipe setup
# # -------------------------------
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(
#     max_num_faces=1,
#     refine_landmarks=True,  # important for iris landmarks
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5
# )

# # -------------------------------
# # Screen settings
# # -------------------------------
# # SCREEN_WIDTH, SCREEN_HEIGHT = 2940, 1912
# SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
# print(SCREEN_HEIGHT, SCREEN_WIDTH)
# DOT_RADIUS = 10
# GRID_ROWS_X = 3
# GRID_COLS_X = 24
# DOT_PAUSE = 0.5  # seconds to pause on each dot
# FRAMES_PER_POINT = 2

# # -------------------------------
# # Helper functions
# # -------------------------------
# def get_eye_features(landmarks, image_shape):
#     h, w, _ = image_shape
#     # Landmarks indices for iris
#     LEFT_IRIS = 468
#     RIGHT_IRIS = 473
#     # Eye corners for normalization
#     LEFT_INNER = 133
#     LEFT_OUTER = 33
#     RIGHT_INNER = 362
#     RIGHT_OUTER = 263
#     # Upper/lower eyelid (left)
#     LEFT_TOP = 159
#     LEFT_BOTTOM = 145
#     # Upper/lower eyelid (right)
#     RIGHT_TOP = 386
#     RIGHT_BOTTOM = 374
#     NOSE = 1

#     def lm_to_pixel(lm):
#         return np.array([lm.x * w, lm.y * h])

#     # Left eye
#     left_iris = lm_to_pixel(landmarks[LEFT_IRIS])
#     left_inner = lm_to_pixel(landmarks[LEFT_INNER])
#     left_outer = lm_to_pixel(landmarks[LEFT_OUTER])
#     left_top = lm_to_pixel(landmarks[LEFT_TOP])
#     left_bottom = lm_to_pixel(landmarks[LEFT_BOTTOM])
#     left_width = np.linalg.norm(left_outer - left_inner)
#     left_height = np.linalg.norm(left_top - left_bottom)
#     left_ratio_x = (left_iris[0] - left_inner[0]) / left_width
#     left_ratio_y = (left_iris[1] - left_top[1]) / left_height

#     # Right eye
#     right_iris = lm_to_pixel(landmarks[RIGHT_IRIS])
#     right_inner = lm_to_pixel(landmarks[RIGHT_INNER])
#     right_outer = lm_to_pixel(landmarks[RIGHT_OUTER])
#     right_top = lm_to_pixel(landmarks[RIGHT_TOP])
#     right_bottom = lm_to_pixel(landmarks[RIGHT_BOTTOM])
#     right_width = np.linalg.norm(right_outer - right_inner)
#     right_height = np.linalg.norm(right_top - right_bottom)
#     right_ratio_x = (right_iris[0] - right_inner[0]) / right_width
#     right_ratio_y = (right_iris[1] - right_top[1]) / right_height
    
#     eye_mid = (left_iris + right_iris) / 2
#     nose = lm_to_pixel(landmarks[NOSE])
#     pitch = eye_mid[1] - nose[1]  # vertical distance from nose to eye midpoint
    
#     # Feature vector
#     features = [
#         left_ratio_x, left_ratio_y,
#         right_ratio_x, right_ratio_y,
#         left_width, left_height,
#         right_width, right_height, 
#         pitch
#     ]
#     return features

# # -------------------------------
# # Calibration grid points
# # -------------------------------
# def generate_grid(rows, cols, screen_width, screen_height):
#     xs = np.linspace(20, screen_width-20, cols)
#     ys = np.linspace(20, screen_height-20, rows)
#     grid = [(int(x), int(y)) for y in ys for x in xs]
#     return grid

# grid_points_x = generate_grid(GRID_ROWS_X, GRID_COLS_X, SCREEN_WIDTH, SCREEN_HEIGHT)

# # -------------------------------
# # Calibration loop
# # -------------------------------
# #dataset = []
# dataset_x = []
# cap = cv2.VideoCapture(0)

# cv2.namedWindow("Calibration Dot", cv2.WINDOW_NORMAL)
# cv2.setWindowProperty("Calibration Dot", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)


# try:
#     for point in grid_points_x:
#         x, y = point
#         print(f"Look at dot at {point}")
#         start_time = time.time()
#         while time.time() - start_time < DOT_PAUSE:
#             ret, frame = cap.read()
#             if not ret:
#                 continue
#             frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             results = face_mesh.process(frame_rgb)
#             if results.multi_face_landmarks:
#                 landmarks = results.multi_face_landmarks[0].landmark
#                 features = get_eye_features(landmarks, frame.shape)
                
#                 dataset_x.append(features + [x, y])

#             # Display the dot on screen
#             display_frame = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)
#             cv2.circle(display_frame, (x, y), DOT_RADIUS, (0, 0, 255), -1)
#             cv2.imshow("Calibration Dot", display_frame)
            
#             if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
#                 raise KeyboardInterrupt        
            
# finally:
#     cap.release()
#     cv2.destroyAllWindows()

# # -------------------------------
# # Save dataset
# # -------------------------------
# columns = [
#     "left_ratio_x", "left_ratio_y", "right_ratio_x", "right_ratio_y",
#     "left_width", "left_height", "right_width", "right_height","pitch",
#     "screen_x", "screen_y"
# ]
# df = pd.DataFrame(dataset_x, columns=columns)
# df.to_csv("eye_calibration.csv", index=False)
# print("Calibration data saved to eye_calibration.csv")



import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import time
import pyautogui

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
DOT_RADIUS = 15
GRID_ROWS_X = 5  # Fewer rows for X calibration
GRID_COLS_X = 9  # More columns for horizontal movement
DOT_PAUSE = 1.5
WARMUP_FRAMES = 10

def get_eye_features(landmarks, image_shape):
    h, w, _ = image_shape
    LEFT_IRIS = 468
    RIGHT_IRIS = 473
    LEFT_INNER = 133
    LEFT_OUTER = 33
    RIGHT_INNER = 362
    RIGHT_OUTER = 263
    LEFT_TOP = 159
    LEFT_BOTTOM = 145
    RIGHT_TOP = 386
    RIGHT_BOTTOM = 374

    def lm_to_pixel(lm):
        return np.array([lm.x * w, lm.y * h])

    # Left eye
    left_iris = lm_to_pixel(landmarks[LEFT_IRIS])
    left_inner = lm_to_pixel(landmarks[LEFT_INNER])
    left_outer = lm_to_pixel(landmarks[LEFT_OUTER])
    left_top = lm_to_pixel(landmarks[LEFT_TOP])
    left_bottom = lm_to_pixel(landmarks[LEFT_BOTTOM])
    left_width = np.linalg.norm(left_outer - left_inner)
    left_height = np.linalg.norm(left_top - left_bottom)
    left_ratio_x = (left_iris[0] - left_inner[0]) / left_width

    # Right eye
    right_iris = lm_to_pixel(landmarks[RIGHT_IRIS])
    right_inner = lm_to_pixel(landmarks[RIGHT_INNER])
    right_outer = lm_to_pixel(landmarks[RIGHT_OUTER])
    right_top = lm_to_pixel(landmarks[RIGHT_TOP])
    right_bottom = lm_to_pixel(landmarks[RIGHT_BOTTOM])
    right_width = np.linalg.norm(right_outer - right_inner)
    right_height = np.linalg.norm(right_top - right_bottom)
    right_ratio_x = (right_iris[0] - right_inner[0]) / right_width

    # Average ratios for stability
    avg_ratio_x = (left_ratio_x + right_ratio_x) / 2
    avg_width = (left_width + right_width) / 2
    
    # Head yaw compensation (horizontal distance between eyes)
    eye_distance = np.linalg.norm(left_iris - right_iris)
    eye_center_x = (left_iris[0] + right_iris[0]) / 2
    normalized_x = eye_center_x / w

    return [left_ratio_x, right_ratio_x, avg_ratio_x, avg_width, eye_distance, normalized_x]

def generate_grid(rows, cols, screen_width, screen_height):
    margin = 50
    xs = np.linspace(margin, screen_width - margin, cols)
    ys = np.linspace(margin, screen_height - margin, rows)
    return [(int(x), int(y)) for y in ys for x in xs]

grid_points_x = generate_grid(GRID_ROWS_X, GRID_COLS_X, SCREEN_WIDTH, SCREEN_HEIGHT)
dataset_x = []
cap = cv2.VideoCapture(0)

cv2.namedWindow("Calibration", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Calibration", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

try:
    for idx, point in enumerate(grid_points_x):
        x, y = point
        print(f"Point {idx + 1}/{len(grid_points_x)}: {point}")
        
        start_time = time.time()
        frame_count = 0
        point_samples = []
        
        while time.time() - start_time < DOT_PAUSE:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame_count += 1
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(frame_rgb)
            
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark
                features = get_eye_features(landmarks, frame.shape)
                
                if frame_count > WARMUP_FRAMES:
                    point_samples.append(features + [x, y])

            # Display
            display_frame = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)
            cv2.circle(display_frame, (x, y), DOT_RADIUS, (255, 255, 0), -1)
            
            progress = int((time.time() - start_time) / DOT_PAUSE * 100)
            cv2.putText(display_frame, f"{progress}%", (x - 30, y + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow("Calibration", display_frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                raise KeyboardInterrupt
        
        dataset_x.extend(point_samples)

finally:
    cap.release()
    cv2.destroyAllWindows()

columns = [
    "left_ratio_x", "right_ratio_x", "avg_ratio_x",
    "avg_width", "eye_distance", "normalized_x",
    "screen_x", "screen_y"
]
df = pd.DataFrame(dataset_x, columns=columns)
df.to_csv("eye_calibration.csv", index=False)
print(f"Saved {len(df)} calibration samples to eye_calibration.csv")