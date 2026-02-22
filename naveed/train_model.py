import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
import joblib

# Load dataset
df = pd.read_csv("data.csv")

# Features
X = df[['strength',
        'weigth_capacity_kg',
        'biodegradability_score',
        'recyclability_percentage']]

# Targets
y_cost = df['cost_per_unit_inr']
y_co2 = df['co2_score']

# Split data
X_train, X_test, y_cost_train, y_cost_test = train_test_split(
    X, y_cost, test_size=0.2, random_state=42)

_, _, y_co2_train, y_co2_test = train_test_split(
    X, y_co2, test_size=0.2, random_state=42)

# Scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train Random Forest (Cost)
rf_cost = RandomForestRegressor(n_estimators=100, random_state=42)
rf_cost.fit(X_train_scaled, y_cost_train)

# Train XGBoost (CO2)
xgb_co2 = xgb.XGBRegressor()
xgb_co2.fit(X_train_scaled, y_co2_train)

# Save models
joblib.dump(rf_cost, "rf_cost_model.pkl")
joblib.dump(xgb_co2, "xgb_co2_model.pkl")
joblib.dump(scaler, "scaler.pkl")

print("Models saved successfully!")
