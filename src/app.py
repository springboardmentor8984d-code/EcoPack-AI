from flask import Flask, request, jsonify, render_template
import pandas as pd
import sqlite3
import joblib
import os

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'ecopack.db')
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')

# Load models
cost_model = joblib.load(os.path.join(MODELS_DIR, 'cost_model.pkl'))
co2_model = joblib.load(os.path.join(MODELS_DIR, 'co2_model.pkl'))
features = joblib.load(os.path.join(MODELS_DIR, 'features.pkl'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/materials', methods=['GET'])
def get_materials():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM materials_processed", conn)
    conn.close()
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/recommend', methods=['POST'])
def recommend():
    data = request.json
    
    # Extract All Inputs
    strength_req = float(data.get('strength', 0))
    weight_req = float(data.get('weight_capacity', 0))
    category = data.get('product_category', 'food')
    fragility = data.get('fragility', 'medium')
    shipping = data.get('shipping_type', 'domestic')
    sustainability_priority = data.get('sustainability_priority', 'medium')
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM materials_processed", conn)
    conn.close()

    # --- 1. ACTION: FILTERING (Constraint Handling) ---
    # User-specified physical constraints
    df = df[df["Strength_MPa"] >= strength_req]
    df = df[df["Weight_Capacity_kg"] >= weight_req]

    if fragility == "high":
        # Keep only materials with high strength (Threshold: 30 MPa)
        df = df[df["Strength_MPa"] >= 30]
    
    if category == "food":
        # Keep only materials with high biodegradability (Threshold: 70)
        df = df[df["Biodegradability_Score"] >= 70]

    if df.empty:
        return jsonify({"recommended_materials": [], "message": "No materials meet the strict safety constraints."})

    # --- 2. ACTION: DYNAMIC WEIGHTING (User Priorities) ---
    # Default Weights
    eco_weight = 0.33
    cost_weight = 0.33
    strength_weight = 0.34

    if sustainability_priority == "high":
        eco_weight = 0.6
        cost_weight = 0.2
        strength_weight = 0.2
    
    if shipping == "international":
        # International shipping prioritizes CO2 reduction due to transport distance
        eco_weight += 0.1
        cost_weight -= 0.1

    # --- 3. ML-BASED PREDICTION & SCORING ---
    # Prepare features for ML models
    X = df[features]
    
    # Use ML models to get 'Predicted' values rather than just DB values
    df['predicted_cost'] = cost_model.predict(X)
    df['predicted_co2'] = co2_model.predict(X)

    # Normalize predicted values for fair scoring (0-1 range)
    def normalize(series, reverse=False):
        s_min, s_max = series.min(), series.max()
        if s_max == s_min: return series * 0
        norm = (series - s_min) / (s_max - s_min)
        return 1 - norm if reverse else norm

    # For Cost and CO2: Lower is better (reverse=True means low value gets high score)
    cost_score = normalize(df['predicted_cost'], reverse=True)
    co2_score = normalize(df['predicted_co2'], reverse=True)
    strength_score = normalize(df['Strength_MPa']) # Higher strength is better
    eco_core_score = (co2_score + normalize(df['Biodegradability_Score'])) / 2

    # Final Suitability Score Calculation
    df['suitability_score'] = (
        eco_weight * eco_core_score +
        cost_weight * cost_score +
        strength_weight * strength_score
    )
    
    # Bonus if the material's historical category matches user selection
    df.loc[df['Product_Category'] == category, 'suitability_score'] += 0.1

    # Sort and Format Output
    ranked = df.sort_values("suitability_score", ascending=False).head(5)
    
    output = {
        "recommended_materials": []
    }
    
    for _, row in ranked.iterrows():
        output["recommended_materials"].append({
            "material": row["Material_Type"],
            "predicted_cost": round(float(row["predicted_cost"]), 2),
            "predicted_co2": round(float(row["predicted_co2"]), 2),
            "suitability_score": round(float(row["suitability_score"]), 2),
            "strength": row["Strength_MPa"],
            "biodegradability": row["Biodegradability_Score"]
        })

    return jsonify(output)

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM materials_processed", conn)
    conn.close()
    
    # Simple aggregations for BI dashboard
    avg_co2 = df['CO2_Impact_Index'].mean()
    avg_cost = df['Cost_Per_Unit'].mean()
    
    # Data for charts
    mat_suitability = df.sort_values(by='Material_Suitability_Score', ascending=False)[['Material_Type', 'Material_Suitability_Score']].head(5).to_dict(orient='records')

    return jsonify({
        'avg_co2': avg_co2,
        'avg_cost': avg_cost,
        'top_materials': mat_suitability
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
