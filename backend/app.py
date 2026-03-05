# =====================================================
# EcoPackAI - Production Backend
# =====================================================

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

DB_URI = os.getenv("DATABASE_URL")

if not DB_URI:
    # Fallback to local SQLite for development
    DB_URI = "sqlite:///ecopackai.db"
    print("No DATABASE_URL found. Using local SQLite database.")

engine = create_engine(DB_URI)


def ensure_tables():
    """Create history tables if they do not exist."""
    is_sqlite = "sqlite" in DB_URI
    with engine.begin() as conn:
        if is_sqlite:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS recommendation_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_category TEXT,
                    fragility TEXT,
                    shipping_type TEXT,
                    sustainability_priority TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS recommendation_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    material TEXT,
                    predicted_cost REAL,
                    predicted_co2 REAL,
                    suitability_score REAL,
                    FOREIGN KEY(run_id) REFERENCES recommendation_runs(id) ON DELETE CASCADE
                );
            """))
            # Create materials table for SQLite if missing
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS materials (
                    material_id INTEGER PRIMARY KEY,
                    material_name TEXT,
                    strength INTEGER,
                    weight_capacity REAL,
                    cost INTEGER,
                    biodegradability_score INTEGER,
                    co2_score INTEGER,
                    recyclability_percentage INTEGER
                );
            """))
        else:
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


def seed_materials_if_empty():
    """Seed sample materials for SQLite development mode."""
    if "sqlite" not in DB_URI:
        return
    
    with engine.begin() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM materials;")).scalar()
        if count > 0:
            return
        
        sample_materials = [
            (1, "Recycled Cardboard", 4, 50, 3, 9, 1, 95),
            (2, "Biodegradable Foam", 3, 30, 5, 10, 1, 80),
            (3, "Corn Starch Packing", 2, 20, 4, 10, 1, 100),
            (4, "Recycled Paper", 3, 25, 2, 9, 1, 100),
            (5, "Bamboo Fiber", 4, 45, 6, 10, 1, 90),
            (6, "Hemp Packaging", 5, 60, 7, 9, 1, 85),
            (7, "Recycled Plastic", 5, 70, 4, 3, 3, 75),
            (8, "Glass Container", 5, 80, 8, 2, 4, 90),
            (9, "Aluminum Can", 5, 75, 6, 1, 5, 95),
            (10, "Steel Tin", 5, 90, 7, 1, 6, 90),
            (11, "PLA Bioplastic", 4, 40, 5, 8, 2, 70),
            (12, "Mushroom Packaging", 3, 35, 8, 10, 1, 100),
        ]
        
        for m in sample_materials:
            conn.execute(
                text("""
                    INSERT INTO materials 
                    (material_id, material_name, strength, weight_capacity, cost, 
                     biodegradability_score, co2_score, recyclability_percentage)
                    VALUES (:id, :name, :str, :wc, :cost, :bio, :co2, :rec);
                """),
                {"id": m[0], "name": m[1], "str": m[2], "wc": m[3], 
                 "cost": m[4], "bio": m[5], "co2": m[6], "rec": m[7]}
            )
        print("Seeded sample materials for development.")


seed_materials_if_empty()


def fetch_materials():
    return pd.read_sql("SELECT * FROM materials;", engine)


# =====================================================
# Load ML Models
# =====================================================
rf_cost = joblib.load("rf_cost_model.pkl")
xgb_co2 = joblib.load("xgb_co2_model.pkl")
scaler = joblib.load("scaler.pkl")


# =====================================================
# Category Filtering Rules
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
# Health Check
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

    product_category = data["product_category"].strip().lower()
    fragility = data["fragility"].strip().lower()
    shipping_type = data["shipping_type"].strip().lower()
    sustainability_priority = data["sustainability_priority"].strip().lower()

    materials_df = fetch_materials()

    if materials_df.empty:
        return jsonify({"recommended_materials": []})

    # =====================================================
    # Category Filtering
    # =====================================================
    if product_category in CATEGORY_RULES:
        filtered = CATEGORY_RULES[product_category](materials_df)

        if filtered.empty:
            filtered = materials_df

        materials_df = filtered
    else:
        return jsonify({"recommended_materials": []})

    # =====================================================
    # Fragility Filtering
    # =====================================================
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
    else:
        filtered = materials_df[
            (materials_df["strength"] >= 2)
        ]

    if filtered.empty:
        filtered = materials_df

    materials_df = filtered

    # =====================================================
    # ML Predictions (STABLE FIXED VERSION)
    # =====================================================
    feature_cols = [
        "strength",
        "weight_capacity",
        "recyclability_percentage",
        "biodegradability_score"
    ]

    materials_df[feature_cols] = materials_df[feature_cols].apply(
        pd.to_numeric,
        errors="coerce"
    ).fillna(0).astype(float)

    predictions = []

    for _, row in materials_df.iterrows():
        features_df = pd.DataFrame([{
            "strength": float(row["strength"]),
            "weight_capacity": float(row["weight_capacity"]),
            "recyclability_percentage": float(row["recyclability_percentage"]),
            "biodegradability_score": float(row["biodegradability_score"])
        }], columns=feature_cols)

        features_scaled = scaler.transform(features_df)

        predictions.append({
            "material": row["material_name"],
            "predicted_cost": round(float(rf_cost.predict(features_scaled)[0]), 4),
            "predicted_co2": round(float(xgb_co2.predict(features_scaled)[0]), 4)
        })

    df = pd.DataFrame(predictions)

    if df.empty:
        return jsonify({
            "recommended_materials": [],
            "top10": []
        })

    # =====================================================
    # Normalization
    # =====================================================
    df["cost_score"] = 1 - df["predicted_cost"].rank(pct=True)
    df["eco_score"] = 1 - df["predicted_co2"].rank(pct=True)

    # =====================================================
    # Dynamic Weighting
    # =====================================================
    cost_weight = 0.45
    eco_weight = 0.55

    if sustainability_priority == "high":
        eco_weight += 0.35
        cost_weight -= 0.35
        df["eco_score"] *= 1.1
    elif sustainability_priority == "low":
        cost_weight += 0.35
        eco_weight -= 0.35
        df["cost_score"] *= 1.1

    if shipping_type == "international":
        eco_weight += 0.25
        cost_weight -= 0.25
        df["eco_score"] *= 1.05
    else:
        cost_weight += 0.1
        eco_weight -= 0.1

    # =====================================================
    # Final Score
    # =====================================================
    df["suitability_score"] = (
        eco_weight * df["eco_score"] +
        cost_weight * df["cost_score"]
    )

    df = df.sort_values("suitability_score", ascending=False)

    top10_df = df.head(10)
    response_df = df.head(3)

    # =====================================================
    # Persist Recommendation
    # =====================================================
    is_sqlite = "sqlite" in DB_URI
    with engine.begin() as conn:
        params = {
            "product_category": product_category,
            "fragility": fragility,
            "shipping_type": shipping_type,
            "sustainability_priority": sustainability_priority
        }
        if is_sqlite:
            conn.execute(
                text("""
                    INSERT INTO recommendation_runs
                        (product_category, fragility, shipping_type, sustainability_priority)
                    VALUES
                        (:product_category, :fragility, :shipping_type, :sustainability_priority);
                """),
                params
            )
            run_id = conn.execute(text("SELECT last_insert_rowid();")).scalar_one()
        else:
            run_id = conn.execute(
                text("""
                    INSERT INTO recommendation_runs
                        (product_category, fragility, shipping_type, sustainability_priority)
                    VALUES
                        (:product_category, :fragility, :shipping_type, :sustainability_priority)
                    RETURNING id;
                """),
                params
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
        "recommended_materials": response_df[
            ["material", "predicted_cost", "predicted_co2", "suitability_score"]
        ].to_dict(orient="records"),
        "top10": top10_df[
            ["material", "predicted_cost", "predicted_co2", "suitability_score"]
        ].to_dict(orient="records")
    })


# =====================================================
# History API
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
# Clear History
# =====================================================
@app.route("/history/clear", methods=["POST"])
def clear_history():
    is_sqlite = "sqlite" in DB_URI
    with engine.begin() as conn:
        if is_sqlite:
            conn.execute(text("DELETE FROM recommendation_items;"))
            conn.execute(text("DELETE FROM recommendation_runs;"))
        else:
            conn.execute(text(
                "TRUNCATE recommendation_items, recommendation_runs RESTART IDENTITY;"
            ))
    return jsonify({"status": "cleared"})

@app.route("/analytics", methods=["GET"])
def analytics():

    query = """
        SELECT material, predicted_cost, predicted_co2, suitability_score
        FROM recommendation_items;
    """

    df = pd.read_sql(query, engine)

    if df.empty:
        return jsonify({"status": "empty"})

    # -----------------------------
    # Summary metrics
    # -----------------------------
    avg_cost = float(df["predicted_cost"].mean())
    avg_co2 = float(df["predicted_co2"].mean())

    total_recs = int(len(df))

    # Baseline comparison
    baseline_cost = 10
    baseline_co2 = 2

    cost_savings = max(0, baseline_cost - avg_cost)
    co2_reduction = max(0, (baseline_co2 - avg_co2) / baseline_co2 * 100)

    # -----------------------------
    # Material usage count
    # -----------------------------
    usage = df["material"].value_counts()

    material_usage = {
        "labels": usage.index.tolist(),
        "values": usage.values.tolist()
    }

    # -----------------------------
    # Sustainability ranking
    # -----------------------------
    ranking = df.groupby("material")["suitability_score"].mean().sort_values(ascending=False)

    ranking_chart = {
        "labels": ranking.index.tolist(),
        "values": ranking.values.tolist()
    }

    # -----------------------------
    # Eco material share
    # -----------------------------
    eco = (df["predicted_co2"] < 1).sum()
    non_eco = len(df) - eco

    eco_share = {
        "labels": ["Eco Friendly", "Standard"],
        "values": [int(eco), int(non_eco)]
    }

    return jsonify({
        "summary": {
            "total_recommendations": total_recs,
            "avg_cost": avg_cost,
            "avg_co2": avg_co2,
            "cost_savings": cost_savings,
            "co2_reduction": co2_reduction
        },
        "material_usage": material_usage,
        "eco_share": eco_share,
        "ranking": ranking_chart
    })


# =====================================================
# Run Server
# =====================================================
if __name__ == "__main__":
    print("Starting EcoPackAI backend...")
    app.run(debug=True)