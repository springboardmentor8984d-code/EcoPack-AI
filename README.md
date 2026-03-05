# 🌱 EcoPack-AI

AI-Based Sustainable Packaging Recommendation System built with Flask, Machine Learning, and PostgreSQL.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-API-000000?logo=flask&logoColor=white)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-ML-F7931E?logo=scikitlearn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-Regression-EC1C24)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791?logo=postgresql&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7)
![License](https://img.shields.io/badge/License-MIT-green.svg)

![Dashboard Overview](images/dashboard-main.png)

## 🚀 Project Overview

EcoPack-AI recommends the most suitable packaging material based on:

- Product category
- Fragility level
- Shipping type
- Sustainability priority

The system predicts and ranks materials using:

- Packaging cost
- CO₂ impact
- Material suitability score

Recommendations are stored in the database and visualized in a BI-style dashboard with analytics and export options.

## 🧠 Core Features

- Intelligent recommendation engine with category + fragility filtering
- Dynamic weighted scoring logic based on sustainability priority and shipping type
- Interactive dashboard analytics (distribution, ranking, trends)
- Recommendation history tracking with clear-history endpoint
- Export support (PDF / Excel on frontend)
- Environment-based DB configuration (PostgreSQL + SQLite fallback)

## 🏛 Architecture

The platform follows a layered architecture from UI → Flask API → ML models → PostgreSQL → BI dashboard.

![System Architecture](images/architecture_new.png)

## 🏗 Tech Stack

- **Backend:** Python, Flask, Flask-CORS
- **Data/ML:** Pandas, NumPy, Scikit-learn, XGBoost, Joblib
- **Database:** PostgreSQL (production), SQLite (local fallback), SQLAlchemy
- **Frontend:** HTML, CSS, JavaScript, Chart.js, Plotly
- **Deployment:** Gunicorn, Render

## 📁 Project Structure

```text
EcoPackAI/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── rf_cost_model.pkl
│   ├── xgb_co2_model.pkl
│   └── scaler.pkl
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── config.js
├── images/
│   ├── architecture_new.png
│   ├── dashboard-main.png
│   ├── material-distribution.png
│   ├── recommendation-trends.png
│   ├── model-metrics-cost.png
│   ├── model-metrics-co2.png
│   └── best-material-output.png
├── model_training.ipynb
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── Procfile
├── runtime.txt
└── README.md
```

## 🔌 API Endpoints

- `GET /` → Health check
- `POST /recommend` → Generate top material recommendations
- `GET /history` → Retrieve recommendation history
- `POST /history/clear` → Clear stored history
- `GET /analytics` → Dashboard analytics aggregates

## ⚙️ Environment Variables

Create a `.env` file using `.env.example`:

```env
API_KEY=change_me
DATABASE_URL=postgresql://username:password@localhost:5432/ecopackai
```

> Note: Current code requires `DATABASE_URL` for PostgreSQL; if not provided, it automatically uses local SQLite (`ecopackai.db`) for development.

## 💻 Run Locally

1. Open terminal in project root:

	```bash
	cd backend
	```

2. Create and activate virtual environment (Windows):

	```bash
	python -m venv venv
	venv\Scripts\activate
	```

3. Install dependencies:

	```bash
	pip install -r requirements.txt
	```

4. Start backend:

	```bash
	python app.py
	```

5. Open frontend file `frontend/index.html` in browser (or host via a simple static server).

## ☁️ Deployment (Render)

- **Build Command**

  ```bash
  pip install -r backend/requirements.txt
  ```

- **Start Command**

  ```bash
  gunicorn backend.app:app
  ```

- **Required Environment Variables**
  - `DATABASE_URL`
  - `API_KEY` (reserved for secured endpoint enhancements)

## 📊 Evaluation Summary

Models are evaluated using:

- MAE
- RMSE
- R² Score

Two model roles:

- Random Forest → packaging cost prediction
- XGBoost → CO₂ prediction used in ranking

### Model Results Snapshot

**Random Forest (Cost Prediction):**

![Random Forest Metrics](images/model-metrics-cost.png)

**XGBoost (CO₂ Prediction):**

![XGBoost Metrics](images/model-metrics-co2.png)

## 🖥 Dashboard Screenshots

### Main BI Dashboard

<img src="images/dashboard-main.png" alt="Main Dashboard" width="100%" />

### Material Distribution & Comparison

<img src="images/material-distribution.png" alt="Material Distribution" width="100%" />

### Sustainability Ranking & Recommendation Trends

<img src="images/recommendation-trends.png" alt="Recommendation Trends" width="100%" />

### Best Material Output (Notebook Validation)

<img src="images/best-material-output.png" alt="Best Material Output" width="70%" />

## 🧩 Screenshot File Checklist

Place these exact files inside the `images/` folder (same spelling and case):

- `architecture_new.png`
- `dashboard-main.png`
- `material-distribution.png`
- `recommendation-trends.png`
- `model-metrics-cost.png`
- `model-metrics-co2.png`
- `best-material-output.png`

## 👨‍💻 Author

**Rajan Kumar**

- GitHub: https://github.com/RajanKumar44

---

If you like this project, give it a ⭐ on GitHub.

