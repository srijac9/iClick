import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
from sklearn.linear_model import LinearRegression


# Load calibration data
df = pd.read_csv("eye_calibration.csv")

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

joblib.dump(model_x, "gaze_model.pkl")
print("X model saved as gaze_model.pkl")
