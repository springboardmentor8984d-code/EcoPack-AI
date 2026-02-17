import pandas as pd
import sqlite3
import os

def perform_feature_engineering(db_path):
    """
    Read data from DB, perform feature engineering, and update DB.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM materials", conn)

    # 1. CO2 Impact Index (Lower is better)
    # Scaled based on emission score and offset by biodegradability
    df['CO2_Impact_Index'] = df['CO2_Emission_Score'] * (100 - df['Biodegradability_Score']) / 100

    # 2. Cost Efficiency Index (Higher is better)
    # Strength per unit cost
    df['Cost_Efficiency_Index'] = df['Strength_MPa'] / df['Cost_Per_Unit']

    # 3. Material Suitability Score (Higher is better)
    df['Material_Suitability_Score'] = (df['Biodegradability_Score'] + df['Recyclability_Percentage']) / 2

    # --- Formal Ranking Evaluation (Normalization) ---
    # We use min-max scaling to bring all values to a 0-1 range
    # For Cost and CO2: Lower is better, so 0 = Best, 1 = Worst
    cost_min, cost_max = df['Cost_Per_Unit'].min(), df['Cost_Per_Unit'].max()
    co2_min, co2_max = df['CO2_Emission_Score'].min(), df['CO2_Emission_Score'].max()
    suit_min, suit_max = df['Material_Suitability_Score'].min(), df['Material_Suitability_Score'].max()

    # Avoid division by zero
    cost_norm = (df['Cost_Per_Unit'] - cost_min) / (cost_max - cost_min) if cost_max > cost_min else 0
    co2_norm = (df['CO2_Emission_Score'] - co2_min) / (co2_max - co2_min) if co2_max > co2_min else 0
    # For Suitability: Higher is better, so we use (1 - normalized_score) to make 0 = Best
    suit_norm = 1 - ((df['Material_Suitability_Score'] - suit_min) / (suit_max - suit_min)) if suit_max > suit_min else 0

    # Calculate Final Sustainability-Optimization Score
    # Score = 0.4*Cost + 0.4*CO2 + 0.2*Suitability (Lower score = Better Material)
    df['final_score'] = (0.4 * cost_norm) + (0.4 * co2_norm) + (0.2 * suit_norm)

    # Rank the materials (Lower score leads to rank 1)
    df = df.sort_values('final_score')
    df['Material_Rank'] = range(1, len(df) + 1)

    # Save processed data
    df.to_sql('materials_processed', conn, if_exists='replace', index=False)
    
    print("Ranking evaluation completed based on formula. Processed data saved.")
    conn.close()

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_FILE = os.path.join(BASE_DIR, 'data', 'ecopack.db')
    perform_feature_engineering(DB_FILE)
