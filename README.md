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
