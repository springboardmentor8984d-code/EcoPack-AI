import os

from flask import Flask, request, jsonify
from flask_cors import CORS

import pandas as pd
import numpy as np
import joblib
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# =====================================================
# Flask App Initialization
# =====================================================
app = Flask(__name__)
CORS(app)

# =====================================================
# Database Configuration
# =====================================================
load_dotenv()

DB_URI = (
    os.getenv("DATABASE_URL")
)

engine = create_engine(DB_URI)

def ensure_tables():
    """Create history tables if they do not exist."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS recommendation_runs (
                id SERIAL PRIMARY KEY,
                product_category TEXT,
                fragility TEXT,
                shipping_type TEXT,
                sustainability_priority TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS recommendation_items (
                id SERIAL PRIMARY KEY,
                run_id INTEGER REFERENCES recommendation_runs(id) ON DELETE CASCADE,
                material TEXT,
                predicted_cost DOUBLE PRECISION,
                predicted_co2 DOUBLE PRECISION,
                suitability_score DOUBLE PRECISION
            );
        """))

ensure_tables()

def fetch_materials():
    return pd.read_sql("SELECT * FROM materials;", engine)

# =====================================================
# Load Trained ML Models
# =====================================================
rf_cost = joblib.load("rf_cost_model.pkl")
xgb_co2 = joblib.load("xgb_co2_model.pkl")
scaler = joblib.load("scaler.pkl")

# =====================================================
# Category Filtering Rules (Single Category)
# =====================================================
CATEGORY_RULES = {
    "food": lambda df: df[
        (df["biodegradability_score"] >= 8) &
        (df["recyclability_percentage"] >= 60)
    ],
    "electronics": lambda df: df[
        (df["strength"] >= 4) &
        (df["weight_capacity"] >= 50) &
        (df["recyclability_percentage"] >= 50)
    ],
    "cosmetics": lambda df: df[
        (df["recyclability_percentage"] >= 85) &
        (df["biodegradability_score"] >= 6)
    ],
    "pharmaceuticals": lambda df: df[
        (df["biodegradability_score"] >= 7) &
        (df["strength"] >= 3)
    ],
    "fragile_goods": lambda df: df[
        (df["strength"] >= 4) &
        (df["weight_capacity"] >= 60)
    ],
    "textiles": lambda df: df[
        (df["recyclability_percentage"] >= 80)
    ],
    "furniture": lambda df: df[
        (df["strength"] >= 5) &
        (df["weight_capacity"] >= 70)
    ],
    "industrial_parts": lambda df: df[
        (df["strength"] >= 5) &
        (df["weight_capacity"] >= 80) &
        (df["recyclability_percentage"] >= 55)
    ],
    "stationery": lambda df: df[
        (df["recyclability_percentage"] >= 85)
    ],
    "ecommerce_general": lambda df: df[
        (df["strength"] >= 3) &
        (df["weight_capacity"] >= 30) &
        (df["recyclability_percentage"] >= 60)
    ]
}

# =====================================================
# Health Check API
# =====================================================
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "EcoPackAI backend running"})

# =====================================================
# Recommendation API
# =====================================================
@app.route("/recommend", methods=["POST"])
def recommend_materials():
    data = request.get_json()

    # -----------------------------
    # Validate Input
    # -----------------------------
    required_fields = [
        "product_category",
        "fragility",
        "shipping_type",
        "sustainability_priority"
    ]

    if not data or not all(field in data for field in required_fields):
        return jsonify({
            "status": "error",
            "message": "Missing required input fields"
        }), 400

    product_category = data["product_category"]
    fragility = data["fragility"]
    shipping_type = data["shipping_type"]
    sustainability_priority = data["sustainability_priority"]

    if not isinstance(product_category, str) or not product_category:
        return jsonify({
            "status": "error",
            "message": "product_category must be a single value"
        }), 400

    # -----------------------------
    # Fetch Materials
    # -----------------------------
    materials_df = fetch_materials()

    if materials_df.empty:
        return jsonify({"recommended_materials": []})

    # -----------------------------
    # CATEGORY FILTERING (SAFE)
    # -----------------------------
    if product_category in CATEGORY_RULES:
        filtered = CATEGORY_RULES[product_category](materials_df)

        # fallback if category rule too strict
        if filtered.empty:
            filtered = materials_df

        materials_df = filtered
    else:
        return jsonify({"recommended_materials": []})

    # -----------------------------
    # FRAGILITY FILTERING (tighter)
    # -----------------------------
    if fragility == "high":
        filtered = materials_df[
            (materials_df["strength"] >= 4) &
            (materials_df["weight_capacity"] >= 60)
        ]
    elif fragility == "medium":
        filtered = materials_df[
            (materials_df["strength"] >= 3) &
            (materials_df["weight_capacity"] >= 40)
        ]
    else:  # low
        filtered = materials_df[
            (materials_df["strength"] >= 2)
        ]

    # fallback if fragility too strict
    if filtered.empty:
        filtered = materials_df

    materials_df = filtered

    # -----------------------------
    # ML Predictions (UNCHANGED)
    # -----------------------------
    predictions = []

    for _, row in materials_df.iterrows():
        features = np.array([[
            row["strength"],
            row["weight_capacity"],
            row["recyclability_percentage"],
            row["biodegradability_score"]
        ]])

        features_scaled = scaler.transform(features)

        predictions.append({
            "material": row["material_name"],
            "predicted_cost": float(rf_cost.predict(features_scaled)[0]),
            "predicted_co2": float(xgb_co2.predict(features_scaled)[0])
        })

    df = pd.DataFrame(predictions)

    # -----------------------------
    # NORMALIZATION
    # -----------------------------
    df["cost_score"] = 1 - df["predicted_cost"].rank(pct=True)
    df["eco_score"] = 1 - df["predicted_co2"].rank(pct=True)

    # -----------------------------
    # RANKING WEIGHTS (USER INPUT)
    # -----------------------------
    cost_weight = 0.45
    eco_weight = 0.55

    if sustainability_priority == "high":
        eco_weight += 0.35  # stronger eco tilt
        cost_weight -= 0.35
        # penalize high CO2 directly
        df["eco_score"] = df["eco_score"] * 1.1
    elif sustainability_priority == "low":
        cost_weight += 0.35
        eco_weight -= 0.35
        # emphasize cheaper picks
        df["cost_score"] = df["cost_score"] * 1.1

    if shipping_type == "international":
        eco_weight += 0.25
        cost_weight -= 0.25
        # slightly reward lighter materials via existing eco score proxy
        df["eco_score"] = df["eco_score"] * 1.05
    else:  # domestic
        cost_weight += 0.1
        eco_weight -= 0.1

    # -----------------------------
    # FINAL SUITABILITY SCORE
    # -----------------------------
    df["suitability_score"] = (
        eco_weight * df["eco_score"] +
        cost_weight * df["cost_score"]
    )

    df = df.sort_values("suitability_score", ascending=False)

    # -----------------------------
    # RESPONSE
    # -----------------------------
    top10_df = df.head(10)[
        ["material", "predicted_cost", "predicted_co2", "suitability_score"]
    ]

    response_df = df.head(3)[
        ["material", "predicted_cost", "predicted_co2", "suitability_score"]
    ]

    # -----------------------------
    # Persist run + items
    # -----------------------------
    with engine.begin() as conn:
        run_id = conn.execute(
            text("""
                INSERT INTO recommendation_runs
                    (product_category, fragility, shipping_type, sustainability_priority)
                VALUES
                    (:product_category, :fragility, :shipping_type, :sustainability_priority)
                RETURNING id;
            """),
            {
                "product_category": product_category,
                "fragility": fragility,
                "shipping_type": shipping_type,
                "sustainability_priority": sustainability_priority
            }
        ).scalar_one()

        conn.execute(
            text("""
                INSERT INTO recommendation_items
                    (run_id, material, predicted_cost, predicted_co2, suitability_score)
                VALUES
                    (:run_id, :material, :predicted_cost, :predicted_co2, :suitability_score);
            """),
            [
                {
                    "run_id": run_id,
                    "material": row.material,
                    "predicted_cost": float(row.predicted_cost),
                    "predicted_co2": float(row.predicted_co2),
                    "suitability_score": float(row.suitability_score)
                }
                for row in top10_df.itertuples()
            ]
        )

    return jsonify({
        "recommended_materials": response_df.to_dict(orient="records"),
        "top10": top10_df.to_dict(orient="records"),
        "inputs": {
            "product_category": product_category,
            "fragility": fragility,
            "shipping_type": shipping_type,
            "sustainability_priority": sustainability_priority
        }
    })

# =====================================================
# Recommendation History API
# =====================================================
@app.route("/history", methods=["GET"])
def history():
    with engine.begin() as conn:
        runs = conn.execute(
            text("SELECT id FROM recommendation_runs ORDER BY created_at ASC;")
        ).fetchall()
        items = conn.execute(
            text("""
                SELECT run_id, material, predicted_cost, predicted_co2, suitability_score
                FROM recommendation_items
                ORDER BY id ASC;
            """)
        ).fetchall()

    items_by_run = {}
    for row in items:
        items_by_run.setdefault(row.run_id, []).append({
            "material": row.material,
            "predicted_cost": float(row.predicted_cost),
            "predicted_co2": float(row.predicted_co2),
            "suitability_score": float(row.suitability_score)
        })

    history_payload = [items_by_run.get(run.id, []) for run in runs]

    return jsonify({"history": history_payload})

# =====================================================
# Clear Recommendation History
# =====================================================
@app.route("/history/clear", methods=["POST"])
def clear_history():
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE recommendation_items, recommendation_runs RESTART IDENTITY;"))
    return jsonify({"status": "cleared"})

# =====================================================
# Run Server
# =====================================================
if __name__ == "__main__":
    print("Starting EcoPackAI backend...")
    app.run(debug=True)
