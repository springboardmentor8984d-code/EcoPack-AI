# ==============================
# IMPORT LIBRARIES
# ==============================

from flask import Flask, request, jsonify, render_template  # For API server
import pandas as pd                        # For data handling
import joblib                              # To load saved ML models
import psycopg2                            # To connect PostgreSQL
from flask import session
import os
from dotenv import load_dotenv

load_dotenv()


# ==============================
# CREATE FLASK APP
# ==============================

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


# ==============================
# LOAD TRAINED MODELS + SCALER
# (Same preprocessing as training)
# ==============================

# RandomForest → cost prediction
rf_cost = joblib.load("models/rf_cost_model.pkl")

# XGBoost → CO2 prediction
xgb_co2 = joblib.load("models/xgb_co2_model.pkl")

# StandardScaler used during training
scaler = joblib.load("models/scaler.pkl")


# ==============================
# DATABASE CONNECTION
# ==============================


conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)


# ==============================
# HOME ROUTE
# loads frontend page
# ==============================

@app.route('/')
def home():
    return render_template("index.html")


# ==========================================================
# MAIN API → MATERIAL RECOMMENDATION
# URL: http://127.0.0.1:5000/recommend
# Method: POST
# ==========================================================

@app.route('/recommend', methods=['POST'])
def recommend_material():

    # ------------------------------------
    # 1. RECEIVE USER INPUT (JSON)
    # ------------------------------------
    data = request.get_json()
    print(data)

    fragility = data['fragility'].lower()
    shipping = data['shipping_type'].lower()
    sustainability = data['sustainability_priority'].lower()
    product_category = data['product_category'].lower()


    # ------------------------------------
    # 2. LOAD MATERIALS FROM DATABASE
    # ------------------------------------
    df = pd.read_sql("SELECT * FROM materials", conn)


    # ------------------------------------
    # 3. FILTER UNSUITABLE MATERIALS
    # (Mentor rule: only remove options)
    # ------------------------------------

    # Fragility → needs strong materials
    if fragility == "high":
        df = df[df['strength'] >= 3]

    elif fragility == "medium":
        df = df[df['strength'] >= 2]


    # Food packaging → biodegradable
    if product_category == "food":
        df = df[df['biodegradability_score'] >= 7]

    print("Rows after filtering:", len(df))


    # ------------------------------------
    # 4. PREPARE FEATURES FOR ML
    # Must match training features EXACTLY
    # ------------------------------------
    X = df[
        ['strength',
         'weight_capacity_kg',
         'recyclability_percent',
         'biodegradability_score']
    ]


    # Scale using same scaler used during training
    X_scaled = scaler.transform(X)


    # ------------------------------------
    # 5. PREDICT COST + CO2
    # ------------------------------------
    df['pred_cost'] = rf_cost.predict(X_scaled)
    df['pred_co2'] = xgb_co2.predict(X_scaled)


    # ------------------------------------
    # 6. CALCULATE SCORES
    # ------------------------------------

    # Strength score (0–10)
    df['strength_norm'] = (df['strength'] / 3) * 10

    # Eco score (biodegradability + recyclability + low CO2)
    df['eco_score'] = (
        df['biodegradability_score'] +
        df['recyclability_percent'] / 10 +
        (10 - df['pred_co2'])
    ) / 3

    # Cost efficiency (lower cost → better)
    df['cost_efficiency'] = 10 - df['pred_cost']


    # ------------------------------------
    # 7. DYNAMIC WEIGHTS
    # (User input changes ranking importance)
    # ------------------------------------

    eco_weight = 0.4
    cost_weight = 0.4
    strength_weight = 0.2

    # Sustainability priority → eco more important
    if sustainability == "high":
        eco_weight += 0.3
        cost_weight -= 0.2

    # International shipping → CO2 more important
    if shipping == "international":
        eco_weight += 0.2
        cost_weight -= 0.1

    print("Weights:", eco_weight, cost_weight, strength_weight)


    # ------------------------------------
    # 8. FINAL SUITABILITY SCORE
    # ------------------------------------
    df['suitability_score'] = (
        eco_weight * df['eco_score'] +
        cost_weight * df['cost_efficiency'] +
        strength_weight * df['strength_norm']
    )


    # ------------------------------------
    # 9. SORT + GET TOP 3 MATERIALS
    # ------------------------------------
    top = df.sort_values(
        'suitability_score',
        ascending=False
    ).head(3)


    # ------------------------------------
    # 10. CREATE JSON RESPONSE
    # ------------------------------------
    results = []

    for _, row in top.iterrows():
        results.append({
            "material": row['material_name'],
            "predicted_cost": float(row['pred_cost']),
            "predicted_co2": float(row['pred_co2']),
            "suitability_score": float(row['suitability_score'])
        })

    session["recommended_materials"] = results

    return jsonify({
        "recommended_materials": results
    })


# =========================
# ANALYTICS ROUTE
# =========================

import plotly.express as px
import plotly.io as pio
import os

@app.route('/analytics')
def analytics():

    top_materials = session.get("recommended_materials")

    if not top_materials:
        return "No recommendation data found. Please generate recommendation first."

    df = pd.DataFrame(top_materials)

    # Baseline values
    baseline_cost = 8
    baseline_co2 = 8

    # Calculate extra metrics
    df["cost_savings"] = baseline_cost - df["predicted_cost"]
    df["co2_reduction_percent"] = (
        (baseline_co2 - df["predicted_co2"]) / baseline_co2
    ) * 100

    # 1️⃣ Horizontal Ranking
    rank_fig = px.bar(
        df,
        x="suitability_score",
        y="material",
        orientation="h",
        title="Top 3 Ranking"
    )
    rank_chart = pio.to_html(rank_fig, full_html=False)

    # 2️⃣ Cost Comparison
    cost_fig = px.bar(
        df,
        x="material",
        y="predicted_cost",
        title="Predicted Cost Comparison"
    )
    cost_chart = pio.to_html(cost_fig, full_html=False)

    # 3️⃣ CO₂ Comparison
    co2_fig = px.bar(
        df,
        x="material",
        y="predicted_co2",
        title="Predicted CO₂ Comparison"
    )
    co2_chart = pio.to_html(co2_fig, full_html=False)

    # 4️⃣ Cost Savings Chart
    savings_fig = px.bar(
        df,
        x="material",
        y="cost_savings",
        title="Cost Savings vs Baseline"
    )
    savings_chart = pio.to_html(savings_fig, full_html=False)

    # 5️⃣ CO₂ Reduction %
    reduction_fig = px.bar(
        df,
        x="material",
        y="co2_reduction_percent",
        title="CO₂ Reduction Percentage"
    )
    reduction_chart = pio.to_html(reduction_fig, full_html=False)

    # 6️⃣ Material Usage Trend (Full Dataset)
    full_df = pd.read_sql("SELECT * FROM materials", conn)
    usage_counts = full_df["material_name"].value_counts().reset_index()
    usage_counts.columns = ["material", "count"]

    usage_fig = px.bar(
        usage_counts,
        x="material",
        y="count",
        title="Material Usage Trend (All Materials)"
    )
    usage_chart = pio.to_html(usage_fig, full_html=False)

    return render_template(
        "analytics.html",
        rank_chart=rank_chart,
        cost_chart=cost_chart,
        co2_chart=co2_chart,
        savings_chart=savings_chart,
        reduction_chart=reduction_chart,
        usage_chart=usage_chart
    )


# =========================
# EXPORT EXCEL
# =========================

from flask import send_file
import io

@app.route('/export_excel')
def export_excel():

    top_materials = session.get("recommended_materials")

    if not top_materials:
        return "No recommendation data found. Please generate recommendation first."

    df = pd.DataFrame(top_materials)

    # Create Excel in memory (not on disk)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Top Recommendations')

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="EcoPack_AI_Report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# =========================
# EXPORT PDF
# =========================

from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes
import io

@app.route('/export_pdf')
def export_pdf():

    top_materials = session.get("recommended_materials")

    if not top_materials:
        return "No recommendation data found. Please generate recommendation first."

    df = pd.DataFrame(top_materials)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=pagesizes.A4)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("EcoPack AI Sustainability Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Create table data
    table_data = [df.columns.tolist()] + df.values.tolist()

    table = Table(table_data)
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="EcoPack_AI_Report.pdf",
        mimetype="application/pdf"
    )


# ==============================
# RUN SERVER
# ==============================

if __name__ == '__main__':
    app.run()
