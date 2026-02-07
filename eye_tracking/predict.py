import cv2
import mediapipe as mp
import pyautogui
import joblib
import numpy as np

from collections import deque

# Load trained model
model_x = joblib.load("gaze_x_model.pkl")
model_y = joblib.load("gaze_y_model.pkl")


SMOOTHING_WINDOW = 10
DEADZONE = 12
MAX_DELTA = 50

x_buffer = deque(maxlen=SMOOTHING_WINDOW)
last_x = None
last_eye_x = None

y_buffer = deque(maxlen=SMOOTHING_WINDOW)
last_y = None
last_eye_y = None

EYE_MOVE_THRESH_X = 0.02
EYE_MOVE_THRESH_Y = 0.015
# Mediapipe setup
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

def get_eye_features(landmarks, image_shape):
    # Use the same function as calibration
    # Returns a vector of length 8
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

    left_iris = lm_to_pixel(landmarks[LEFT_IRIS])
    left_inner = lm_to_pixel(landmarks[LEFT_INNER])
    left_outer = lm_to_pixel(landmarks[LEFT_OUTER])
    left_top = lm_to_pixel(landmarks[LEFT_TOP])
    left_bottom = lm_to_pixel(landmarks[LEFT_BOTTOM])
    left_width = np.linalg.norm(left_outer - left_inner)
    left_height = np.linalg.norm(left_top - left_bottom)
    left_ratio_x = (left_iris[0] - left_inner[0]) / left_width
    left_ratio_y = (left_iris[1] - left_top[1]) / left_height

    right_iris = lm_to_pixel(landmarks[RIGHT_IRIS])
    right_inner = lm_to_pixel(landmarks[RIGHT_INNER])
    right_outer = lm_to_pixel(landmarks[RIGHT_OUTER])
    right_top = lm_to_pixel(landmarks[RIGHT_TOP])
    right_bottom = lm_to_pixel(landmarks[RIGHT_BOTTOM])
    right_width = np.linalg.norm(right_outer - right_inner)
    right_height = np.linalg.norm(right_top - right_bottom)
    right_ratio_x = (right_iris[0] - right_inner[0]) / right_width
    right_ratio_y = (right_iris[1] - right_top[1]) / right_height

    return [left_ratio_x, left_ratio_y, right_ratio_x, right_ratio_y,
            left_width, left_height, right_width, right_height]

while True:
    ret, frame = cap.read()
    if not ret:
        continue
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)
    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark
        features = get_eye_features(landmarks, frame.shape)
        current_eye_x = features[0] + features[2]  # left + right
        current_eye_y = features[1] + features[3]  # left + right


        # if last_eye_x is not None:
        #     if abs(current_eye_x - last_eye_x) < EYE_MOVE_THRESH_X:
        #         # Eyes didn't really move → keep last_x
        #         current_eye_x = None
        # last_eye_x = features[0] + features[2]

        if last_eye_y is not None:
            if abs(current_eye_y - last_eye_y) < EYE_MOVE_THRESH_Y:
                current_eye_y = None
        last_eye_y = features[1] + features[3]
        
        # pred_x = model_x.predict([features])[0]
        # pred_y = model_y.predict([features])[0]
        pred_x = model_x.predict([[features[0], features[2]]])[0]  # left_ratio_x, right_ratio_x
        
        # inside loop
        # pred_x = model_x.predict([[features[0], features[2]]])[0]
        # x_buffer.append(pred_x)
        # smooth_x = np.mean(x_buffer)
        
        # if last_x is not None and abs(smooth_x - last_x) < DEADZONE:
        #     smooth_x = last_x
        if current_eye_x is not None:
            pred_x = model_x.predict([[features[0], features[2]]])[0]
        else:
            pred_x = last_x
        # 1️⃣ Clamp sudden jumps
        if last_x is not None:
            pred_x = np.clip(pred_x, last_x - MAX_DELTA, last_x + MAX_DELTA)

        # 2️⃣ Smooth
        # x_buffer.append(pred_x)
        # smooth_x = int(np.mean(x_buffer))
        smooth_x = pred_x
        # 3️⃣ Deadzone
        if last_x is not None and abs(smooth_x - last_x) < DEADZONE:
            smooth_x = last_x

        # 4️⃣ Update last_x (THIS WAS MISSING)
        last_x = smooth_x
        
        ## pred_y = model_y.predict([[features[1], features[3]]])[0]  # left_ratio_y, right_ratio_y
        # screen_height = pyautogui.size()[1]
        # pred_y = screen_height/2

        #NOT CHANGING Y FOR NOW
        if current_eye_y is not None:
            pred_y = model_y.predict([[features[1], features[3]]])[0]
        else:
            pred_y = last_y

        # Clamp sudden jumps
        if last_y is not None:
            pred_y = np.clip(pred_y, last_y - MAX_DELTA, last_y + MAX_DELTA)

        # Deadzone
        if last_y is not None and abs(pred_y - last_y) < DEADZONE:
            pred_y = last_y

        # Update last_y
        last_y = pred_y
        last_eye_y = features[1] + features[3]
        
        # Draw predicted gaze dot
        display_frame = np.zeros((pyautogui.size()[1], pyautogui.size()[0], 3), dtype=np.uint8)
        cv2.circle(display_frame, (int(last_x), int(last_y)), 15, (0, 255, 0), -1)
        cv2.imshow("Gaze Prediction", display_frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
