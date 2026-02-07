# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split
# from sklearn.ensemble import RandomForestRegressor
# from sklearn.metrics import mean_squared_error
# import joblib

# # Load calibration data
# df = pd.read_csv("eye_calibration.csv")

# # Features: eye ratios + eye width/height
# X = df[[
#     "left_ratio_x", "left_ratio_y", 
#     "right_ratio_x", "right_ratio_y",
#     "left_width", "left_height",
#     "right_width", "right_height"
# ]].values

# # X VALUES
# X_x = df[["left_ratio_x", 
#     "right_ratio_x"]].values

# # Target: screen coordinates
# y_x = df["screen_x"].values


# X_x_train, X_x_test, y_x_train, y_x_test = train_test_split(
#     X_x, y_x, test_size=0.2, random_state=42
# )

# # RANDOM FOREST
# # Train model
# model = RandomForestRegressor(n_estimators=200, random_state=42)
# model.fit(X_x_train, y_x_train)

# # Evaluate
# y_x_pred = model.predict(X_x_test)
# error = np.mean(np.linalg.norm(y_x_pred - y_x_test, axis=1))
# print(f"HEY Average pixel error: {error:.2f}")

# joblib.dump(model, "gaze_x_model.pkl")
# print("Model saved as gaze_x_model.pkl")



# # Y VALUES
# X_y = df[["left_ratio_y", 
#     "right_ratio_y"]].values

# # Target: screen coordinates
# y_y = df["screen_y"].values


# X_y_train, X_y_test, y_y_train, y_y_test = train_test_split(
#     X_y, y_y, test_size=0.2, random_state=42
# )

# # RANDOM FOREST
# # Train model
# model = RandomForestRegressor(n_estimators=200, random_state=42)
# model.fit(X_y_train, y_y_train)

# # Evaluate
# y_pred = model.predict(X_y_test)
# error = np.mean(np.linalg.norm(y_pred - y_y_test, axis=1))
# print(f"HEY Average pixel error: {error:.2f}")

# joblib.dump(model, "gaze_y_model.pkl")
# print("Model saved as gaze_y_model.pkl")




import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
from sklearn.linear_model import LinearRegression


# Load calibration data
df = pd.read_csv("eye_calibration_x.csv")

# --- X model ---
X_x = df[["left_ratio_x", "right_ratio_x"]].values
y_x = df["screen_x"].values  # 1D now

X_x_train, X_x_test, y_x_train, y_x_test = train_test_split(
    X_x, y_x, test_size=0.2, random_state=42
)

# model_x = RandomForestRegressor(n_estimators=200, random_state=42)
model_x = LinearRegression()
model_x.fit(X_x_train, y_x_train)

y_x_pred = model_x.predict(X_x_test)
error_x = np.mean(np.abs(y_x_pred - y_x_test))
print(f"X model average pixel error: {error_x:.2f}")

joblib.dump(model_x, "gaze_x_model.pkl")
print("X model saved as gaze_x_model.pkl")

df = pd.read_csv("eye_calibration_y.csv")

# --- Y model ---
X_y = df[["left_ratio_y", "right_ratio_y"]].values
y_y = df["screen_y"].values  # 1D now

X_y_train, X_y_test, y_y_train, y_y_test = train_test_split(
    X_y, y_y, test_size=0.2, random_state=42
)

# model_y = RandomForestRegressor(n_estimators=200, random_state=42)
model_y = LinearRegression()
model_y.fit(X_y_train, y_y_train)

y_y_pred = model_y.predict(X_y_test)
error_y = np.mean(np.abs(y_y_pred - y_y_test))
print(f"Y model average pixel error: {error_y:.2f}")

joblib.dump(model_y, "gaze_y_model.pkl")
print("Y model saved as gaze_y_model.pkl")
