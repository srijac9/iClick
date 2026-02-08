# import joblib
# import numpy as np
# import os

# # Load trained Y model
# HERE = os.path.dirname(os.path.abspath(__file__))
# model_path = os.path.join(HERE, "gaze_model.pkl")

# model_y = joblib.load(model_path)

# # Smoothing & thresholds
# SMOOTHING_WINDOW = 10
# DEADZONE = 30
# MAX_DELTA = 50
# EYE_MOVE_THRESH_Y = 0.015

# # Buffers / state
# last_y = None
# last_eye_y = None

# def predict_y(features):
#     """
#     Predicts Y coordinate based on eye features.
#     features: [left_ratio_y, right_ratio_y]
#     """
#     global last_y, last_eye_y
    
    
#     pred_y = model_y.predict([features])[0]

#     current_eye_y = features[0] + features[1]

#     # Ignore tiny movements
#     if last_eye_y is not None and abs(current_eye_y - last_eye_y) < EYE_MOVE_THRESH_Y:
#         current_eye_y = None
#     last_eye_y = features[0] + features[1]
    
#     # Predict Y
#     if current_eye_y is not None:
#         pred_y = model_y.predict([features])[0]
#     else:
#         pred_y = last_y

#     # Clamp sudden jumps
#     if last_y is not None:
#         pred_y = np.clip(pred_y, last_y - MAX_DELTA, last_y + MAX_DELTA)

#     # Deadzone
#     if last_y is not None and abs(pred_y - last_y) < DEADZONE:
#         pred_y = last_y

#     last_y = pred_y
#     return last_y


import joblib
import numpy as np
from collections import deque
import os

HERE = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(HERE, "gaze_model.pkl")

model_y = joblib.load(model_path)

# Improved smoothing
class GazeSmootherY:
    def __init__(self, buffer_size=5, movement_threshold=0.01):
        self.buffer = deque(maxlen=buffer_size)
        self.last_pred = None
        self.last_features = None
        self.movement_threshold = movement_threshold
        
    def smooth(self, features, raw_prediction):
        # Detect if eyes actually moved
        if self.last_features is not None:
            feature_delta = np.abs(np.array(features[:2]) - np.array(self.last_features[:2])).mean()
            
            if feature_delta < self.movement_threshold:
                # Eyes didn't move significantly, return last position
                return self.last_pred if self.last_pred is not None else raw_prediction
        
        self.last_features = features
        
        # Add to buffer and smooth
        self.buffer.append(raw_prediction)
        
        # Weighted average (more recent = higher weight)
        weights = np.exp(np.linspace(0, 1, len(self.buffer)))
        smoothed = np.average(list(self.buffer), weights=weights)
        
        # Limit jump size
        if self.last_pred is not None:
            max_jump = 80
            smoothed = np.clip(smoothed, 
                              self.last_pred - max_jump, 
                              self.last_pred + max_jump)
        
        self.last_pred = smoothed
        return smoothed

smoother = GazeSmootherY(buffer_size=5, movement_threshold=0.008)

def predict_y(features):
    """
    features: [left_ratio_y, right_ratio_y, avg_ratio_y, avg_height, normalized_y]
    """
    raw_pred = model_y.predict([features])[0]
    smoothed_pred = smoother.smooth(features, raw_pred)
    return smoothed_pred