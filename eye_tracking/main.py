import cv2
import mediapipe as mp
import numpy as np
import pyautogui
from x_dir.predict import predict_x
from y_dir.predict import predict_y

SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

# Mediapipe setup
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

# Helper to get eye features
def get_eye_features(landmarks, image_shape):
    h, w, _ = image_shape
    LEFT_IRIS = 468
    RIGHT_IRIS = 473
    LEFT_INNER = 133
    LEFT_OUTER = 33
    LEFT_TOP = 159
    LEFT_BOTTOM = 145
    RIGHT_INNER = 362
    RIGHT_OUTER = 263
    RIGHT_TOP = 386
    RIGHT_BOTTOM = 374
    NOSE = 1

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
    left_ratio_y = (left_iris[1] - left_top[1]) / left_height

    # Right eye
    right_iris = lm_to_pixel(landmarks[RIGHT_IRIS])
    right_inner = lm_to_pixel(landmarks[RIGHT_INNER])
    right_outer = lm_to_pixel(landmarks[RIGHT_OUTER])
    right_top = lm_to_pixel(landmarks[RIGHT_TOP])
    right_bottom = lm_to_pixel(landmarks[RIGHT_BOTTOM])
    right_width = np.linalg.norm(right_outer - right_inner)
    right_height = np.linalg.norm(right_top - right_bottom)
    right_ratio_x = (right_iris[0] - right_inner[0]) / right_width
    right_ratio_y = (right_iris[1] - right_top[1]) / right_height

    eye_mid = (left_iris + right_iris) / 2
    nose = lm_to_pixel(landmarks[1])  # Nose tip
    
    pitch = eye_mid[1] - nose[1]  # vertical distance from nose to eye midpoint
    return [left_ratio_x, right_ratio_x, left_ratio_y, right_ratio_y, left_height, right_height, pitch]

# Create fullscreen window
cv2.namedWindow("Gaze Prediction", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Gaze Prediction", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            features = get_eye_features(landmarks, frame.shape)

            # Predict X
            features_x = [features[0], features[1]]
            x_coord = int(predict_x(features_x))
            # x_coord = SCREEN_WIDTH//2

            # Predict Y
            features_y = [features[2], features[3], features[4], features[5]]  # left_ratio_y, right_ratio_y, left_height, right_height, pitch
            y_coord = int(predict_y(features_y))
            # y_coord = SCREEN_HEIGHT//2
            
            # Draw dot
            display_frame = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)
            cv2.circle(display_frame, (x_coord, y_coord), 15, (0, 255, 0), -1)
            cv2.imshow("Gaze Prediction", display_frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
