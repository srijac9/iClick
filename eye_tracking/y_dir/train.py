# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# from sklearn.ensemble import RandomForestRegressor
# import joblib
# from sklearn.linear_model import LinearRegression
# from sklearn.ensemble import GradientBoostingRegressor

# df = pd.read_csv("eye_calibration.csv")
# # --- Y model ---
# # X_y = df[["left_ratio_y", "right_ratio_y", "left_height", "right_height", "pitch"]].values
# X_y = df[["left_ratio_y", "right_ratio_y", "left_height", "right_height"]].values

# # X_y = df[["left_ratio_y", "right_ratio_y"]].values

# y_y = df["screen_y"].values  

# X_y_train, X_y_test, y_y_train, y_y_test = train_test_split(
#     X_y, y_y, test_size=0.2, random_state=42
# )
# model_y = GradientBoostingRegressor(n_estimators=300, learning_rate=0.1, random_state=42)
# #model_y = RandomForestRegressor(n_estimators=200, random_state=42)
# # model_y = LinearRegression()
# model_y.fit(X_y_train, y_y_train)

# y_y_pred = model_y.predict(X_y_test)
# error_y = np.mean(np.abs(y_y_pred - y_y_test))
# print(f"Y model average pixel error: {error_y:.2f}")

# joblib.dump(model_y, "gaze_model.pkl")
# print("Y model saved as gaze_model.pkl")

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
import joblib

df = pd.read_csv("eye_calibration.csv")

# Use consistent features
X_y = df[["left_ratio_y", "right_ratio_y", "avg_ratio_y", "avg_height", "normalized_y"]].values
y_y = df["screen_y"].values

X_train, X_test, y_train, y_test = train_test_split(
    X_y, y_y, test_size=0.2, random_state=42
)

# Optimized model
model_y = GradientBoostingRegressor(
    n_estimators=200,
    learning_rate=0.1,
    max_depth=5,
    min_samples_split=5,
    random_state=42
)
model_y.fit(X_train, y_train)

y_pred = model_y.predict(X_test)
error = np.mean(np.abs(y_pred - y_test))
print(f"Y model average pixel error: {error:.2f}")

# Error distribution
percentiles = [50, 75, 90, 95]
errors = np.abs(y_pred - y_test)
for p in percentiles:
    print(f"{p}th percentile error: {np.percentile(errors, p):.2f} pixels")

joblib.dump(model_y, "gaze_model.pkl")
print("Model saved as gaze_model.pkl")