import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor

df = pd.read_csv("eye_calibration.csv")
# --- Y model ---
# X_y = df[["left_ratio_y", "right_ratio_y", "left_height", "right_height", "pitch"]].values
X_y = df[["left_ratio_y", "right_ratio_y", "left_height", "right_height"]].values

# X_y = df[["left_ratio_y", "right_ratio_y"]].values

y_y = df["screen_y"].values  

X_y_train, X_y_test, y_y_train, y_y_test = train_test_split(
    X_y, y_y, test_size=0.2, random_state=42
)
model_y = GradientBoostingRegressor(n_estimators=300, learning_rate=0.1, random_state=42)
#model_y = RandomForestRegressor(n_estimators=200, random_state=42)
# model_y = LinearRegression()
model_y.fit(X_y_train, y_y_train)

y_y_pred = model_y.predict(X_y_test)
error_y = np.mean(np.abs(y_y_pred - y_y_test))
print(f"Y model average pixel error: {error_y:.2f}")

joblib.dump(model_y, "gaze_model.pkl")
print("Y model saved as gaze_model.pkl")
