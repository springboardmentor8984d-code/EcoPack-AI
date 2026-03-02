# EcoPackAI – AI-Powered Sustainable Packaging Recommendation System

EcoPackAI is an AI-powered full-stack web platform designed to recommend optimal packaging materials based on product attributes, sustainability parameters, and industry standards.

## Features
- **Material Recommendation**: Get ranked eco-friendly materials based on strength and weight requirements.
- **Sustainability Analytics**: Visualize CO2 impact and cost efficiency.
- **ML-Powered Predictions**: Uses Random Forest and XGBoost to predict costs and environmental footprints.
- **Modern UI**: Glassmorphism design for a premium user experience.

## Project Structure
- `data/`: Contains raw CSV data.
- `src/`: Core logic including data management, feature engineering, and Flask API.
- `models/`: Trained ML models (joblib format).
- `templates/`: HTML templates for the frontend.
- `static/`: Static assets (CSS, JS).

## How to Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up PostgreSQL:
   - Ensure you have a running PostgreSQL instance.
   - Create a database (default: `ecopack_db`).
   - Configure connection via environment variables if needed (defaults: `DB_USER=postgres`, `DB_PASSWORD=password`, `DB_HOST=localhost`, `DB_PORT=5432`).
3. Initialize data and train models:
   ```bash
   python src/data_management.py
   python src/feature_engineering.py
   python src/model_training.py
   ```
4. Run the Flask application:
   ```bash
   python src/app.py
   ```
5. Access the app at `http://127.0.0.1:5000`

## Tech Stack
- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Machine Learning**: Scikit-learn, XGBoost
- **Frontend**: HTML5, Bootstrap 5, Chart.js, Glassmorphism CSS
- **Analytics**: Plotly/Chart.js
## Overview
EcoPackAI is a Machine Learning–driven decision support system that recommends sustainable packaging materials based on product characteristics and sustainability priorities.

The system predicts:
- Packaging Cost
- CO₂ Emission Impact

It ranks materials using a dynamic weighted scoring framework and visualizes results through an interactive dashboard.

---

## Key Features
- Machine Learning–based cost and CO₂ prediction
- Dynamic weighted ranking logic
- Top 5 recommendation system
- Interactive BI dashboard (Plotly charts)
- PostgreSQL cloud database logging
- Excel export (Full ranking report)
- PDF export (Top 5 summary report)
- Production-ready deployment (Render + Gunicorn)

---

## Technologies Used

### Backend
- Python
- Flask
- Gunicorn (Production WSGI Server)

### Machine Learning
- Random Forest Regressor
- XGBoost Regressor
- Scikit-learn

### Frontend
- HTML
- Bootstrap
- JavaScript

### Visualization
- Plotly

### Database
- PostgreSQL (Render Cloud)
- Environment-based secure configuration

### Export
- Pandas (Excel)
- ReportLab (PDF)

---

## System Workflow
1. User selects product filters (category, fragility, shipping type, sustainability priority).
2. Backend generates feature vector.
3. ML models predict cost and CO₂ impact.
4. Weighted ranking formula calculates final score.
5. Top 5 materials are displayed.
6. Usage data is logged into PostgreSQL database.
7. Reports can be exported in Excel or PDF format.

---

## Ranking Logic

Final Score is calculated using:

Final Score =  
(Weight₁ × Predicted Cost) +  
(Weight₂ × Predicted CO₂) +  
(Weight₃ × Suitability Score)

Weights dynamically adjust based on:
- Shipping type (Domestic / International)
- Sustainability priority (Low / Medium / High)

Lower final score → Higher rank.

---

## Live Deployment

Backend deployed on Render:

https://ecopackai-backend-6rv7.onrender.com

---

## Installation & Local Setup

1. Clone the repository

2. Install dependencies:
   pip install -r requirements.txt

3. Set environment variable:
   DATABASE_URL=your_postgresql_connection_string


4. Run locally:
   python app.py


---

## Production Setup

The application runs in production using:
gunicorn app:app


Debug mode is disabled in production.

---

## Current Status
- ML model training completed
- Flask backend fully implemented
- Dashboard integration completed
- PostgreSQL cloud integration completed
- Production deployment completed
- Export functionality verified
- System production-ready

---

## Future Enhancements
- Real-time carbon emission API integration
- Multi-dataset support
- Advanced authentication & user roles
- Enterprise-scale scalability improvements

---

## Author
Nilesh Gawhale  
Infosys Springboard Internship – Batch 11
