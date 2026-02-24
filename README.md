# EcoPackAI – AI-Powered Sustainable Packaging Recommendation System

## Overview
EcoPackAI is a Machine Learning–driven decision support system that recommends sustainable packaging materials based on product characteristics and sustainability priorities.

The system predicts:
- Packaging Cost
- CO₂ Emission Impact

It then ranks materials using a weighted scoring framework and visualizes results through an interactive BI dashboard.

---

## Key Features
- Machine Learning–based cost and CO₂ prediction
- Dynamic material ranking logic
- Top 5 recommendation system
- Business Intelligence dashboard (Plotly charts)
- SQLite database logging for usage tracking
- Excel export (Full ranking)
- PDF export (Top 5 summary report)

---

## Technologies Used

### Backend
- Python
- Flask

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
- SQLite (for recommendation logging)

### Export
- Pandas (Excel)
- ReportLab (PDF)

---

## System Workflow
1. User selects product filters (category, fragility, shipping type, sustainability priority).
2. Backend generates feature vector.
3. ML models predict cost and CO₂.
4. Weighted ranking formula calculates final score.
5. Top 5 materials are displayed.
6. Usage data is logged into database.
7. Reports can be exported in Excel or PDF format.

---

## Installation & Setup

1. Clone the repository
2. Install dependencies:

   pip install -r requirements.txt

3. Run the application:

   python app.py

4. Open browser and go to:
   http://127.0.0.1:5000

---

## Current Status
- ML model training completed
- Dashboard integration completed
- SQLite database logging implemented
- Export functionality implemented
- Ready for demo presentation

---

## Future Enhancements
- PostgreSQL cloud integration
- Cloud deployment (Render/Heroku)
- Real-time carbon emission API integration
- Multi-dataset support
- Enterprise-scale scalability improvements

---

## Author
Nilesh Gawhale  
Infosys Springboard Internship – Batch 11