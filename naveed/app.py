from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine

# ---------------------------------------
# Flask Initialization
# ---------------------------------------
app = Flask(__name__)
CORS(app)

# ---------------------------------------
# Database Configuration
# ---------------------------------------
DB_URI = "postgresql://postgres:Naveed%4015@localhost:5432/packagingdb"
engine = create_engine(DB_URI)


def fetch_materials():
    return pd.read_sql("SELECT * FROM materials;", engine)


try:
    with engine.connect() as conn:
        print("Database connected successfully")
except Exception as e:
    print("DB connection error:", e)


# ---------------------------------------
# Load ML Models
# ---------------------------------------
rf_cost = joblib.load("rf_cost_model.pkl")
xgb_co2 = joblib.load("xgb_co2_model.pkl")
scaler = joblib.load("scaler.pkl")


# ---------------------------------------
# Category Filtering Rules
# ---------------------------------------
CATEGORY_RULES = {
    "food": lambda df: df[df["biodegradability_score"] >= 7],
    "electronics": lambda df: df[df["strength"] >= 2],
    "cosmetics": lambda df: df[df["recyclability_percentage"] >= 80],
    "pharmaceuticals": lambda df: df[df["biodegradability_score"] >= 6],
    "fragile_goods": lambda df: df[df["strength"] >= 2],
    "textiles": lambda df: df[df["recyclability_percentage"] >= 70],
    "furniture": lambda df: df[df["strength"] >= 3],
    "industrial_parts": lambda df: df[df["strength"] >= 3],
    "stationery": lambda df: df[df["recyclability_percentage"] >= 75],
    "ecommerce_general": lambda df: df[df["strength"] >= 1],
}


# ---------------------------------------
# Health Check API
# ---------------------------------------
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "EcoPackAI backend running"})





# ---------------------------------------
# Recommendation API
# ---------------------------------------
@app.route("/recommend", methods=["POST"])
def recommend_materials():

    data = request.get_json()

    required_fields = [
        "product_category",
        "fragility",
        "shipping_type",
        "sustainability_priority",
    ]

    if not data or not all(field in data for field in required_fields):
        return jsonify({
            "status": "error",
            "message": "Missing required input fields"
        }), 400

    product_category = data["product_category"].lower()
    fragility = data["fragility"].lower()
    shipping_type = data["shipping_type"].lower()
    sustainability_priority = data["sustainability_priority"].lower()

    # ---------------------------------------
    # Fetch Materials from DB
    # ---------------------------------------
    materials_df = fetch_materials()

    if materials_df.empty:
        return jsonify({"recommended_materials": []})

    # ---------------------------------------
    # Category Filtering
    # ---------------------------------------
    if product_category in CATEGORY_RULES:
        filtered = CATEGORY_RULES[product_category](materials_df)
        if filtered.empty:
            filtered = materials_df
        materials_df = filtered

    # ---------------------------------------
    # Fragility Filtering
    # ---------------------------------------
    if fragility == "high":
        materials_df = materials_df[materials_df["strength"] >= 3]
    elif fragility == "medium":
        materials_df = materials_df[materials_df["strength"] >= 2]
    else:
        materials_df = materials_df[materials_df["strength"] >= 1]

    # ---------------------------------------
    # ML Predictions
    # ---------------------------------------
    predictions = []

    for _, row in materials_df.iterrows():

        features = pd.DataFrame([{
        "strength": row["strength"],
        "weigth_capacity_kg": row["weigth_capacity_kg"],
        "biodegradability_score": row["biodegradability_score"],
        "recyclability_percentage": row["recyclability_percentage"]
    
        }])

        features_scaled = scaler.transform(features)

    
       

        predictions.append({
            "material": row["material_name"],
            "predicted_cost": float(rf_cost.predict(features_scaled)[0]),
            "predicted_co2": float(xgb_co2.predict(features_scaled)[0])
        })

    df = pd.DataFrame(predictions)
    print("Predictions DataFrame:")
    print(df.head())

    # ---------------------------------------
    # Normalization + Ranking
    # ---------------------------------------
    df["cost_score"] = 1 - df["predicted_cost"].rank(pct=True)
    df["eco_score"] = 1 - df["predicted_co2"].rank(pct=True)

    # Default weights
    cost_weight = 0.5
    eco_weight = 0.5

    if sustainability_priority == "high":
        eco_weight = 0.7
        cost_weight = 0.3

    elif sustainability_priority == "low":
        cost_weight = 0.7
        eco_weight = 0.3

    if shipping_type == "international":
        eco_weight += 0.1
        cost_weight -= 0.1

    df["suitability_score"] = (
        eco_weight * df["eco_score"] +
        cost_weight * df["cost_score"]
    )

    df = df.sort_values("suitability_score", ascending=False)

    # ---------------------------------------
    # Final Response
    # ---------------------------------------
    response_df = df.head(10)

    return jsonify({
        "recommended_materials":
        response_df.to_dict(orient="records")
    })


# ---------------------------------------
# Run Server
# ---------------------------------------
if __name__ == "__main__":
     app.run(host="0.0.0.0", port=5000)