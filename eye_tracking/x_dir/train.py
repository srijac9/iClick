# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# from sklearn.ensemble import RandomForestRegressor
# import joblib
# from sklearn.linear_model import LinearRegression


# # Load calibration data
# df = pd.read_csv("eye_calibration.csv")

# # --- X model ---
# X_x = df[["left_ratio_x", "right_ratio_x"]].values
# y_x = df["screen_x"].values  # 1D now

# X_x_train, X_x_test, y_x_train, y_x_test = train_test_split(
#     X_x, y_x, test_size=0.2, random_state=42
# )

# # model_x = RandomForestRegressor(n_estimators=200, random_state=42)
# model_x = LinearRegression()
# model_x.fit(X_x_train, y_x_train)

# y_x_pred = model_x.predict(X_x_test)
# error_x = np.mean(np.abs(y_x_pred - y_x_test))
# print(f"X model average pixel error: {error_x:.2f}")

# joblib.dump(model_x, "gaze_model.pkl")
# print("X model saved as gaze_model.pkl")



import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor
import joblib

df = pd.read_csv("eye_calibration.csv")

# Use consistent features
X_x = df[["left_ratio_x", "right_ratio_x", "avg_ratio_x", "avg_width", "normalized_x"]].values
y_x = df["screen_x"].values

X_train, X_test, y_train, y_test = train_test_split(
    X_x, y_x, test_size=0.2, random_state=42
)

# Optimized model
model_x = GradientBoostingRegressor(
    n_estimators=200,
    learning_rate=0.1,
    max_depth=5,
    min_samples_split=5,
    random_state=42
)
model_x.fit(X_train, y_train)

y_pred = model_x.predict(X_test)
error = np.mean(np.abs(y_pred - y_test))
print(f"X model average pixel error: {error:.2f}")

# Error distribution
percentiles = [50, 75, 90, 95]
errors = np.abs(y_pred - y_test)
for p in percentiles:
    print(f"{p}th percentile error: {np.percentile(errors, p):.2f} pixels")

joblib.dump(model_x, "gaze_model.pkl")
print("Model saved as gaze_model.pkl")