import sqlite3
import pandas as pd
import os

def initialize_database(csv_path, db_path):
    """
    Load CSV data into a SQLite database.
    """
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    df = pd.read_csv(csv_path)
    df.to_sql('raw_materials', conn, if_exists='replace', index=False)
    conn.close()
    print(f"Successfully loaded {len(df)} rows into {db_path}")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CSV_FILE = os.path.join(BASE_DIR, 'data', 'raw_materials.csv')
    DB_FILE = os.path.join(BASE_DIR, 'data', 'ecopack.db')
    initialize_database(CSV_FILE, DB_FILE)
