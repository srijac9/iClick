# import joblib
# import numpy as np
# import os

# # Load trained model
# HERE = os.path.dirname(os.path.abspath(__file__))
# model_path = os.path.join(HERE, "gaze_model.pkl")

# model_x = joblib.load(model_path)


# SMOOTHING_WINDOW = 10
# DEADZONE = 12
# MAX_DELTA = 50
# EYE_MOVE_THRESH_X = 0.02

# # buffers/state for smoothing
# last_x = None
# last_eye_x = None

# def predict_x(features):
#     """
#     Predicts X coordinate based on eye features.
#     features: [left_ratio_x, right_ratio_x]
#     """
#     global last_x, last_eye_x

#     current_eye_x = features[0] + features[1]

#     # Ignore tiny movements
#     if last_eye_x is not None and abs(current_eye_x - last_eye_x) < EYE_MOVE_THRESH_X:
#         current_eye_x = None
#     last_eye_x = features[0] + features[1]

#     # Predict X
#     if current_eye_x is not None:
#         pred_x = model_x.predict([features])[0]
#     else:
#         pred_x = last_x

#     # Clamp sudden jumps
#     if last_x is not None:
#         pred_x = np.clip(pred_x, last_x - MAX_DELTA, last_x + MAX_DELTA)

#     # Deadzone
#     if last_x is not None and abs(pred_x - last_x) < DEADZONE:
#         pred_x = last_x

#     last_x = pred_x
#     return last_x















import joblib
import numpy as np
from collections import deque
import os

HERE = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(HERE, "gaze_model.pkl")

model_x = joblib.load(model_path)

class GazeSmootherX:
    def __init__(self, buffer_size=5, movement_threshold=0.01):
        self.buffer = deque(maxlen=buffer_size)
        self.last_pred = None
        self.last_features = None
        self.movement_threshold = movement_threshold
        
    def smooth(self, features, raw_prediction):
        # Detect if eyes actually moved
        if self.last_features is not None:
            # Compare horizontal eye ratios
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
            max_jump = 100  # Slightly larger for horizontal movement
            smoothed = np.clip(smoothed, 
                              self.last_pred - max_jump, 
                              self.last_pred + max_jump)
        
        self.last_pred = smoothed
        return smoothed

smoother = GazeSmootherX(buffer_size=5, movement_threshold=0.008)

def predict_x(features):
    """
    features: [left_ratio_x, right_ratio_x, avg_ratio_x, avg_width, normalized_x]
    """
    raw_pred = model_x.predict([features])[0]
    smoothed_pred = smoother.smooth(features, raw_pred)
    return smoothed_pred