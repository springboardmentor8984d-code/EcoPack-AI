import pandas as pd
import os
import joblib
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
from sqlalchemy import text
from db_utils import get_db_engine

def train_models(models_dir):
    """
    Train ML models using data from the DB.
    """
    engine = get_db_engine()
    
    with engine.connect() as conn:
        df = pd.read_sql_query(text("SELECT * FROM materials_processed"), conn)

    if df.empty:
        print("Error: No data in materials_processed table.")
        return

    features = ['Strength_MPa', 'Weight_Capacity_kg', 'Biodegradability_Score', 'Recyclability_Percentage']
    X = df[features]
    y_cost = df['Cost_Per_Unit']
    y_co2 = df['CO2_Emission_Score']

    # Cost Model
    X_train, X_test, y_train, y_test = train_test_split(X, y_cost, test_size=0.2, random_state=42)
    cost_model = XGBRegressor(n_estimators=1000, learning_rate=0.01, random_state=42)
    cost_model.fit(X_train, y_train)
    y_pred_cost = cost_model.predict(X_test)

    # CO2 Model
    X_train_co2, X_test_co2, y_train_co2, y_test_co2 = train_test_split(X, y_co2, test_size=0.2, random_state=42)
    co2_model = XGBRegressor(n_estimators=1000, learning_rate=0.01, random_state=42)
    co2_model.fit(X_train_co2, y_train_co2)
    y_pred_co2 = co2_model.predict(X_test_co2)

    # Save
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        
    joblib.dump(cost_model, os.path.join(models_dir, 'cost_model.pkl'))
    joblib.dump(co2_model, os.path.join(models_dir, 'co2_model.pkl'))
    joblib.dump(features, os.path.join(models_dir, 'features.pkl'))
    
    metrics_file = os.path.join(os.path.dirname(models_dir), 'training_metrics.txt')
    with open(metrics_file, 'w') as f:
        f.write(f"Cost RMSE: {np.sqrt(mean_squared_error(y_test, y_pred_cost)):.4f}\n")
        f.write(f"CO2 RMSE: {np.sqrt(mean_squared_error(y_test_co2, y_pred_co2)):.4f}\n")

    print(f"Models saved. Metrics at: {metrics_file}")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    train_models(MODELS_DIR)
