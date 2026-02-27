# 🌱 EcoPackAI: Intelligent Predictive Systems for Sustainable Logistics

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-black?style=for-the-badge&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-Machine%20Learning-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-Regression-red?style=for-the-badge)

**EcoPackAI** is an end-to-end Machine Learning control center designed to autonomously optimize enterprise packaging decisions. By analyzing product fragility, dimensional weights, and complex logistics routes, the system utilizes advanced dual-regression models to predict the exact financial cost and CO₂ footprint of over 50 different packaging materials in real-time.

---

## 📖 1. Project Overview & Problem Statement

The modern supply chain operates under a critical dual mandate: reducing extreme logistical costs and aggressively minimizing single-use plastic waste. Traditional packaging selection relies heavily on static, rule-based heuristics (*"use bubble wrap for fragile items"*), leading to systemic **over-packaging** (inflating costs and CO₂) or **under-packaging** (risking product damage). 

**EcoPackAI solves this by replacing human intuition with data-driven inference.** It predicts, scores, and ranks packaging materials dynamically, streaming this telemetry to an asynchronous Business Intelligence (BI) dashboard for enterprise stakeholders.

---

## ✨ 2. Core Features

* **🧠 Dual-Model Inference Engine:** Utilizes a **Random Forest Regressor** for economic predictions (Cost) and an **XGBoost Regressor** for environmental predictions (CO₂).
* **⚙️ Implicit Feature Learning:** The models natively learned the complex physics of logistics. By training on a deterministic dataset, the AI automatically applies severe predictive penalties for structurally deficient packaging without requiring slow, hardcoded backend rules.
* **⚖️ Dynamic AI Ranking Algorithm:** Applies Min-Max normalization and user-defined sustainability priorities (e.g., "High Sustainability" vs. "Cost Savings") to calculate a final **AI Match %**.
* **📊 Real-Time BI Dashboard:** A Plotly-powered interface utilizing JavaScript polling (`setInterval`) to render live Material Adoption and Emission Trend charts without page refreshes.
* **🗄️ Dynamic Database Integration:** Connected to PostgreSQL via SQLAlchemy, ensuring the frontend Predictor UI always pulls the latest live catalog of products and shipping routes.

---
## Cost Model File (Large File)

The trained cost model file is not included in this repository due to GitHub file size limitations (70MB).

Download the model from the link below:

Google Drive Link:
<https://drive.google.com/file/d/1BpsIeLJS957YpMM4TaA17_-oawO0put9/view?usp=sharing>

After downloading, place the file inside the following folder:
**/artifacts**

Make sure the file name is:
cost_model.pkl
---
## 📸 3. Application Screenshots

### The Predictor Interface
> *The AI control center where users input logistics parameters and receive real-time material rankings.*
![Predictor UI](Images/predictor_ui.png)

### Real-Time BI Dashboard
> *Live telemetry updating every 3 seconds, showing total CO₂ saved, cost reductions, and dynamic material adoption charts.*
![Live Dashboard](Images/live_dashboard.png)
---
## 🏗️ System Architecture

The application is decoupled into an API-driven architecture, ensuring the machine learning inference operates seamlessly with real-time UI updates.

```mermaid
graph TD
    A[Frontend: Predictor UI] -->|POST /api/v1/recommend| B(Flask Backend API)
    C[(PostgreSQL DB)] <-->|SQLAlchemy Fetch| B
    B -->|User Input| D[preprocessor.pkl]
    D --> E((Random Forest))
    D --> F((XGBoost))
    E -->|Target Cost| G{Ranking Algorithm}
    F -->|Target CO2| G
    G -->|Top 3 Telemetry| H[(live_dashboard_data.csv)]
    G -->|JSON Response| A
    H <-->|JS Polling GET /api/v1/analytics| I[Frontend: Live BI Dashboard]
```
---
## 🏷️ **Machine Learning Pipeline**

The models were trained on a deterministic, physics-based synthetic dataset of 22,500 logistics permutations. The pipeline automatically standardizes numerical features and one-hot encodes categorical routes.

🔩 **flowchart**
    Data[(Raw Input)] --> Preprocess[ColumnTransformer<br>StandardScaler + OneHotEncoder]
    Preprocess --> RF[Random Forest<br>Estimator]
    Preprocess --> XGB[XGBoost<br>Estimator]
    RF --> Out1[Predicted Cost INR]
    XGB --> Out2[Predicted CO2 kg]

---
## 📝 **Model Performance**
The algorithms successfully reverse-engineered the complex logistical formulas utilized during the data generation phase, they achieved perfect predictive accuracy:

| Target Model | Target Variable | R² Score |
| :--- | :--- | :--- |
| **Random Forest** | target_cost (INR) | 1.0000 |
| **XGBoost** | target_co2 (kg) | 1.0000 |

---
### 📁 **Project Structure**
```
EcoPackAI/
├── artifacts/
│   ├── cost_model.pkl        # Trained Random Forest Model
│   ├── co2_model.pkl         # Trained XGBoost Model
|   ├── evaluation_metrics    # Evaluation Metrics of models
│   └── preprocessor.pkl      # Scaler & Encoder Pipeline
├── static/
│   └── css/
│       └── style.css         # UI Styling
├── templates/
│   ├── index.html            # Predictor Interface
│   └── dashboard.html        # Live BI Dashboard
├── raw_data/
│   └── unified_master_dataset.csv    # 22,500 Synthetic Scenarios
│   └── eda_summary_statistics        # Statistics of the Dataset
│   └── Packaging_materials.csv       # Ecofriendly materials dataset
│   └── Product_data.csv              # Product dataset
│   └── Shipping_data.csv             # Shipping dataset
├── app.py                    # Main Flask Application
├── EcoPackAI_Documentation   # Documentation
├── live_dashboard_data.csv   # Real-time updated prediction data
├── EcopackAI 2.ipynb         # Jupyter Notebook file
├── requirements.txt          # Python Dependencies
└── README.md                 # Project Documentation
```
---
## 🛠️ Technology Stack
| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.9, Flask | Stateless REST API handling routing and ML inference. |
| **Database** | PostgreSQL, SQLAlchemy | Relational storage for dynamic UI population. |
| **Machine Learning** | Scikit-Learn, XGBoost | Feature preprocessing, regression, and data manipulation. |
| **Frontend UI** | HTML5, Bootstrap 5, Vanilla JS | Responsive predictor interface and dashboard layout. |
| **Data Visualization** | Plotly.js | Interactive, asynchronous charting engine. |
| **Reporting/Export** | `html2pdf.js`, `xlsxwriter` | 1-click PDF reports and Excel telemetry exports. |
---
## ⚙️ **Getting Started**
### Prerequisites

Python 3.9+

PostgreSQL installed and running on port 5432.

### Bash

git clone [https://github.com/CHERRY0456/EcoPackAI.git](https://github.com/CHERRY0456/EcoPackAI.git)

cd EcoPackAI

---
## Database Configuration
Open pgAdmin or your SQL CLI.

Create a new database named ecopack_db.

Import the CSV files (product_dataset.csv, shipping_dataset.csv, packaging_materials.csv) to create the base tables.

Update the DB_URI string in app.py with your PostgreSQL password:

**DB_URI = "postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/ecopack_db"**

---
## 📃 Future Roadmap
Live Vendor APIs: Replace static baseline material pricing with real-time market API fetches from global packaging suppliers.

Computer Vision Edge Integration: Implement a Convolutional Neural Network (CNN) to auto-detect product dimensions and fragility from a physical camera feed on the warehouse floor.

Cloud Native Deployment: Containerize the application via Docker and deploy the ML inference engine to AWS SageMaker for global scalability.

---
## 🧑‍💻 Developed By: V. Jai Sri Charan
