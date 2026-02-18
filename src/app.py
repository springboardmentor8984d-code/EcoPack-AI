from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
import numpy as np
import onnxruntime as ort
import sqlite3

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'ecopack.db')
MODELS_DIR = os.path.join(BASE_DIR, '..', 'models')

# Load models (ONNX) - Lightweight for Vercel
try:
    cost_session = ort.InferenceSession(os.path.join(MODELS_DIR, 'cost_model.onnx'))
    co2_session = ort.InferenceSession(os.path.join(MODELS_DIR, 'co2_model.onnx'))
except Exception as e:
    print(f"Error loading ONNX models: {e}")
    cost_session = None
    co2_session = None

# Hardcoded features
features = ['Strength_MPa', 'Weight_Capacity_kg', 'Biodegradability_Score', 'Recyclability_Percentage']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/materials', methods=['GET'])
def get_materials():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM materials_processed", conn)
    finally:
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
    try:
        df = pd.read_sql_query("SELECT * FROM materials_processed", conn)
    finally:
        conn.close()

    # --- 1. ACTION: FILTERING (Constraint Handling) ---
    df = df[df["Strength_MPa"] >= strength_req]
    df = df[df["Weight_Capacity_kg"] >= weight_req]

    if fragility == "high":
        df = df[df["Strength_MPa"] >= 30]
    
    if category == "food":
        df = df[df["Biodegradability_Score"] >= 70]

    if df.empty:
        return jsonify({"recommended_materials": [], "message": "No materials meet the strict safety constraints."})

    # --- 2. ACTION: DYNAMIC WEIGHTING ---
    eco_weight, cost_weight, strength_weight = 0.33, 0.33, 0.34
    if sustainability_priority == "high":
        eco_weight, cost_weight, strength_weight = 0.6, 0.2, 0.2
    
    if shipping == "international":
        eco_weight += 0.1
        cost_weight -= 0.1

    # --- 3. ML-BASED PREDICTION & SCORING ---
    # Prepare input for ONNX (Convert to float32 numpy array)
    X = df[features].values.astype(np.float32)
    
    # ONNX Inference
    # Input name is usually 'float_input' based on our conversion script
    input_name_cost = cost_session.get_inputs()[0].name
    input_name_co2 = co2_session.get_inputs()[0].name
    
    df['predicted_cost'] = cost_session.run(None, {input_name_cost: X})[0]
    df['predicted_co2'] = co2_session.run(None, {input_name_co2: X})[0]

    def normalize(series, reverse=False):
        if series.max() == series.min(): return series * 0
        norm = (series - series.min()) / (series.max() - series.min())
        return 1 - norm if reverse else norm

    cost_score = normalize(df['predicted_cost'], reverse=True)
    co2_score = normalize(df['predicted_co2'], reverse=True)
    strength_score = normalize(df['Strength_MPa'])
    eco_core_score = (co2_score + normalize(df['Biodegradability_Score'])) / 2

    df['suitability_score'] = (eco_weight * eco_core_score + cost_weight * cost_score + strength_weight * strength_score)
    df.loc[df['Product_Category'] == category, 'suitability_score'] += 0.1

    ranked = df.sort_values("suitability_score", ascending=False).head(5)
    output = {"recommended_materials": []}
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
    try:
        df = pd.read_sql_query("SELECT * FROM materials_processed", conn)
    finally:
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

@app.route('/db-view')
def view_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM materials_processed LIMIT 100", conn)
        conn.close()
        
        table_html = df.to_html(classes='table table-striped', index=False)
        return f"""
        <html>
            <head>
                <title>Database View</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body class="container mt-5">
                <h1>Materials Processed (Top 100)</h1>
                {table_html}
            </body>
        </html>
        """
    except Exception as e:
        return f"Error reading database: {e}. Path: {DB_PATH}"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
