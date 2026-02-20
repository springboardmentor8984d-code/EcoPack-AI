import sqlite3
import pandas as pd
import numpy as np
import os

def perform_feature_engineering(db_path):
    """
    Read data from the DB, perform feature engineering, and update the DB.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM raw_materials", conn)

    # 1. CO2 Impact Index (Lower is better)
    df['CO2_Impact_Index'] = df['CO2_Emission_Score'] * (100 - df['Biodegradability_Score']) / 100

    # 2. Cost Efficiency Index (Higher is better)
    df['Cost_Efficiency_Index'] = df['Strength_MPa'] / df['Cost_Per_Unit']

    # 3. Material Suitability Score (Higher is better)
    df['Material_Suitability_Score'] = (df['Biodegradability_Score'] + df['Recyclability_Percentage']) / 2

    # Normalization
    cost_min, cost_max = df['Cost_Per_Unit'].min(), df['Cost_Per_Unit'].max()
    co2_min, co2_max = df['CO2_Emission_Score'].min(), df['CO2_Emission_Score'].max()
    suit_min, suit_max = df['Material_Suitability_Score'].min(), df['Material_Suitability_Score'].max()

    cost_norm = (df['Cost_Per_Unit'] - cost_min) / (cost_max - cost_min) if cost_max > cost_min else 0
    co2_norm = (df['CO2_Emission_Score'] - co2_min) / (co2_max - co2_min) if co2_max > co2_min else 0
    suit_norm = 1 - ((df['Material_Suitability_Score'] - suit_min) / (suit_max - suit_min)) if suit_max > suit_min else 0

    df['final_score'] = (0.4 * cost_norm) + (0.4 * co2_norm) + (0.2 * suit_norm)
    df = df.sort_values('final_score')
    df['Material_Rank'] = range(1, len(df) + 1)

    df.to_sql('materials_processed', conn, if_exists='replace', index=False)
    print("Ranking evaluation completed. Processed data saved.")
    conn.close()

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_FILE = os.path.join(BASE_DIR, 'data', 'ecopack.db')
    perform_feature_engineering(DB_FILE)
