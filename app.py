from flask import Flask, request, render_template, send_file
import pandas as pd
import joblib
from sklearn.preprocessing import MinMaxScaler
import psycopg2
import numpy as np
import os

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
# PROCESS DATA
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

    data["predicted_cost"] = cost_model.predict(X_scaled)
    data["predicted_co2"] = co2_model.predict(X_scaled)

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
    sustainability = input_data.get("sustainability_priority", "medium")

    # ---------------- FILTERING ----------------
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

    # ---------------- NORMALIZATION ----------------
    scaler_local = MinMaxScaler()

    data[["cost_norm", "co2_norm", "strength_norm"]] = scaler_local.fit_transform(
        data[["predicted_cost", "predicted_co2", "tensile_strength_mpa"]]
    )

    data["eco_score"] = 1 - (0.5 * data["cost_norm"] + 0.5 * data["co2_norm"])

    # ---------------- INPUT-AWARE BOOSTS ----------------
    if fragility == "high":
        data["strength_norm"] *= 1.5
    elif fragility == "low":
        data["strength_norm"] *= 0.7

    if sustainability == "high":
        data["eco_score"] *= 1.5
    elif sustainability == "low":
        data["eco_score"] *= 0.7

    if category == "electronics":
        data["strength_norm"] *= 1.3
    elif category == "food":
        data["eco_score"] *= 1.3

    # ---------------- WEIGHTS ----------------
    eco_weight = 0.4
    cost_weight = 0.3
    strength_weight = 0.3

    if shipping == "international":
        eco_weight += 0.2
        cost_weight -= 0.1

    # ---------------- FINAL SCORE ----------------
    data["suitability_score"] = (
        eco_weight * data["eco_score"] +
        cost_weight * (1 - data["cost_norm"]) +
        strength_weight * data["strength_norm"]
    )

    # tiny randomness (prevents ties but not noticeable)
    data["suitability_score"] += np.random.uniform(0, 0.001, len(data))

    # ---------------- METRICS ----------------
    baseline_co2 = data["predicted_co2"].max()
    baseline_cost = data["predicted_cost"].max()

    data["co2_reduction_percent"] = (
        (baseline_co2 - data["predicted_co2"]) / baseline_co2
    ) * 100

    # ✅ FIX: remove negative values
    data["co2_reduction_percent"] = data["co2_reduction_percent"].clip(lower=0)

    data["cost_savings"] = baseline_cost - data["predicted_cost"]

    # ---------------- SORT ----------------
    result = data.sort_values("suitability_score", ascending=False)

    top_results = result.head(3)
    full_data = result.head(10)

    # ---------------- SAVE TO DB ----------------
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
# EXPORT EXCEL
# -------------------------------
@app.route("/export_excel")
def export_excel():
    cursor.execute("""
        SELECT material_name, predicted_cost, predicted_co2, suitability_score,
               co2_reduction, cost_savings
        FROM recommendations
        ORDER BY id DESC
        LIMIT 50
    """)
    rows = cursor.fetchall()

    df_export = pd.DataFrame(rows, columns=[
        "Material", "Cost", "CO2", "Score", "CO2 Reduction", "Cost Savings"
    ])

    file_path = "export.xlsx"
    df_export.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)


# -------------------------------
# EXPORT PDF
# -------------------------------
from reportlab.platypus import SimpleDocTemplate, Table

@app.route("/export_pdf")
def export_pdf():

    cursor.execute("""
        SELECT material_name, predicted_cost, predicted_co2, suitability_score
        FROM recommendations
        ORDER BY id DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()

    pdf_path = "report.pdf"

    doc = SimpleDocTemplate(pdf_path)

    data = [["Material", "Cost", "CO2", "Score"]]
    data.extend(rows)

    table = Table(data)

    doc.build([table])

    return send_file(pdf_path, as_attachment=True)


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

    avg_co2 = sum([r["co2_reduction_percent"] for r in results]) / len(results)
    avg_cost = sum([r["cost_savings"] for r in results]) / len(results)

    labels, values = get_material_usage()

    return render_template(
        "result.html",
        results=results,
        full_data=full_data,
        avg_co2=round(avg_co2, 2),
        avg_cost=round(avg_cost, 2),
        usage_labels=labels,
        usage_values=values
    )


# -------------------------------
# RUN (Render compatible)
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


