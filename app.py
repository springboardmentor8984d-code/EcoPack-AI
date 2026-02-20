from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import numpy as np
import joblib
import os
import io

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from openpyxl import Workbook

app = Flask(__name__)

# ---------------- GLOBAL STORAGE ----------------
LAST_RECOMMENDATIONS = []
LAST_METRICS = {}

# ---------------- LAZY LOADING ----------------
cost_model = None
co2_model = None
scaler = None

STRENGTH_MAP = {"Low": 1, "Medium": 2, "High": 3}

def load_models():
    global cost_model, co2_model, scaler
    if cost_model is None:
        cost_model = joblib.load("cost_model.pkl")
    if co2_model is None:
        co2_model = joblib.load("co2_model.pkl")
    if scaler is None:
        scaler = joblib.load("scaler.pkl")

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- RECOMMEND ----------------
@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        load_models()   # 🔥 loads once only

        global LAST_RECOMMENDATIONS, LAST_METRICS

        data = request.get_json()

        weight = float(data.get("weight"))
        fragility = data.get("fragility")

        df = pd.read_csv("packaging_materials.csv")

        df["strength_num"] = df["strength"].map(STRENGTH_MAP).fillna(1)

        if fragility == "High":
            df = df[df["strength_num"] == 3]
        elif fragility == "Medium":
            df = df[df["strength_num"] >= 2]

        recommendations = []

        for _, row in df.iterrows():

            model_input = pd.DataFrame([{
                "strength": row["strength_num"],
                "Weight_Capacity_kg": weight,
                "Recyclability_Percentage": row["recyclability_percentage"],
                "biodegradability_score": row["biodegradability_score"]
            }])

            scaled = scaler.transform(model_input)

            pred_cost = float(cost_model.predict(scaled)[0])
            pred_co2 = float(co2_model.predict(scaled)[0])

            eco_score = (
                (row["recyclability_percentage"] * 0.4) +
                (row["biodegradability_score"] * 0.3)
            )

            strength_score = row["strength_num"] * 10
            cost_score = max(0, 10 - row["cost_per_unit"]) * 5
            ml_score = max(0, 10 - pred_co2) * 10

            suitability = round(
                (ml_score * 0.4) +
                (eco_score * 0.3) +
                (strength_score * 0.2) +
                (cost_score * 0.1),
                2
            )

            recommendations.append({
                "material": row["material_type"],
                "cost": round(float(row["cost_per_unit"]), 2),
                "co2": round(max(pred_co2, 0), 2),
                "suitability": suitability
            })

        top_recs = sorted(recommendations, key=lambda x: x["suitability"], reverse=True)[:5]

        best = top_recs[0]

        LAST_RECOMMENDATIONS = top_recs
        LAST_METRICS = {
            "cost_savings": round(max(0, 10.0 - best["cost"]), 2),
            "co2_reduction": round(max(0, ((8.0 - best["co2"]) / 8.0) * 100), 2)
        }

        return jsonify({
            "estimated_cost": best["cost"],
            "estimated_co2": best["co2"],
            "recommendations": top_recs
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

