from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import numpy as np
import psycopg2
import joblib
import os
import io

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from openpyxl import Workbook

app = Flask(__name__)
df = pd.read_csv("packaging_materials.csv")

# ---------------- GLOBAL STORAGE ----------------
LAST_RECOMMENDATIONS = []
LAST_METRICS = {}

# ---------------- LOAD MODELS ----------------
cost_model = joblib.load("cost_model.pkl")
co2_model = joblib.load("co2_model.pkl")
scaler = joblib.load("scaler.pkl")

# ---------------- DATABASE CONNECTION ----------------
#def get_db_connection():
#    return psycopg2.connect(
 #       host="localhost",
  #      database="ecopackai",
   #     user="postgres",
    #    password="Teja@750"
    #)

STRENGTH_MAP = {"Low": 1, "Medium": 2, "High": 3}

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- RECOMMEND ----------------
@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        global LAST_RECOMMENDATIONS, LAST_METRICS

        data = request.get_json()

        weight = float(data.get("weight"))
        fragility = data.get("fragility")

        conn = get_db_connection()

        query = """
        SELECT material_type,
               strength,
               weight_capacity_kg,
               cost_per_unit,
               co2_emission_score,
               recyclability_percentage,
               biodegradability_score
        FROM packaging_materials
        """

        df = pd.read_sql(query, conn)
        conn.close()

        # Convert strength to numeric
        df["strength_num"] = df["strength"].map(STRENGTH_MAP).fillna(1)

        # Fragility filtering
        if fragility == "High":
            df = df[df["strength_num"] == 3]
        elif fragility == "Medium":
            df = df[df["strength_num"] >= 2]

        recommendations = []

        for _, row in df.iterrows():

            # -------- ML INPUT (EXACT TRAINING FORMAT) --------
            model_input = pd.DataFrame([{
                "strength": row["strength_num"],
                "Weight_Capacity_kg": weight,
                "Recyclability_Percentage": row["recyclability_percentage"],
                "biodegradability_score": row["biodegradability_score"]
            }])

            scaled = scaler.transform(model_input)

            pred_cost = float(cost_model.predict(scaled)[0])
            pred_co2 = float(co2_model.predict(scaled)[0])

            # ================= HYBRID RANKING ENGINE =================

            # Material intelligence scores
            eco_score = (
                (row["recyclability_percentage"] * 0.4) +
                (row["biodegradability_score"] * 0.3)
            )

            strength_score = row["strength_num"] * 10
            cost_score = max(0, 10 - row["cost_per_unit"]) * 5

            # ML intelligence
            ml_score = max(0, 10 - pred_co2) * 10

            # Final suitability (HYBRID AI)
            suitability = round(
                (ml_score * 0.4) +        # ML influence
                (eco_score * 0.3) +       # sustainability
                (strength_score * 0.2) +  # strength logic
                (cost_score * 0.1),       # cost logic
                2
            )

            recommendations.append({
                "material": row["material_type"],
                "cost": round(float(row["cost_per_unit"]), 2),
                "co2": round(max(pred_co2, 0), 2),
                "suitability": suitability
            })

        # Ranking
        top_recs = sorted(
            recommendations,
            key=lambda x: x["suitability"],
            reverse=True
        )[:5]

        # BI Metrics
        best = top_recs[0]

        cost_savings = round(max(0, 10.0 - best["cost"]), 2)
        co2_reduction = round(
            max(0, ((8.0 - best["co2"]) / 8.0) * 100),
            2
        )

        LAST_RECOMMENDATIONS = top_recs
        LAST_METRICS = {
            "cost_savings": cost_savings,
            "co2_reduction": co2_reduction
        }

        return jsonify({
            "estimated_cost": best["cost"],
            "estimated_co2": best["co2"],
            "recommendations": top_recs
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= PDF DOWNLOAD =================
@app.route("/download_pdf")
def download_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("EcoPackAI Recommendation Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(
        f"Cost Savings: ₹{LAST_METRICS.get('cost_savings',0)}",
        styles["Normal"]
    ))
    elements.append(Paragraph(
        f"CO₂ Reduction: {LAST_METRICS.get('co2_reduction',0)}%",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 12))

    table_data = [["Rank", "Material", "Cost", "CO₂", "Suitability"]]

    for i, r in enumerate(LAST_RECOMMENDATIONS):
        table_data.append([
            i+1,
            r["material"],
            r["cost"],
            r["co2"],
            r["suitability"]
        ])

    elements.append(Table(table_data))
    doc.build(elements)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True,
                     download_name="EcoPackAI_Report.pdf")


# ================= EXCEL DOWNLOAD =================
@app.route("/download_excel")
def download_excel():
    wb = Workbook()
    ws = wb.active
    ws.title = "Recommendations"

    ws.append(["Rank", "Material", "Cost", "CO₂", "Suitability"])

    for i, r in enumerate(LAST_RECOMMENDATIONS):
        ws.append([
            i+1,
            r["material"],
            r["cost"],
            r["co2"],
            r["suitability"]
        ])

    file_stream = io.BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    return send_file(
        file_stream,
        as_attachment=True,
        download_name="EcoPackAI_Recommendations.xlsx"
    )


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
