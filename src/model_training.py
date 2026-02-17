import pandas as pd
import sqlite3
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder

def train_models(db_path, models_dir):
    """
    Train ML models for Cost and CO2 footprint prediction.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM materials_processed", conn)
    conn.close()

    if df.empty:
        print("Error: No data in materials_processed table.")
        return

    # Features: Strength, Weight_Capacity, Biodegradability, Recyclability
    features = ['Strength_MPa', 'Weight_Capacity_kg', 'Biodegradability_Score', 'Recyclability_Percentage']
    
    X = df[features]
    y_cost = df['Cost_Per_Unit']
    y_co2 = df['CO2_Emission_Score']

    # 1. Cost Prediction Model (XGBoost)
    X_train, X_test, y_train, y_test = train_test_split(X, y_cost, test_size=0.2, random_state=42)
    cost_model = XGBRegressor(n_estimators=1000, learning_rate=0.01, random_state=42)
    cost_model.fit(X_train, y_train)
    import numpy as np
    y_pred_cost = cost_model.predict(X_test)
    print("--- Cost Prediction Model (Random Forest) ---", flush=True)
    print(f"RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_cost)):.4f}", flush=True)
    print(f"MAE: {mean_absolute_error(y_test, y_pred_cost):.4f}", flush=True)
    print(f"R2 Score: {r2_score(y_test, y_pred_cost):.4f}", flush=True)

    # 2. CO2 Footprint Prediction Model (XGBoost)
    X_train_co2, X_test_co2, y_train_co2, y_test_co2 = train_test_split(X, y_co2, test_size=0.2, random_state=42)
    co2_model = XGBRegressor(n_estimators=1000, learning_rate=0.01, random_state=42)
    co2_model.fit(X_train_co2, y_train_co2)
    
    y_pred_co2 = co2_model.predict(X_test_co2)
    print("\n--- CO2 Footprint Prediction Model (XGBoost) ---", flush=True)
    print(f"RMSE: {np.sqrt(mean_squared_error(y_test_co2, y_pred_co2)):.4f}", flush=True)
    print(f"MAE: {mean_absolute_error(y_test_co2, y_pred_co2):.4f}", flush=True)
    print(f"R2 Score: {r2_score(y_test_co2, y_pred_co2):.4f}", flush=True)

    # Save models
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        
    joblib.dump(cost_model, os.path.join(models_dir, 'cost_model.pkl'))
    joblib.dump(co2_model, os.path.join(models_dir, 'co2_model.pkl'))
    joblib.dump(features, os.path.join(models_dir, 'features.pkl'))
    
    metrics_file = os.path.join(os.path.dirname(models_dir), 'training_metrics.txt')
    with open(metrics_file, 'w') as f:
        f.write("--- Cost Prediction Model (Random Forest) ---\n")
        f.write(f"RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_cost)):.4f}\n")
        f.write(f"MAE: {mean_absolute_error(y_test, y_pred_cost):.4f}\n")
        f.write(f"R2 Score: {r2_score(y_test, y_pred_cost):.4f}\n\n")
        
        f.write("--- CO2 Footprint Prediction Model (XGBoost) ---\n")
        f.write(f"RMSE: {np.sqrt(mean_squared_error(y_test_co2, y_pred_co2)):.4f}\n")
        f.write(f"MAE: {mean_absolute_error(y_test_co2, y_pred_co2):.4f}\n")
        f.write(f"R2 Score: {r2_score(y_test_co2, y_pred_co2):.4f}\n")

    print(f"\nModels and metrics saved. Metrics at: {metrics_file}")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_FILE = os.path.join(BASE_DIR, 'data', 'ecopack.db')
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    train_models(DB_FILE, MODELS_DIR)
