# 🌱 EcoPackAI -- Sustainable Material Recommendation & Cost Prediction System

EcoPackAI is a Machine Learning--powered web application that recommends
eco-friendly packaging materials based on cost, CO₂ score, and
suitability. It also predicts material cost using a trained Random
Forest model.

------------------------------------------------------------------------

## 🚀 Features

### ✅ 1. Material Recommendation System

-   Ranks materials based on:
    -   Cost
    -   CO₂ Score
    -   Suitability
-   Weighted scoring logic
-   Returns Top-N best materials

### ✅ 2. Cost Prediction Model

-   Trained using Random Forest Regressor
-   Predicts cost using:
    -   CO₂ Score
    -   Suitability
    -   Material features
-   Optimized using R², RMSE, and MAE metrics

### ✅ 3. REST API

-   JSON-based API endpoints
-   CORS enabled
-   Database integrated

### ✅ 4. PostgreSQL Integration

-   Stores materials dataset
-   Connected via SQLAlchemy

------------------------------------------------------------------------

## 🏗 Tech Stack

  Layer        Technology
  ------------ ------------------------------
  Backend      Flask
  ML Model     Scikit-learn (Random Forest)
  Database     PostgreSQL
  ORM          SQLAlchemy
  Frontend     HTML, CSS
  Deployment   Localhost (Flask Dev Server)

------------------------------------------------------------------------

## 📂 Project Structure

    EcoPackAI/
    │
    ├── app.py                 # Main Flask API
    ├── model.pkl              # Trained ML model
    ├── scaler.pkl             # Feature scaler
    ├── templates/
    │   └── index.html         # Frontend UI
    ├── static/                # CSS & JS
    ├── materials.csv          # Dataset
    ├── .env                   # Environment variables
    └── README.md

------------------------------------------------------------------------

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

``` bash
git clone https://github.com/your-username/EcoPackAI.git
cd EcoPackAI
```

### 2️⃣ Create Virtual Environment

``` bash
python -m venv venv
venv\Scripts\activate   # Windows
```

### 3️⃣ Install Dependencies

``` bash
pip install -r requirements.txt
```

### 4️⃣ Setup PostgreSQL

-   Create database: `EcoPackAI`
-   Import materials table
-   Update `.env` file:

```{=html}
<!-- -->
```
    DATABASE_URL=postgresql://username:password@localhost:5432/EcoPackAI

### 5️⃣ Run the Application

``` bash
python app.py
```

Server will run on:

    http://127.0.0.1:5000

------------------------------------------------------------------------

## 🔌 API Endpoints

### 🔹 Health Check

    GET /

### 🔹 Get Recommendations

    POST /recommend

### 🔹 Predict Cost

    POST /predict

------------------------------------------------------------------------

## 🧠 Machine Learning Details

-   Model: Random Forest Regressor
-   Target Variable: Cost
-   Features:
    -   CO₂ Score
    -   Suitability
    -   Material characteristics
-   Evaluation Metrics:
    -   R² Score
    -   RMSE
    -   MAE

------------------------------------------------------------------------

## 📊 Recommendation Logic

1.  Normalize features\
2.  Apply weighted scoring\
3.  Rank materials\
4.  Return Top-N results

------------------------------------------------------------------------

## 📌 License

This project is for academic and learning purposes.
