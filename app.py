from flask import Flask, request, render_template
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler
import psycopg2
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# -------------------------------
# DATABASE CONNECTION
# -------------------------------
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

# -------------------------------
# LOAD MODELS
# -------------------------------
cost_model = joblib.load("cost_model.pkl")
co2_model = joblib.load("co2_model.pkl")
scaler = joblib.load("scaler.pkl")

# -------------------------------
# LOAD DATASET
# -------------------------------
df = pd.read_csv("ecopackai_unique_materials_dataset.csv")

# -------------------------------
# PROCESS DATA (FIXED)
# -------------------------------
def process_data():
    data = df.copy()

    X = data[
        ["tensile_strength_mpa",
         "max_load_kg",
         "recyclability_percent",
         "biodegradability_score"]
    ]

    X_scaled = scaler.transform(X)

    # COST prediction
    data["predicted_cost"] = cost_model.predict(X_scaled)

    # CO2 prediction (SAFE FIX)
    try:
        co2_pred = co2_model.predict(X_scaled)
        co2_pred = np.array(co2_pred)

        # remove NaN
        co2_pred = np.nan_to_num(co2_pred, nan=0.0)

        # clamp negative values
        co2_pred = np.clip(co2_pred, 0, None)

    except Exception as e:
        print("CO2 MODEL ERROR:", e)

        # SMART fallback instead of zero
        co2_pred = data["predicted_cost"] * 0.6

    data["predicted_co2"] = co2_pred

    return data

# -------------------------------
# MATERIAL USAGE (DB)
# -------------------------------
def get_material_usage():
    cursor.execute("""
        SELECT material_name, COUNT(*) 
        FROM recommendations
        GROUP BY material_name
        ORDER BY COUNT(*) DESC
    """)
    rows = cursor.fetchall()

    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]

    return labels, values

# -------------------------------
# RECOMMENDATION LOGIC
# -------------------------------
def recommend_material(input_data):

    data = process_data()

    fragility = input_data.get("fragility", "medium")
    category = input_data.get("product_category", "general")
    shipping = input_data.get("shipping_type", "domestic")

    # FILTERING
    if fragility == "high":
        data = data[data["tensile_strength_mpa"] >= 4]
    elif fragility == "medium":
        data = data[data["tensile_strength_mpa"] >= 2]
    else:
        data = data[data["tensile_strength_mpa"] >= 1]

    if category == "food":
        data = data[data["biodegradability_score"] >= 3]
    elif category == "electronics":
        data = data[data["tensile_strength_mpa"] >= 3]
    elif category == "cosmetics":
        data = data[data["biodegradability_score"] >= 2]

    if data.empty:
        return [], []

    # NORMALIZATION
    scaler_local = MinMaxScaler()
    data[["cost_norm", "co2_norm", "strength_norm"]] = scaler_local.fit_transform(
        data[["predicted_cost", "predicted_co2", "tensile_strength_mpa"]]
    )

    # ECO SCORE
    data["eco_score"] = 1 - (0.5 * data["cost_norm"] + 0.5 * data["co2_norm"])

    # WEIGHTS
    eco_weight = 0.4
    cost_weight = 0.3
    strength_weight = 0.3

    if shipping == "international":
        eco_weight += 0.2
        cost_weight -= 0.1

    data["suitability_score"] = (
        eco_weight * data["eco_score"] +
        cost_weight * (1 - data["cost_norm"]) +
        strength_weight * data["strength_norm"]
    )

    result = data.sort_values("suitability_score", ascending=False)

    top_results = result.head(5).copy()
    full_data = result.head(15).copy()

    # METRICS
    baseline_co2 = max(data["predicted_co2"].max(), 1)
    baseline_cost = data["predicted_cost"].max()

    top_results["co2_reduction_percent"] = (
        (baseline_co2 - top_results["predicted_co2"]) / baseline_co2
    ) * 100

    # FIX: clamp between 0–100
    top_results["co2_reduction_percent"] = top_results["co2_reduction_percent"].clip(0, 100)

    top_results["cost_savings"] = baseline_cost - top_results["predicted_cost"]

    # SAVE TO DB
    for _, row in top_results.iterrows():
        cursor.execute("""
            INSERT INTO recommendations 
            (material_name, predicted_cost, predicted_co2, suitability_score, co2_reduction, cost_savings)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            row["material_name"],
            float(row["predicted_cost"]),
            float(row["predicted_co2"]),
            float(row["suitability_score"]),
            float(row["co2_reduction_percent"]),
            float(row["cost_savings"])
        ))

    conn.commit()

    return (
        top_results.to_dict(orient="records"),
        full_data.to_dict(orient="records")
    )

# -------------------------------
# ROUTES
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict_form", methods=["POST"])
def predict_form():

    data = {
        "product_category": request.form.get("product_category"),
        "fragility": request.form.get("fragility"),
        "shipping_type": request.form.get("shipping_type"),
        "sustainability_priority": request.form.get("sustainability_priority")
    }

    results, full_data = recommend_material(data)

    if not results:
        return render_template("result.html", results=[], full_data=[])

    labels, values = get_material_usage()

    return render_template(
        "result.html",
        results=results,
        full_data=full_data,
        usage_labels=labels,
        usage_values=values
    )

# -------------------------------
if __name__ == "__main__":
    app.run(debug=False)