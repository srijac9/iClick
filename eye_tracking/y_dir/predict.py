import joblib
import numpy as np
import os

# Load trained Y model
HERE = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(HERE, "gaze_model.pkl")

model_y = joblib.load(model_path)

# Smoothing & thresholds
SMOOTHING_WINDOW = 10
DEADZONE = 30
MAX_DELTA = 50
EYE_MOVE_THRESH_Y = 0.015

# Buffers / state
last_y = None
last_eye_y = None

def predict_y(features):
    """
    Predicts Y coordinate based on eye features.
    features: [left_ratio_y, right_ratio_y]
    """
    global last_y, last_eye_y
    
    
    pred_y = model_y.predict([features])[0]

    current_eye_y = features[0] + features[1]

    # Ignore tiny movements
    if last_eye_y is not None and abs(current_eye_y - last_eye_y) < EYE_MOVE_THRESH_Y:
        current_eye_y = None
    last_eye_y = features[0] + features[1]
    
    # Predict Y
    if current_eye_y is not None:
        pred_y = model_y.predict([features])[0]
    else:
        pred_y = last_y

    # Clamp sudden jumps
    if last_y is not None:
        pred_y = np.clip(pred_y, last_y - MAX_DELTA, last_y + MAX_DELTA)

    # Deadzone
    if last_y is not None and abs(pred_y - last_y) < DEADZONE:
        pred_y = last_y

    last_y = pred_y
    return last_y
