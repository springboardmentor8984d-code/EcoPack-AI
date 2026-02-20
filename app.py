import os
import joblib
import pandas as pd
import numpy as np
import csv
from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)

# --- Load Models & Data ---
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    rf_cost = joblib.load(os.path.join(MODEL_DIR, "cost_model.pkl"))
    xgb_co2 = joblib.load(os.path.join(MODEL_DIR, "co2_model.pkl"))
    scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
    # Load dataset to get material names and base properties for filtering
    df_base = pd.read_csv(os.path.join(MODEL_DIR, "ecopack_dataset_api_80.csv"))
    # Ensure correct column names from CSV (clean up if needed)
    df_base.columns = df_base.columns.str.strip()
except Exception as e:
    print(f"Error loading models or data: {e}")
    rf_cost = None
    xgb_co2 = None
    scaler = None
    df_base = None

# --- Calculate Global Stats for Normalization (Match Notebook Logic) ---
if df_base is not None:
    MIN_COST = df_base['cost_per_unit'].min()
    MAX_COST = df_base['cost_per_unit'].max()
    MIN_CO2 = df_base['co2_emission_score'].min()
    MAX_CO2 = df_base['co2_emission_score'].max()
    MIN_STRENGTH = df_base['strength_score'].min()
    MAX_STRENGTH = df_base['strength_score'].max()
else:
    MIN_COST = 0; MAX_COST = 5
    MIN_CO2 = 0; MAX_CO2 = 10
    MIN_STRENGTH = 0; MAX_STRENGTH = 100

# --- Logger Setup ---
USAGE_LOG_FILE = os.path.join(MODEL_DIR, "usage_log.csv")
if not os.path.exists(USAGE_LOG_FILE):
    with open(USAGE_LOG_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "material_name", "category", "shipping", "sustainability"])

def log_usage(material_name, category, shipping, sustainability):
    try:
        with open(USAGE_LOG_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), material_name, category, shipping, sustainability])
    except Exception as e:
        print(f"Logging error: {e}")

# --- Constants & Logic ---
FEATURES = [
    "strength_score",
    "weight_capacity_kg",
    "recyclability_percent",
    "biodegradability_score"
]

def predict_metrics(row):
    """Predict Cost and CO2 for a single row."""
    # Prepare input for Cost Model (Log Transformed Target)
    # The models expect a DataFrame with specific feature names
    input_data = pd.DataFrame([row], columns=FEATURES)
    
    # Cost Prediction
    cost_log_pred = rf_cost.predict(input_data)[0]
    cost_pred = np.expm1(cost_log_pred) # Inverse log1p

    # CO2 Prediction (Scaled Input)
    input_scaled = scaler.transform(input_data)
    co2_pred = xgb_co2.predict(input_scaled)[0]

    return round(cost_pred, 2), round(co2_pred, 2)

# --- Category Filtering Rules ---
# Mapping image values to dataset scale:
# Strength: x10 (e.g. 4 -> 40)
# Weight Capacity: Scaled to fit 5-25kg (e.g. 50 -> 15, 60 -> 18, 70 -> 21, 80 -> 24)
CATEGORY_RULES = {
    "Food": lambda df: df[
        (df["biodegradability_score"] >= 8) & 
        (df["recyclability_percent"] >= 60)
    ],
    "Electronics": lambda df: df[
        (df["strength_score"] >= 40) & 
        (df["weight_capacity_kg"] >= 15) & 
        (df["recyclability_percent"] >= 50)
    ],
    "Cosmetics": lambda df: df[
        (df["recyclability_percent"] >= 85) & 
        (df["biodegradability_score"] >= 6)
    ],
    "Pharmaceuticals": lambda df: df[
        (df["biodegradability_score"] >= 7) & 
        (df["strength_score"] >= 30)
    ],
    "Fragile Goods": lambda df: df[
        (df["strength_score"] >= 40) & 
        (df["weight_capacity_kg"] >= 18)
    ],
    "Textiles": lambda df: df[
        (df["recyclability_percent"] >= 80)
    ],
    "Furniture": lambda df: df[
        (df["strength_score"] >= 50) & 
        (df["weight_capacity_kg"] >= 21)
    ],
    "Industrial Parts": lambda df: df[
        (df["strength_score"] >= 50) & 
        (df["weight_capacity_kg"] >= 24) & 
        (df["recyclability_percent"] >= 55)
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    if df_base is None or rf_cost is None:
        return jsonify({"error": "Models or data not loaded"}), 500

    try:
        data = request.json
        product_category = data.get('product_category')
        fragility = data.get('fragility', 'Medium')
        data = request.json
        product_category = data.get('product_category')
        fragility = data.get('fragility', 'Medium')
        shipping_type = data.get('shipping_type', 'Domestic')
        sustainability_priority = data.get('sustainability_priority', 'Medium')

        # --- 1. Filter Materials ---
        # Logic: Filter based on Category Rules FIRST
        filtered_df = df_base.copy()

        # Normalize category name matching (case-insensitive key lookup)
        rule_func = None
        for key in CATEGORY_RULES:
            if key.lower() == product_category.lower():
                rule_func = CATEGORY_RULES[key]
                break
        
        if rule_func:
            filtered_df = rule_func(filtered_df)

        # Logic: Filter based on Fragility constraints (Additional layer)
        
        if fragility == 'High':
            filtered_df = filtered_df[filtered_df['strength_score'] > 60]
        elif fragility == 'Medium':
            filtered_df = filtered_df[filtered_df['strength_score'] >45]
        # Low fragility: keep everything (or minimal threshold)

        if filtered_df.empty:
            return jsonify({"error": "No suitable materials found for these criteria."}), 404

        # --- 2. Predict & Score ---
        results = []
        for _, row in filtered_df.iterrows():
            # Extract features for prediction
            features = {
                "strength_score": row['strength_score'],
                "weight_capacity_kg": row['weight_capacity_kg'],
                "recyclability_percent": row['recyclability_percent'],
                "biodegradability_score": row['biodegradability_score']
            }
            
            # Get Predictions
            pred_cost, pred_co2 = predict_metrics(features)

            # --- 3. Ranking Logic (Weighted Score) ---
            # Weights depend on user inputs
            w_cost = 0.4
            w_co2 = 0.4
            w_suitability = 0.2

            if shipping_type == 'International':
                w_cost -= 0.1
                w_co2 += 0.1 # Higher importance on CO2/Durability implicitly
            
            if sustainability_priority == 'High':
                w_co2 += 0.2
                w_cost -= 0.1
                w_suitability -= 0.1
            elif sustainability_priority == 'Low':
                w_cost += 0.2
                w_co2 -= 0.2
            
            # Normalize (Dynamic Min/Max from loaded dataset)
            # Cost & CO2: Lower is better -> 1 - normalized_val
            cost_norm = 1 - ((max(min(pred_cost, MAX_COST), MIN_COST) - MIN_COST) / (MAX_COST - MIN_COST))
            co2_norm = 1 - ((max(min(pred_co2, MAX_CO2), MIN_CO2) - MIN_CO2) / (MAX_CO2 - MIN_CO2))
            
            # Strength: Higher is better -> normalized_val
            strength_norm = (features['strength_score'] - MIN_STRENGTH) / (MAX_STRENGTH - MIN_STRENGTH)

            # Suitability Score (Matches Notebook: 0.5*Strength + 0.3*Recycle + 0.2*Bio)
            suitability_score = (
                0.4 * strength_norm +
                0.3 * (features['recyclability_percent'] / 100) +
                0.3 * (features['biodegradability_score'] / 10)
            )

            poly_score = (w_cost * cost_norm) + (w_co2 * co2_norm) + (w_suitability * suitability_score)

            results.append({
                "material_name": row['material_Name'],
                "rank_score": float(round(poly_score, 3)),
                "predicted_cost": float(pred_cost),
                "predicted_co2": float(pred_co2),
                "suitability_score": float(round(suitability_score * 100, 1)),
                "strength": float(row['strength_score']),
                "recyclability": float(row['recyclability_percent'])
            })

        # Calculate Baseline (Average of 'plastic' if available, else overall average)
        # simplistic baseline for demo
        baseline_cost = 1.0 # default if no plastic
        baseline_co2 = 8.0
        
        try:
            plastic_df = df_base[df_base['material_Name'].str.contains('plastic', case=False, na=False)]
            if not plastic_df.empty:
                # We need predicted values for plastic, but we can't easily predict for 'generic plastic' 
                # without specific weight/strength.
                # Let's use the average 'cost_per_unit' & 'co2_emission_score' from the CSV as a rough baseline proxy
                # This is an approximation since models predict specific values.
                baseline_cost = plastic_df['cost_per_unit'].mean()
                baseline_co2 = plastic_df['co2_emission_score'].mean()
        except:
            pass

        # Sort by Rank Score (Descending)
        results = sorted(results, key=lambda x: x['rank_score'], reverse=True)
        
        # Log the top recommendation
        if results:
            log_usage(results[0]['material_name'], product_category, shipping_type, sustainability_priority)

        # Return Top 5 + Baseline info
        return jsonify({
            "recommendations": results[:5],
            "baseline": {
                "cost": round(baseline_cost, 2),
                "co2": round(baseline_co2, 2)
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/usage')
def get_usage():
    if not os.path.exists(USAGE_LOG_FILE):
        return jsonify({})
    
    try:
        df_log = pd.read_csv(USAGE_LOG_FILE)
        # Count occurrences of each material
        usage_counts = df_log['material_name'].value_counts().to_dict()
        return jsonify(usage_counts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
