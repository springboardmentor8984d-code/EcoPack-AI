from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine, text
from functools import wraps
import plotly.express as px
import plotly.utils
import json
import io
import os
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)

# ==========================================
# 1. SECURITY & CONFIGURATION
# ==========================================
API_KEY = os.getenv("API_KEY")
# Ensure your PostgreSQL password is correct here
DB_URI = os.getenv("DATABASE_URL")
if not API_KEY or not DB_URI:
    raise ValueError("Environment variables API_KEY and DATABASE_URL must be set.")
engine = create_engine(DB_URI)

def require_api_key(f):
    """Decorator to secure API endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        provided_key = request.headers.get('x-api-key')
        if provided_key and provided_key == API_KEY:
            return f(*args, **kwargs)
        return jsonify({"status": "error", "message": "Unauthorized Access."}), 401
    return decorated

# ==========================================
# 2. LOAD MODELS ONLY (CACHE REMOVED)
# ==========================================
print("Initializing EcoPackAI Models...")
try:
    rf_cost_model = joblib.load('artifacts/cost_model.pkl')
    xgb_co2_model = joblib.load('artifacts/co2_model.pkl')
    preprocessor = joblib.load('artifacts/preprocessor.pkl')
    print("ML Artifacts Loaded successfully. API is ready!")
except Exception as e:
    print(f"Initialization Error: {e}")

# ==========================================
# 3. PREDICTION & UI ROUTES
# ==========================================
@app.route('/')
def home():
    """Serves the main Prediction UI by fetching dropdowns directly from DB."""
    try:
        with engine.connect() as conn:
            prods_df = pd.read_sql(text("SELECT DISTINCT product_name FROM products"), conn)
            ships_df = pd.read_sql(text("SELECT DISTINCT shipping_type FROM shipping"), conn)
            
        PRODUCT_LIST = sorted(prods_df['product_name'].tolist())
        SHIPPING_LIST = sorted(ships_df['shipping_type'].tolist())
    except Exception as e:
        print(f"Database connection error on home route: {e}")
        PRODUCT_LIST, SHIPPING_LIST = [], []

    return render_template('index.html', product_list=PRODUCT_LIST, shipping_list=SHIPPING_LIST)

@app.route('/api/v1/recommend', methods=['POST'])
@require_api_key
def recommend_packaging():
    """Handles the ML prediction and logs it for the Dashboard."""
    try:
        user_data = request.get_json()
        target_product = user_data.get('product_name')
        target_shipping = user_data.get('shipping_type')
        priority = user_data.get('sustainability_priority', 'medium') 

        if not target_product or not target_shipping:
            return jsonify({"status": "error", "message": "Missing required parameters."}), 400

        with engine.connect() as conn:
            product_info = pd.read_sql(text("SELECT * FROM products WHERE product_name = :p"), conn, params={"p": target_product})
            shipping_info = pd.read_sql(text("SELECT * FROM shipping WHERE shipping_type = :s"), conn, params={"s": target_shipping})
            valid_mats = pd.read_sql(text("SELECT * FROM materials"), conn)

        product_info.columns = product_info.columns.str.lower().str.strip()
        shipping_info.columns = shipping_info.columns.str.lower().str.strip()
        valid_mats.columns = valid_mats.columns.str.lower().str.strip()

        product_info = product_info.iloc[0]
        shipping_info = shipping_info.iloc[0]

        if product_info['fragility_level'] > 5:
            valid_mats = valid_mats[valid_mats['strength'] >= 6]

        valid_mats['avg_weight'] = product_info['avg_weight']
        valid_mats['fragility_level'] = product_info['fragility_level']
        valid_mats['industry_type'] = product_info['industry_type']
        valid_mats['distance_km'] = shipping_info['distance_km']
        valid_mats['handling_risk'] = shipping_info['handling_risk']
        valid_mats['shipping_type'] = target_shipping

        feature_names = ['strength', 'cost_per_unit', 'co2_emission_score', 'avg_weight', 
                         'fragility_level', 'distance_km', 'handling_risk', 'shipping_type', 'industry_type']
        
        processed_features = preprocessor.transform(valid_mats[feature_names])
        valid_mats['pred_cost'] = rf_cost_model.predict(processed_features).round(2)
        valid_mats['pred_co2'] = xgb_co2_model.predict(processed_features).round(2)

        def norm(col, invert=False):
            res = (col - col.min()) / (col.max() - col.min() + 1e-9)
            return 1 - res if invert else res
        
        c_norm = norm(valid_mats['pred_cost'])
        e_norm = norm(valid_mats['pred_co2'])
        s_norm = norm((valid_mats['strength'] * 0.6) + (valid_mats['weight_capacity'] * 0.4), invert=True)

        w_eco, w_cost = (0.6, 0.2) if priority == "high" else (0.4, 0.4)
        valid_mats['final_score'] = ((c_norm * w_cost) + (e_norm * w_eco) + (s_norm * 0.2)).round(4)
        top_5 = valid_mats.sort_values(by='final_score', ascending=True).head(5).reset_index(drop=True)

        # ---------------------------------------------------------
        # THE REAL-TIME BRIDGE: Log the #1 AI choice to the dashboard!
        try:
            # We will log the Top 3 materials to simulate split enterprise orders
            # #1 gets high volume, #2 gets medium volume, #3 gets low volume
            volumes = [np.random.randint(150, 200), np.random.randint(50, 100), np.random.randint(10, 40)]
            records = []
            
            for idx in range(3):
                mat = top_5.iloc[idx]
                cost_savings = float(mat['pred_cost']) * 0.25 
                co2_saved = float(mat['pred_co2']) * 1.5      
                
                records.append({
                    'date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'material_used': mat['material_type'],
                    'cost_savings_inr': round(cost_savings, 2),
                    'co2_reduction_kg': round(co2_saved, 2),
                    'shipment_volume': volumes[idx]
                })
            
            new_record = pd.DataFrame(records)
            log_file = 'live_dashboard_data.csv'
            
            if not os.path.exists(log_file):
                new_record.to_csv(log_file, index=False)
            else:
                new_record.to_csv(log_file, mode='a', header=False, index=False)
        except Exception as log_e:
            print(f"Live Log Error: {log_e}")
        # ---------------------------------------------------------
        # ---------------------------------------------------------

        recommendations = []
        for i, row in top_5.iterrows():
            recommendations.append({
                "rank": i + 1,
                "material": row['material_type'],
                "cost": float(row['pred_cost']),
                "co2": float(row['pred_co2']),
                "match": max(10, 100 - (float(row['final_score']) * 100))
            })

        return jsonify({"status": "success", "data": recommendations}), 200

    except Exception as e:
        print(f"Backend Error: {e}")
        return jsonify({"status": "error", "message": "Database or Prediction Error. Check terminal."}), 500


# ==========================================
# 4. LIVE DASHBOARD ROUTE (MODULE 7)
# ==========================================
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/v1/analytics', methods=['GET'])
def get_analytics():
    """Reads live history from your predictions and builds the charts."""
    log_file = 'live_dashboard_data.csv'
    
    if os.path.exists(log_file):
        df = pd.read_csv(log_file)
        df['date'] = pd.to_datetime(df['date'])
    else:
        # Fallback if no predictions have been made yet
        df = pd.DataFrame({
            'date': [pd.Timestamp.now()],
            'material_used': ['Awaiting Live Data'],
            'cost_savings_inr': [0.0],
            'co2_reduction_kg': [0.0],
            'shipment_volume': [1]
        })
    
    total_savings = df['cost_savings_inr'].sum().round(2)
    total_co2_saved = df['co2_reduction_kg'].sum().round(2)
    
    # Material Distribution (Donut) based on YOUR live choices
    mat_usage = df.groupby('material_used')['shipment_volume'].sum().reset_index()
    mat_usage = df.groupby('material_used')['shipment_volume'].sum().reset_index()
    fig1 = px.pie(mat_usage, values='shipment_volume', names='material_used', hole=0.6,
                  color_discrete_sequence=['#1e5631', '#4c9a2a', '#81c784', '#aed581', '#c5e1a5'])
    
    # --- THE OVERLAP FIX ---
    # 1. Show ONLY the clean percentage inside the slices
    fig1.update_traces(
        textposition='inside', 
        textinfo='percent', 
        insidetextfont=dict(color='white', size=14)
    )
    
    # 2. Give the chart margins and move the text legend neatly to the bottom
    fig1.update_layout(
        margin=dict(t=20, b=40, l=10, r=10), 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            orientation="h", 
            yanchor="top", 
            y=-0.1, 
            xanchor="center", 
            x=0.5,
            font=dict(size=11)
        )
    )
    
    # Trends Over Time based on YOUR prediction timestamps
    fig2 = px.line(df, x='date', y='co2_reduction_kg', markers=True)
    fig2.update_traces(line_color='#4c9a2a', line_width=3, marker=dict(size=8))
    fig2.update_layout(margin=dict(t=10, b=20, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="CO₂ Saved (kg)")

    return jsonify({
        "kpis": {"savings": total_savings, "co2": total_co2_saved, "reduction_pct": 28.4},
        "charts": {
            "mat": json.loads(json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)),
            "trend": json.loads(json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder))
        }
    })

@app.route('/api/v1/export/excel', methods=['GET'])
def export_excel():
    log_file = 'live_dashboard_data.csv'
    if not os.path.exists(log_file):
        return "No data to export yet. Run a prediction first!", 400
        
    df = pd.read_csv(log_file)
    # Try available Excel writer engines to be robust if a library is missing
    engines = ['xlsxwriter', 'openpyxl']
    last_exc = None
    for eng in engines:
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine=eng) as writer:
                df.to_excel(writer, sheet_name='Live Report', index=False)
            break
        except Exception as e:
            last_exc = e
            continue

    if last_exc is not None and 'output' not in locals():
        print(f"Excel export failed (no engine available): {last_exc}")
        return jsonify({"status": "error", "message": "Excel export failed. Install xlsxwriter or openpyxl."}), 500

    output.seek(0)
    mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    # Support both Flask >=2.0 (`download_name`) and older (`attachment_filename`)
    try:
        return send_file(output, download_name="Live_EcoPackAI_Report.xlsx", as_attachment=True, mimetype=mimetype)
    except TypeError:
        return send_file(output, attachment_filename="Live_EcoPackAI_Report.xlsx", as_attachment=True, mimetype=mimetype)


if __name__ == '__main__':
    app.run(debug=True, port=5000)