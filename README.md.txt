# 🌱 EcoPackAI  
### Intelligent Sustainable Packaging Recommendation System  
**Infosys Springboard Internship – Artificial Intelligence Domain**

---

## 📌 Project Overview

EcoPackAI is an AI-driven decision support system designed to recommend eco-friendly packaging materials by analyzing sustainability metrics, durability requirements, and cost efficiency.

The system leverages Machine Learning models to:

- 📦 Predict Packaging Cost  
- 🌍 Predict CO₂ Emissions  
- 📊 Rank Materials Based on Sustainability and Suitability  
- 📈 Provide Real-Time Dashboard Insights  

This project demonstrates the integration of predictive analytics, environmental sustainability, and interactive visualization into a deployable AI solution.

---

## 🎯 Problem Statement

Traditional packaging material selection often ignores:

- Environmental impact  
- Carbon footprint  
- Cost optimization  
- Dynamic product requirements  

EcoPackAI addresses this by building an intelligent recommendation engine that balances:

- Sustainability
- Cost Efficiency
- Material Strength
- Shipping Requirements

---

## 🏗️ System Architecture

User Input (Frontend Dashboard)
↓
Flask API (Backend)
↓
ML Models (Random Forest + XGBoost)
↓
Scoring & Ranking Engine
↓
Dashboard Output (CO₂ Reduction + Cost Savings + Ranked Materials)
📊 Dataset Description

The dataset includes packaging materials with sustainability and operational attributes.

### Features Used

| Feature | Description |
|----------|-------------|
| material_type | Name of packaging material |
| strength | Durability level (Low / Medium / High) |
| weight_capacity_kg | Maximum supported load |
| cost_per_unit | Manufacturing cost |
| biodegradability_score | Environmental decomposition rating |
| co2_emission_score | Carbon emission indicator |
| recyclability_percent | Recycling efficiency |

---

## 🔧 Feature Engineering

- Converted categorical strength values to numerical scale:
  - Low → 1  
  - Medium → 2  
  - High → 3  

- Standardized numerical features using `StandardScaler`.

---

## 🤖 Machine Learning Models

### 1️⃣ Random Forest Regressor
Used for:
Cost Prediction

yaml
Copy code

Why selected:
- Handles non-linear relationships
- Robust to overfitting
- Strong performance on structured data

---

### 2️⃣ XGBoost Regressor
Used for:
CO₂ Emission Prediction

yaml
Copy code

Why selected:
- High predictive accuracy
- Gradient boosting optimization
- Efficient handling of feature interactions

---

## 📈 Model Evaluation Metrics

Models were evaluated using:

- **MAE (Mean Absolute Error)**
- **RMSE (Root Mean Squared Error)**
- **R² Score**

These metrics ensure prediction reliability and performance consistency.

---

## 🧮 Ranking & Recommendation Logic

### Step 1 – User-Based Filtering

Materials are filtered based on:

- Product Category
- Fragility Level
- Shipping Type
- Sustainability Priority

---

### Step 2 – Eco Score Calculation

eco_score = biodegradability_score
+ (recyclability_percent / 10)
- predicted_co2

yaml
Copy code

---

### Step 3 – Final Suitability Score

final_score =
eco_weight * eco_score

cost_weight * (1 / predicted_cost)

strength_weight * strength_score

yaml
Copy code

Weights dynamically adjust based on user input priorities.

---

## 📊 Dashboard Features

The web interface provides:

- 📉 CO₂ Reduction Percentage
- 💰 Cost Savings Indicator
- 🏆 Top 5 Ranked Materials
- 📋 Dynamic Input Form
- 🔄 Real-Time API Response

---

## 🚀 Deployment

The application is deployed using:

- Flask Backend
- Gunicorn WSGI Server
- Render Cloud Hosting
- GitHub Version Control

---

## 📦 Required Dependencies

flask
pandas
numpy
scikit-learn
xgboost
gunicorn
joblib
