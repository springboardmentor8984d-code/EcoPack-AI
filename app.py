from flask import Flask, request, jsonify, render_template
import pandas as pd
import joblib

# Create Flask app
app = Flask(__name__)

# Load trained models
rf_cost = joblib.load("rf_model.pkl")
xgb_co2 = joblib.load("xgb_model.pkl")
scaler = joblib.load("scaler.pkl")

# Load dataset
df = pd.read_csv("EchoPack_converted.csv")

# Convert all column names to lowercase (SAFETY STEP)
df.columns = df.columns.str.lower()

# Create strength score
df["strength_score"] = df["strength"].map({
    "low": 1,
    "medium": 2,
    "high": 3
})

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/recommend", methods=["POST"])
def recommend():

    user_input = request.json
    filtered_df = df.copy()

    # Filtering logic
    if user_input["fragility"].lower() == "high":
        filtered_df = filtered_df[
            filtered_df["strength_score"] >= 3
        ]

    if user_input["product_category"].lower() == "food":
        filtered_df = filtered_df[
            filtered_df["biodegradability_score"] >= 7
        ]

    # Weight logic
    eco_weight = 0.4
    cost_weight = 0.3
    strength_weight = 0.3

    if user_input["sustainability_priority"].lower() == "high":
        eco_weight = 0.6
        cost_weight = 0.2
        strength_weight = 0.2

    # Prepare features
    X_input = scaler.transform(filtered_df[[
        "strength_score",
        "weight_capacity_kg",
        "recyclability_percent",
        "biodegradability_score"
    ]])

    # Predictions
    filtered_df["predicted_cost"] = rf_cost.predict(X_input)
    filtered_df["predicted_co2"] = xgb_co2.predict(X_input)

    # Eco score
    filtered_df["eco_score"] = (
        filtered_df["biodegradability_score"]
        + (filtered_df["recyclability_percent"] / 10)
        - filtered_df["predicted_co2"]
    )

    # Final ranking score
    filtered_df["final_score"] = (
        eco_weight * filtered_df["eco_score"]
        + cost_weight * (1 / filtered_df["predicted_cost"])
        + strength_weight * filtered_df["strength_score"]
    )

    # Sort top 5
    final = filtered_df.sort_values(
        "final_score", ascending=False
    ).head(5)

    # Baseline calculations
    baseline_co2 = filtered_df["predicted_co2"].mean()
    baseline_cost = filtered_df["predicted_cost"].mean()

    final["co2_reduction_percent"] = (
        (baseline_co2 - final["predicted_co2"]) / baseline_co2
    ) * 100

    final["cost_savings"] = (
        baseline_cost - final["predicted_cost"]
    )

    return jsonify({
        "recommended_materials": [
            {
                "material": row["material_type"],
                "cost": float(row["predicted_cost"]),
                "co2": float(row["predicted_co2"]),
                "score": float(row["final_score"]),
                "co2_reduction": float(row["co2_reduction_percent"]),
                "cost_savings": float(row["cost_savings"])
            }
            for _, row in final.iterrows()
        ]
    })

if __name__ == "__main__":
    app.run(debug=True)
