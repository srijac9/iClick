import joblib
import numpy as np
import os

# Load trained model
HERE = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(HERE, "gaze_model.pkl")

model_x = joblib.load(model_path)


SMOOTHING_WINDOW = 10
DEADZONE = 12
MAX_DELTA = 50
EYE_MOVE_THRESH_X = 0.02

# buffers/state for smoothing
last_x = None
last_eye_x = None

def predict_x(features):
    """
    Predicts X coordinate based on eye features.
    features: [left_ratio_x, right_ratio_x]
    """
    global last_x, last_eye_x

    current_eye_x = features[0] + features[1]

    # Ignore tiny movements
    if last_eye_x is not None and abs(current_eye_x - last_eye_x) < EYE_MOVE_THRESH_X:
        current_eye_x = None
    last_eye_x = features[0] + features[1]

    # Predict X
    if current_eye_x is not None:
        pred_x = model_x.predict([features])[0]
    else:
        pred_x = last_x

    # Clamp sudden jumps
    if last_x is not None:
        pred_x = np.clip(pred_x, last_x - MAX_DELTA, last_x + MAX_DELTA)

    # Deadzone
    if last_x is not None and abs(pred_x - last_x) < DEADZONE:
        pred_x = last_x

    last_x = pred_x
    return last_x
